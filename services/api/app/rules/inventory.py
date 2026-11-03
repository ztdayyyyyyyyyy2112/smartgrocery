from datetime import date, timedelta
from decimal import Decimal


def inventory_alerts(*, available: Decimal, nearest_expiry: date | None, low_stock_threshold: Decimal, expiry_warning_days: int = 3) -> list[str]:
    alerts: list[str] = []
    if available < low_stock_threshold:
        alerts.append("LOW_STOCK_ALERT")
    if nearest_expiry is not None:
        if nearest_expiry < date.today():
            alerts.append("DO_NOT_SELL_EXPIRED")
        elif nearest_expiry <= date.today() + timedelta(days=expiry_warning_days):
            alerts.append("EXPIRY_WARNING")
    return alerts
