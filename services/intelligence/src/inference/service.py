"""Điều phối inference: forecast 7 ngày + Safety Stock + ROP + MEU.

Dùng được theo 2 cách (mục 11.2) — nhóm chọn 1:
  A. Python module:  from src.inference.service import get_service; get_service().replenishment(dict)
  B. HTTP service:   uvicorn src.inference.api:app --port 8001  (xem api.py)

Nguyên tắc:
  * Backend là nguồn sự thật về tồn kho; AI không ghi vào database nghiệp vụ.
  * Không bịa số: thiếu dữ liệu -> status/warning có cấu trúc.
  * Không trả NaN/Infinity; forecast luôn >= 0.
  * AI chỉ ĐỀ XUẤT; requires_approval luôn = true.
"""
from __future__ import annotations

import math
import threading
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from src.data import load_data as L
from src.features.build_features import build_origin_features
from src.models.predict import forecast_all
from src.models.train_lightgbm import BUNDLE_PATH, load_bundle
from src.optimization.meu import MEUInputMissingError, optimize_order_qty
from src.optimization.reorder_point import (HorizonInsufficientError, basic_order_qty, inventory_position,
                                            lead_time_demand, reorder_point)
from src.optimization.safety_stock import safety_stock
from src.utils import config
from src.utils.logging_config import get_logger

log = get_logger("intelligence.service", "inference.log")

HOLDING_RATE_ANNUAL = 0.25     # giả định demo: chi phí lưu kho 25%/năm giá vốn
GOODWILL_RATE = 0.10           # giả định demo: phạt mất khách = 10% giá bán / đơn vị thiếu
PERISHABLE_WASTE_SHARE = 0.5   # giả định demo: hàng tươi (shelf life <= 7 ngày) dư -> 50% hủy


class ServiceError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(message)
        self.code, self.message, self.http_status = code, message, http_status


def _f(x, nd=3):
    """float an toàn cho JSON: NaN/Inf -> None."""
    if x is None:
        return None
    x = float(x)
    return None if (math.isnan(x) or math.isinf(x)) else round(x, nd)


