"""Pydantic schema cho AI API contract (docs/api/ai_contract.md).

ĐỀ XUẤT — cần Tuấn Anh (Backend) xác nhận trước khi xem là contract chính thức.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class InventoryInput(BaseModel):
    on_hand: float = Field(ge=0, description="Tồn kho thực tế khả dụng (Backend, đã loại hàng hỏng/khóa)")
    on_order: float = Field(default=0, ge=0, description="Đã đặt PO nhưng chưa nhận")
    reserved: float = Field(default=0, ge=0, description="Đã giữ chỗ cho đơn hàng chưa xuất kho")


class CostInput(BaseModel):
    selling_price: Optional[float] = Field(default=None, ge=0)
    purchase_cost: Optional[float] = Field(default=None, ge=0)
    holding_cost_per_unit: Optional[float] = Field(default=None, ge=0)
    stockout_penalty_per_unit: Optional[float] = Field(default=None, ge=0)
    waste_cost_per_unit: Optional[float] = Field(default=None, ge=0)
    salvage_value_per_unit: Optional[float] = Field(default=None, ge=0,
                                                    description="Mặc định = purchase_cost (hàng dư vẫn bán được kỳ sau)")


class ReplenishmentRequest(BaseModel):
    store_id: str = Field(min_length=1, examples=["S001"])
    sku_id: str = Field(min_length=1, examples=["SKU005"])
    forecast_horizon: int = Field(default=7, ge=1, le=7)
    inventory: InventoryInput
    lead_time_days: Optional[int] = Field(default=None, ge=1, le=60,
                                          description="Không truyền -> lấy từ product master")
    service_level: float = Field(default=0.95, gt=0.5, lt=1)
    review_period_days: int = Field(default=1, ge=0, le=6)
    pack_size: Optional[int] = Field(default=None, ge=1)
    moq: Optional[int] = Field(default=None, ge=0)
    costs: Optional[CostInput] = None
    use_meu: bool = True
    as_of_date: Optional[date] = Field(default=None, description="Mặc định: ngày dữ liệu bán hàng mới nhất")

    @model_validator(mode="after")
    def _strip(self):
        self.store_id = self.store_id.strip().upper()
        self.sku_id = self.sku_id.strip().upper()
        return self


class BatchReplenishmentRequest(BaseModel):
    items: list[ReplenishmentRequest] = Field(min_length=1, max_length=500)


class ForecastPoint(BaseModel):
    date: date
    horizon: int
    predicted_demand: float
    baseline_seasonal_naive: Optional[float] = None


class MEUScenario(BaseModel):
    label: str
    probability: float
    demand: float


class MEUResult(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    recommended_qty: Optional[int] = None
    expected_utility: Optional[float] = None
    expected_utility_no_order: Optional[float] = None
    expected_utility_reference_qty: Optional[float] = None
    protection_period_days: Optional[int] = None
    scenarios: list[MEUScenario] = []
    top_candidates: list[dict] = []
    cost_source: Optional[str] = None


Status = Literal["REORDER_RECOMMENDED", "NO_REORDER_NEEDED", "HORIZON_INSUFFICIENT",
                 "INSUFFICIENT_HISTORY", "INVENTORY_DATA_CHECK", "FORECAST_UNAVAILABLE"]


class ReplenishmentResponse(BaseModel):
    store_id: str
    sku_id: str
    product_name: Optional[str] = None
    model_version: str
    forecast_method: str
    generated_at: str
    as_of_date: date
    forecast: list[ForecastPoint]
    forecast_total: Optional[float] = None
    lead_time_days: int
    service_level: float
    sigma_daily: Optional[float] = None
    inventory_position: float
    lead_time_demand: Optional[float] = None
    safety_stock: Optional[float] = None
    reorder_point: Optional[float] = None
    rop_order_qty: Optional[int] = None
    suggested_order_qty: Optional[int] = None
    days_of_cover: Optional[float] = None
    meu: MEUResult
    status: Status
    alert_level: Literal["CRITICAL", "WARNING", "OK", "MANUAL_REVIEW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    requires_approval: bool = True
    warnings: list[str] = []
    explanation: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
