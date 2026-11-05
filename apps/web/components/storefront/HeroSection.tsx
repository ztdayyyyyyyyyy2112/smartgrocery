import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="bg-gradient-to-b from-primary-light/80 to-white py-12 md:py-16">
      <div className="sg-container grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <span className="inline-flex items-center rounded-full border border-primary/20 bg-white px-3 py-1 text-sm font-semibold text-primary-dark">
            Smart grocery delivery
          </span>
          <h1 className="mt-6 text-4xl font-black tracking-tight text-foreground md:text-5xl lg:text-6xl">
            Fresh groceries, smarter everyday living.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-muted">
            Discover quality produce, pantry essentials, and household staples curated for
            healthy routines and fast family shopping.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/products"
              className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-dark focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-primary-dark"
            >
              Shop Now
            </Link>
            <Link
              href="/products"
              className="inline-flex items-center justify-center rounded-xl border border-border bg-white px-4 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary hover:text-primary focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Explore Products
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap gap-6 text-sm font-medium text-foreground">
            <span>✔ Fresh produce</span>
            <span>✔ Same-day essentials</span>
            <span>✔ Smart recommendations</span>
          </div>
        </div>

        <div className="relative">
          <div className="rounded-[28px] border border-primary/20 bg-white p-6 shadow-xl shadow-primary/5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-muted">Today’s basket</p>
                <h2 className="mt-2 text-2xl font-bold text-foreground">Healthy essentials</h2>
              </div>
              <span className="rounded-full bg-primary-light px-3 py-1 text-sm font-semibold text-primary-dark">
                24 items
              </span>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {[
                ["🥬", "Leafy greens", "110,000₫"],
                ["🍋", "Citrus mix", "80,000₫"],
                ["🥛", "Fresh milk", "48,000₫"],
                ["🥩", "Protein pack", "180,000₫"],
              ].map(([icon, label, price]) => (
                <div key={label} className="rounded-2xl border border-border bg-background p-4">
                  <div className="text-3xl">{icon}</div>
                  <p className="mt-3 font-semibold text-foreground">{label}</p>
                  <p className="mt-1 text-sm text-muted">{price}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
