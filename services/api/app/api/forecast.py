from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import DemandForecast, ForecastJob, ForecastJobStatus, PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, RecommendationStatus, ReplenishmentRecommendation, Store, Supplier, SupplierProduct, UserRole
from app.security import require_roles
from app.store_access import ensure_store_access, merchant_store_id

router = APIRouter(tags=["forecast"])
merchant_admin = require_roles(UserRole.MERCHANT, UserRole.ADMIN)


class ForecastJobRequest(BaseModel):
    store_id: UUID
    as_of: date = Field(default_factory=date.today)
    horizon_days: int = Field(default=7, ge=1, le=7)


class ForecastOutput(BaseModel):
    product_id: UUID
    target_date: date
    predicted_qty: float = Field(ge=0)


class RecommendationOutput(BaseModel):
    product_id: UUID
    suggested_qty: float = Field(ge=0)
    safety_stock: float = Field(ge=0)
    reorder_point: float = Field(ge=0)
    meu_score: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=1)


class ForecastJobResult(BaseModel):
    status: ForecastJobStatus
    model_name: str | None = None
    model_version: str | None = None
    forecasts: list[ForecastOutput] = Field(default_factory=list)
    recommendations: list[RecommendationOutput] = Field(default_factory=list)
    error_message: str | None = None


class RecommendationDecision(BaseModel):
    convert_to_po: bool = False
    supplier_id: UUID | None = None


