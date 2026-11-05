import { groceryCategories } from "../../lib/mock-data";

export default function CategoryGrid() {
  return (
    <section className="bg-background py-16 md:py-20">
      <div className="sg-container">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
              Categories
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
              Shop by essentials
            </h2>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {groceryCategories.map((category) => (
            <article
              key={category.name}
              className="rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-light text-3xl shadow-sm">
                {category.icon}
              </div>
              <h3 className="text-xl font-semibold text-foreground">{category.name}</h3>
              <p className="mt-2 text-sm text-muted">{category.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
