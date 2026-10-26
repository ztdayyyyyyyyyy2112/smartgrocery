export default function CartPage() {
  return (
    <section className="sg-container py-16 md:py-20">
      <div className="mx-auto max-w-3xl rounded-2xl border border-border bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
          Cart
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground">Your shopping cart</h1>
        <p className="mt-4 text-lg text-muted">
          This demo cart placeholder shows the intended storefront flow without
          processing real checkout or payment operations.
        </p>

        <div className="mt-8 space-y-4">
          {[1, 2].map((item) => (
            <div key={item} className="flex items-center justify-between rounded-xl border border-border bg-background p-4">
              <div>
                <p className="font-semibold text-foreground">Fresh Cart Item {item}</p>
                <p className="text-sm text-muted">{item * 2} items · Demo cart entry</p>
              </div>
              <span className="text-lg font-semibold text-primary-dark">{item * 52000}₫</span>
            </div>
          ))}
        </div>

        <div className="mt-8 flex items-center justify-between border-t border-border pt-6">
          <span className="text-lg font-medium text-foreground">Estimated total</span>
          <span className="text-2xl font-bold text-primary-dark">128,000₫</span>
        </div>
      </div>
    </section>
  );
}
