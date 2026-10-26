import Link from "next/link";

export default function ProductsPage() {
  return (
    <section className="sg-container py-16 md:py-20">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
          Products
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground md:text-5xl">
          Fresh picks for everyday essentials
        </h1>
        <p className="mt-4 text-lg text-muted">
          This is a placeholder storefront catalog for SmartGrocery. Product listings,
          filters, and detail pages will be connected to the live backend in later
          integration work.
        </p>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((item) => (
          <article key={item} className="sg-card">
            <div className="mb-4 flex h-48 items-center justify-center rounded-xl bg-primary-light text-5xl">
              {item % 2 === 0 ? "🥬" : "🍋"}
            </div>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-foreground">Sample Product {item}</h2>
              <span className="rounded-full bg-primary-light px-2.5 py-1 text-xs font-semibold text-primary-dark">
                Demo
              </span>
            </div>
            <p className="mt-2 text-sm text-muted">Fresh produce · 1kg</p>
            <div className="mt-5 flex items-center justify-between">
              <span className="text-2xl font-bold text-primary-dark">{item * 25000}₫</span>
              <Link href="/cart" className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:border-primary hover:text-primary">
                View cart
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