@router.post("/jobs/forecasts", status_code=status.HTTP_202_ACCEPTED)
def create_forecast_job(payload: ForecastJobRequest, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    ensure_store_access(db, user, payload.store_id)
    if db.get(Store, payload.store_id) is None:
        raise HTTPException(status_code=404, detail="Store not found")
    job = ForecastJob(store_id=payload.store_id, as_of=payload.as_of, horizon_days=payload.horizon_days, created_by=user.id, status=ForecastJobStatus.QUEUED)
    db.add(job)
    db.commit()
    db.refresh(job)
    from app.core.config import get_settings
    if get_settings().forecast_autorun:
        from app.worker import run_forecast_job
        try:
            run_forecast_job.delay(str(job.id))
        except Exception as exc:
            job.status = ForecastJobStatus.FAILED
            job.error_message = f"Could not queue forecast job: {type(exc).__name__}"
            db.commit()
            raise HTTPException(status_code=503, detail="Forecast worker unavailable") from exc
    return {"job_id": str(job.id), "status": job.status.value}


@router.get("/jobs/{job_id}")
def get_forecast_job(job_id: UUID, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> dict:
    job = db.get(ForecastJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Forecast job not found")
    ensure_store_access(db, _user, job.store_id)
    return {"job_id": str(job.id), "status": job.status.value, "as_of": job.as_of.isoformat(),
            "error_message": job.error_message}


@router.post("/jobs/{job_id}/result")
def complete_forecast_job(job_id: UUID, payload: ForecastJobResult, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> dict:
    db.rollback()
    with db.begin():
        job = db.scalar(select(ForecastJob).where(ForecastJob.id == job_id).with_for_update())
        if job is None:
            raise HTTPException(status_code=404, detail="Forecast job not found")
        if _user is not None:
            ensure_store_access(db, _user, job.store_id)
        if job.status not in {ForecastJobStatus.QUEUED, ForecastJobStatus.RUNNING}:
            raise HTTPException(status_code=409, detail="Forecast job cannot be completed")
        if payload.status == ForecastJobStatus.FAILED:
            if not payload.error_message:
                raise HTTPException(status_code=422, detail="error_message is required for failed jobs")
            job.status = ForecastJobStatus.FAILED
            job.error_message = payload.error_message
            return {"job_id": str(job.id), "status": job.status.value}
        if payload.status != ForecastJobStatus.SUCCEEDED or not payload.model_name or not payload.model_version:
            raise HTTPException(status_code=422, detail="Successful jobs require model metadata")
        product_ids = {item.product_id for item in payload.forecasts} | {item.product_id for item in payload.recommendations}
        if product_ids:
            from app.models import Product
            products = set(db.scalars(select(Product.id).where(Product.id.in_(product_ids), Product.is_active.is_(True))).all())
            if products != product_ids:
                raise HTTPException(status_code=422, detail="Unknown or inactive product in forecast result")
        horizon_end = job.as_of + timedelta(days=job.horizon_days)
        for item in payload.forecasts:
            if not job.as_of <= item.target_date <= horizon_end:
                raise HTTPException(status_code=422, detail="Forecast target_date outside job horizon")
            db.add(DemandForecast(job_id=job.id, store_id=job.store_id, product_id=item.product_id, target_date=item.target_date, predicted_qty=item.predicted_qty, model_name=payload.model_name, model_version=payload.model_version))
        for item in payload.recommendations:
            db.add(ReplenishmentRecommendation(job_id=job.id, store_id=job.store_id, product_id=item.product_id, suggested_qty=item.suggested_qty, safety_stock=item.safety_stock, reorder_point=item.reorder_point, meu_score=item.meu_score, reason=item.reason, status=RecommendationStatus.PENDING))
        job.status = ForecastJobStatus.SUCCEEDED
        job.error_message = None
        return {"job_id": str(job.id), "status": job.status.value, "forecast_count": len(payload.forecasts), "recommendation_count": len(payload.recommendations)}


@router.get("/forecasts")
def list_forecasts(store_id: UUID | None = None, product_id: UUID | None = None, from_: date | None = Query(default=None, alias="from"), to: date | None = None, model_name: str | None = None, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> list[dict]:
    stmt = select(DemandForecast).order_by(DemandForecast.target_date)
    owned = merchant_store_id(db, _user)
    if owned is not None: stmt = stmt.where(DemandForecast.store_id == owned)
    if store_id: stmt = stmt.where(DemandForecast.store_id == store_id)
    if product_id: stmt = stmt.where(DemandForecast.product_id == product_id)
    if from_: stmt = stmt.where(DemandForecast.target_date >= from_)
    if to: stmt = stmt.where(DemandForecast.target_date <= to)
    if model_name: stmt = stmt.where(DemandForecast.model_name == model_name)
    return [{"id": str(x.id), "store_id": str(x.store_id), "product_id": str(x.product_id), "target_date": x.target_date, "predicted_qty": str(x.predicted_qty), "model_name": x.model_name, "model_version": x.model_version} for x in db.scalars(stmt).all()]


@router.get("/recommendations")
def list_recommendations(status_filter: RecommendationStatus | None = Query(default=None, alias="status"), store_id: UUID | None = None, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> list[dict]:
    stmt = select(ReplenishmentRecommendation).order_by(ReplenishmentRecommendation.created_at.desc())
    owned = merchant_store_id(db, _user)
    if owned is not None: stmt = stmt.where(ReplenishmentRecommendation.store_id == owned)
    if status_filter: stmt = stmt.where(ReplenishmentRecommendation.status == status_filter)
    if store_id: stmt = stmt.where(ReplenishmentRecommendation.store_id == store_id)
    return [{"id": str(x.id), "store_id": str(x.store_id), "product_id": str(x.product_id), "suggested_qty": str(x.suggested_qty), "safety_stock": str(x.safety_stock), "reorder_point": str(x.reorder_point), "meu_score": str(x.meu_score) if x.meu_score is not None else None, "reason": x.reason, "status": x.status.value} for x in db.scalars(stmt).all()]


def _set_recommendation_status(recommendation_id: UUID, target: RecommendationStatus, db: Session, user) -> dict:
    recommendation = db.get(ReplenishmentRecommendation, recommendation_id)
    if recommendation is None: raise HTTPException(status_code=404, detail="Recommendation not found")
    ensure_store_access(db, user, recommendation.store_id)
    if recommendation.status != RecommendationStatus.PENDING: raise HTTPException(status_code=409, detail="Recommendation cannot be changed")
    recommendation.status = target
    db.commit()
    return {"id": str(recommendation.id), "status": recommendation.status.value}


@router.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation(recommendation_id: UUID, payload: RecommendationDecision | None = None, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    payload = payload or RecommendationDecision()
    recommendation = db.get(ReplenishmentRecommendation, recommendation_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    ensure_store_access(db, user, recommendation.store_id)
    if recommendation.status != RecommendationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Recommendation cannot be changed")
    if not payload.convert_to_po:
        recommendation.status = RecommendationStatus.APPROVED
        db.commit()
        return {"id": str(recommendation.id), "status": recommendation.status.value}
    if payload.supplier_id is None:
        raise HTTPException(status_code=422, detail="supplier_id is required when convert_to_po is true")
    supplier = db.get(Supplier, payload.supplier_id)
    if supplier is None or supplier.store_id != recommendation.store_id:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier_product = db.get(SupplierProduct, (payload.supplier_id, recommendation.product_id))
    if supplier_product is None:
        raise HTTPException(status_code=409, detail="Supplier does not provide recommended product")
    po = PurchaseOrder(store_id=recommendation.store_id, supplier_id=payload.supplier_id, created_by=user.id, status=PurchaseOrderStatus.PENDING_APPROVAL, notes=f"Created from recommendation {recommendation.id}")
    db.add(po)
    db.flush()
    db.add(PurchaseOrderItem(purchase_order_id=po.id, product_id=recommendation.product_id, quantity_ordered=recommendation.suggested_qty, unit_cost=supplier_product.unit_cost))
    recommendation.status = RecommendationStatus.CONVERTED
    db.commit()
    return {"id": str(recommendation.id), "status": recommendation.status.value, "purchase_order_id": str(po.id)}


@router.post("/recommendations/{recommendation_id}/reject")
def reject_recommendation(recommendation_id: UUID, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> dict:
    return _set_recommendation_status(recommendation_id, RecommendationStatus.REJECTED, db, _user)