class IntelligenceService:
    def __init__(self, load_model: bool = True):
        self.lock = threading.Lock()
        self.products = L.load_products().set_index("sku_id")
        self.promotions = L.load_promotions()
        self.holidays = L.load_holidays()
        self.panel = pd.read_csv(config.DAILY_SALES, parse_dates=["date"], dtype={"store_id": str, "sku_id": str})
        self.as_of_default = self.panel["date"].max()
        self.origin = build_origin_features(self.panel)
        self.series = set(map(tuple, self.panel[["store_id", "sku_id"]].drop_duplicates().to_numpy()))
        self.resid = self._load_resid()
        self.bundle, self.model_error = None, None
        if load_model:
            try:
                self.bundle = load_bundle(BUNDLE_PATH)
            except Exception as e:  # noqa: BLE001
                self.model_error = f"{type(e).__name__}: {e}"
                log.error("MODEL_UNAVAILABLE - %s -> fallback seasonal naive", self.model_error)
        self._cache: dict[pd.Timestamp, pd.DataFrame] = {}
        self._load_precomputed()
        log.info("Service ready: series=%d as_of=%s model=%s", len(self.series), self.as_of_default.date(),
                 self.model_version)

    # ------------------------------------------------------------------ setup
    @property
    def model_version(self) -> str:
        return self.bundle["model_version"] if self.bundle else "seasonal-naive-fallback"

    def _load_resid(self):
        p = config.MODEL_DIR / "residual_stats.csv"
        return pd.read_csv(p, dtype={"store_id": str, "sku_id": str}) if p.exists() else None

    def _load_precomputed(self):
        p = config.FORECAST_DIR / "latest_forecast.csv"
        if not p.exists() or self.bundle is None:
            return
        df = pd.read_csv(p, parse_dates=["as_of_date", "forecast_date"], dtype={"store_id": str, "sku_id": str})
        if df.empty:
            return
        gen = pd.to_datetime(df["generated_at"].iloc[0], utc=True)
        fresh = datetime.now(timezone.utc) - gen.to_pydatetime() < timedelta(hours=config.FORECAST_STALE_HOURS)
        if fresh and df["model_version"].iloc[0] == self.model_version:
            self._cache[pd.Timestamp(df["as_of_date"].iloc[0])] = df
            log.info("Loaded precomputed forecast generated_at=%s", gen)
        else:
            log.info("Precomputed forecast stale/khác version -> sẽ tính on-the-fly")

    def _forecasts(self, as_of: pd.Timestamp) -> pd.DataFrame:
        with self.lock:
            if as_of not in self._cache:
                self._cache[as_of] = forecast_all(self.bundle, self.origin, self.panel, as_of, self.promotions,
                                                  self.holidays, self.products.reset_index(), self.resid)
            return self._cache[as_of]

    # ------------------------------------------------------------------ public
    def health(self) -> dict:
        return {"status": "ok" if self.bundle else "degraded", "model_loaded": self.bundle is not None,
                "model_version": self.model_version, "data_as_of": str(self.as_of_default.date()),
                "series": len(self.series), "model_error": self.model_error}

    def model_info(self) -> dict:
        info = {k: v for k, v in (self.bundle or {}).items() if k != "models"}
        info["n_estimators"] = {str(k): int(v) for k, v in info.get("n_estimators", {}).items()}
        return {"model_version": self.model_version, **info}

    def forecast(self, store_id: str, sku_id: str, as_of=None, horizon: int = 7) -> dict:
        store_id, sku_id = store_id.strip().upper(), sku_id.strip().upper()
        as_of = self._check(store_id, sku_id, as_of)
        fc = self._forecasts(as_of)
        s = fc[(fc.store_id == store_id) & (fc.sku_id == sku_id)].sort_values("horizon").head(horizon)
        r0 = s.iloc[0]
        return {
            "store_id": store_id, "sku_id": sku_id, "as_of_date": str(as_of.date()),
            "model_version": r0.model_version, "generated_at": r0.generated_at, "method": r0.method,
            "status": r0.status, "confidence": r0.confidence,
            "forecast": [{"date": str(pd.Timestamp(r.forecast_date).date()), "horizon": int(r.horizon),
                          "predicted_demand": _f(r.predicted_sales),
                          "baseline_seasonal_naive": _f(r.baseline_seasonal_naive)} for r in s.itertuples()],
        }

    def _check(self, store_id, sku_id, as_of):
        if (store_id, sku_id) not in self.series:
            if sku_id not in self.products.index:
                raise ServiceError("UNKNOWN_SKU", f"SKU {sku_id} không có trong product master", 404)
            raise ServiceError("UNKNOWN_SERIES", f"{store_id}/{sku_id} không có lịch sử bán hàng", 404)
        as_of = pd.Timestamp(as_of) if as_of is not None else self.as_of_default
        if as_of > self.as_of_default:
            raise ServiceError("AS_OF_OUT_OF_RANGE", f"as_of_date > dữ liệu mới nhất {self.as_of_default.date()}")
        return as_of

    def _sigma(self, store_id, sku_id, hist_mean, category):
        if self.resid is not None:
            r = self.resid[(self.resid.store_id == store_id) & (self.resid.sku_id == sku_id)]
            if len(r) and pd.notna(r.sigma_daily.iloc[0]):
                return float(r.sigma_daily.iloc[0]), str(r.sigma_source.iloc[0])
            c = self.resid[(self.resid.category == category) & (self.resid.n_resid >= 20)]
            if len(c):
                cv = float((c.sigma_daily / c.mean_actual.clip(lower=0.1)).median())
                return max(cv * max(hist_mean, 0.5), 0.5), "category_cv_fallback"
        return max(float(hist_mean), 0.5), "poisson_assumption_fallback"

    def default_costs(self, sku_id: str) -> dict:
        p = self.products.loc[sku_id]
        price, cost = float(p.unit_price), float(p.purchase_cost)
        return {
            "selling_price": price, "purchase_cost": cost,
            "holding_cost_per_unit": round(cost * HOLDING_RATE_ANNUAL / 365 * 7, 2),
            "stockout_penalty_per_unit": round(price * GOODWILL_RATE, 2),
            "waste_cost_per_unit": round(cost * PERISHABLE_WASTE_SHARE, 2) if p.shelf_life_days <= 7 else 0.0,
        }

    def replenishment(self, req) -> dict:
        from src.inference.schemas import ReplenishmentRequest
        if isinstance(req, dict):
            req = ReplenishmentRequest(**req)
        as_of = self._check(req.store_id, req.sku_id, req.as_of_date)
        prod = self.products.loc[req.sku_id]
        fc = self._forecasts(as_of)
        s = fc[(fc.store_id == req.store_id) & (fc.sku_id == req.sku_id)].sort_values("horizon")
        warnings: list[str] = []
        if self.bundle is None:
            warnings.append("MODEL_UNAVAILABLE")
        method, confidence, fstatus = s.method.iloc[0], s.confidence.iloc[0], s.status.iloc[0]
        daily = s.predicted_sales.tolist()
        hist_mean = float(np.nanmean(daily)) if not all(pd.isna(daily)) else 0.0

        L_days = int(req.lead_time_days or prod.lead_time_days)
        pack = int(req.pack_size or prod.pack_size)
        moq = int(req.moq if req.moq is not None else prod.moq)
        ip = inventory_position(req.inventory.on_hand, req.inventory.on_order, req.inventory.reserved)
        sigma, sigma_src = self._sigma(req.store_id, req.sku_id, hist_mean, prod.category)
        base = dict(
            store_id=req.store_id, sku_id=req.sku_id, product_name=str(prod.product_name),
            model_version=s.model_version.iloc[0], forecast_method=method, generated_at=s.generated_at.iloc[0],
            as_of_date=str(as_of.date()), lead_time_days=L_days, service_level=req.service_level,
            sigma_daily=_f(sigma), inventory_position=_f(ip), confidence=confidence,
            lead_time_demand=None, safety_stock=None, reorder_point=None, rop_order_qty=None,
            suggested_order_qty=None, days_of_cover=None, requires_approval=True,
            forecast=[{"date": str(pd.Timestamp(r.forecast_date).date()), "horizon": int(r.horizon),
                       "predicted_demand": _f(r.predicted_sales),
                       "baseline_seasonal_naive": _f(r.baseline_seasonal_naive)}
                      for r in s.head(req.forecast_horizon).itertuples()],
        )
        base["forecast_total"] = _f(sum(p["predicted_demand"] or 0 for p in base["forecast"]))
        no_meu = {"enabled": False}
        if sigma_src != "backtest_residual":
            warnings.append(f"SIGMA_{sigma_src.upper()}")

        if any(pd.isna(daily)):
            return {**base, "meu": {**no_meu, "reason": "FORECAST_UNAVAILABLE"}, "status": "FORECAST_UNAVAILABLE",
                    "alert_level": "MANUAL_REVIEW", "warnings": warnings + ["FORECAST_UNAVAILABLE"],
                    "explanation": "Không đủ lịch sử để dự báo; cần nhập hàng thủ công."}
        if fstatus == "INSUFFICIENT_HISTORY":
            warnings.append("INSUFFICIENT_HISTORY")
        if confidence == "LOW":
            warnings.append("LOW_CONFIDENCE")
        if ip < 0:
            return {**base, "meu": {**no_meu, "reason": "INVENTORY_DATA_CHECK"}, "status": "INVENTORY_DATA_CHECK",
                    "alert_level": "MANUAL_REVIEW", "warnings": warnings + ["NEGATIVE_INVENTORY_POSITION"],
                    "explanation": "Inventory position âm (reserved > on_hand + on_order). "
                                   "Cần kiểm tra dữ liệu reserved/on_order trước khi đề xuất."}
        try:
            ltd = lead_time_demand(daily, L_days)
        except HorizonInsufficientError:
            return {**base, "meu": {**no_meu, "reason": "HORIZON_INSUFFICIENT"}, "status": "HORIZON_INSUFFICIENT",
                    "alert_level": "MANUAL_REVIEW", "warnings": warnings + ["HORIZON_INSUFFICIENT"],
                    "explanation": f"Lead time {L_days} ngày dài hơn horizon dự báo 7 ngày; "
                                   "không ngoại suy. Cần duyệt thủ công hoặc mở rộng horizon."}

        ss = safety_stock(sigma, L_days, req.service_level)
        rop = reorder_point(ltd, ss)
        rop_qty = basic_order_qty(ip, rop, pack, moq)
        mean_daily = max(float(np.mean(daily)), 1e-9)
        cover = ip / mean_daily
        alert = "CRITICAL" if ip < ltd else ("WARNING" if ip <= rop else "OK")
        result = {**base, "lead_time_demand": _f(ltd), "safety_stock": _f(ss), "reorder_point": _f(rop),
                  "rop_order_qty": rop_qty, "days_of_cover": _f(cover, 1), "alert_level": alert}

        if ip > rop:
            result.update(status="NO_REORDER_NEEDED", suggested_order_qty=0,
                          meu={**no_meu, "reason": "IP_ABOVE_ROP"}, warnings=warnings,
                          explanation=(f"Tồn khả dụng {ip:.0f} > điểm đặt hàng {rop:.1f} "
                                       f"(nhu cầu {L_days} ngày lead time {ltd:.1f} + safety stock {ss:.1f}); "
                                       f"đủ bán khoảng {cover:.1f} ngày. Chưa cần nhập."))
            return result

        final_qty, meu = rop_qty, {**no_meu, "reason": "DISABLED_BY_REQUEST"}
        if req.use_meu:
            costs, src = (req.costs.model_dump() if req.costs else None), "request"
            if costs is None:
                costs, src = self.default_costs(req.sku_id), "product_master_demo_assumption"
            try:
                m = optimize_order_qty(daily, sigma, ip, L_days, req.review_period_days, costs, pack, moq, rop_qty)
                meu = {"enabled": True, "cost_source": src, **m}
                final_qty = m["recommended_qty"]
            except MEUInputMissingError as e:
                warnings.append("MEU_INPUT_MISSING")
                meu = {**no_meu, "reason": str(e)}
        expl = (f"Tồn khả dụng {ip:.0f} <= điểm đặt hàng {rop:.1f} "
                f"(nhu cầu lead time {L_days} ngày = {ltd:.1f}, safety stock {ss:.1f} @ service level "
                f"{req.service_level:.0%}). Lượng theo ROP: {rop_qty} (pack {pack}, MOQ {moq}).")
        if meu.get("enabled"):
            expl += (f" MEU chọn {final_qty} đơn vị (utility kỳ vọng {meu['expected_utility']:,.0f} so với "
                     f"{meu['expected_utility_reference_qty']:,.0f} nếu đặt theo ROP).")
        if alert == "CRITICAL":
            expl += " CẢNH BÁO: tồn hiện tại không đủ bán đến khi hàng về."
        result.update(status="REORDER_RECOMMENDED", suggested_order_qty=int(final_qty), meu=meu,
                      warnings=warnings, explanation=expl)
        return result


_service: IntelligenceService | None = None


def get_service() -> IntelligenceService:
    global _service
    if _service is None:
        _service = IntelligenceService()
    return _service
