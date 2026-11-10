"""FastAPI cho SmartGrocery Intelligence (Phương án B — service riêng, mặc định port 8001).

Chạy:  uvicorn src.inference.api:app --host 0.0.0.0 --port 8001
Swagger: http://localhost:8001/docs

Backend (Tuấn Anh) gọi qua HTTP; Frontend KHÔNG gọi trực tiếp service này.
"""
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from src.inference.schemas import (BatchReplenishmentRequest, ErrorResponse, ReplenishmentRequest,
                                   ReplenishmentResponse)
from src.inference.service import ServiceError, get_service
from src.utils.logging_config import get_logger

log = get_logger("intelligence.api", "inference.log")
app = FastAPI(title="SmartGrocery Intelligence", version="1.0.0",
              description="Dự báo nhu cầu 7 ngày + đề xuất nhập hàng (Safety Stock, ROP, MEU)")


@app.exception_handler(ServiceError)
async def _service_error(_, exc: ServiceError):
    return JSONResponse(status_code=exc.http_status, content={"error_code": exc.code, "message": exc.message})


@app.exception_handler(Exception)
async def _unexpected(_, exc: Exception):  # không để 1 request lỗi làm dừng service
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": "Lỗi nội bộ AI service"})


@app.on_event("startup")
def _warmup():
    get_service()


@app.get("/health")
def health():
    return get_service().health()


@app.get("/model/info")
def model_info():
    return get_service().model_info()


@app.get("/forecast/{store_id}/{sku_id}", responses={404: {"model": ErrorResponse}})
def forecast(store_id: str, sku_id: str, horizon: int = Query(7, ge=1, le=7)):
    return get_service().forecast(store_id, sku_id, horizon=horizon)


@app.post("/forecast/replenishment", response_model=ReplenishmentResponse,
          responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
def replenishment(req: ReplenishmentRequest):
    res = get_service().replenishment(req)
    log.info("replenishment %s/%s status=%s qty=%s", req.store_id, req.sku_id, res["status"],
             res.get("suggested_order_qty"))
    return res


@app.post("/forecast/replenishment/batch")
def replenishment_batch(req: BatchReplenishmentRequest):
    out = []
    for item in req.items:
        try:
            out.append({"ok": True, "result": get_service().replenishment(item)})
        except ServiceError as e:
            out.append({"ok": False, "store_id": item.store_id, "sku_id": item.sku_id,
                        "error_code": e.code, "message": e.message})
    return {"count": len(out), "items": out}
