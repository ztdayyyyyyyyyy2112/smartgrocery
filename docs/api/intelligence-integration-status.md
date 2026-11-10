# Intelligence integration — demo contract

The tracked `database/demo/*.csv` catalog uses the same business keys as the intelligence dataset: `Store.code = S001…S003`, `Product.sku = SKU001…SKU032`. Existing legacy seed rows are preserved. PostgreSQL UUIDs remain internal and are mapped in `services/api/app/intelligence.py`.

For each forecast job the backend worker reads sellable non-expired batch stock and reservations, plus quantities in sent purchase orders. It sends these live quantities to the AI batch endpoint. The AI returns 7-day demand and replenishment calculations based on the synthetic historical sales ending 09/11/2026. The worker validates Store–SKU identities, maps the SKU back to the product UUID, and stores forecasts and positive replenishment recommendations. The merchant alone approves a recommendation and creates/receives a purchase order.

The synthetic sales history is fixed; checkout changes the inventory input and thus the replenishment decision, but it does not retrain the forecasting model. Every job records the AI history's `as_of` date, so the dashboard must show that date. Do not present this as a rolling production forecast. To use new real sales data, add a verified ingestion/training process and rerun model evaluation.

`FORECAST_AUTORUN=true` enables Celery dispatch when a job is created. It is set in Docker Compose and `.env.example`; API CI leaves it false to preserve focused backend tests. Failures mark the job `failed` with an error message; the frontend can retry by creating a new job. The full Docker demo is checked by `scripts/demo_smoke.py` in CI.
