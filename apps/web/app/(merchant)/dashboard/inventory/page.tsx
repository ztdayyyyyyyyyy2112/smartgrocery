export default function InventoryPage() {
  return (
    <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">Inventory</p>
      <h2 className="mt-3 text-3xl font-bold text-foreground">Stock overview</h2>
      <p className="mt-4 max-w-2xl text-muted">
        This page will display product-level stock counts, replenishment statuses, and low-stock alerts.
      </p>
    </section>
  );
}
