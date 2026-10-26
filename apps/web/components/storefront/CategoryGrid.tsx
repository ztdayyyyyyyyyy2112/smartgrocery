import Image from "next/image";
import { groceryCategories } from "../../lib/mock-data";

export default function CategoryGrid() {
  return (
    <section className="bg-primary-light/50 py-8 md:py-10">
      <div className="sg-container">
        <div className="overflow-hidden rounded-xl border border-border bg-white">
          <h2 className="border-b border-border px-5 py-4 text-lg font-semibold uppercase tracking-wide text-foreground">
            Categories
          </h2>
          <div className="grid grid-cols-2 gap-px bg-border sm:grid-cols-3 lg:grid-cols-6">
            {groceryCategories.map((category, index) => (
              <article
                key={category.name}
                className="flex min-w-0 flex-col items-center bg-white px-3 py-5 text-center transition-colors hover:bg-primary-light/40"
              >
                <div className="relative h-20 w-20 overflow-hidden rounded-full bg-primary-light sm:h-24 sm:w-24">
                  <Image
                    src={category.imageSrc}
                    alt={category.name}
                    fill
                    loading={index === 0 ? "eager" : "lazy"}
                    sizes="(max-width: 640px) 80px, 96px"
                    className="object-cover"
                  />
                </div>
                <h3 className="mt-3 text-sm font-semibold text-foreground sm:text-base">
                  {category.name}
                </h3>
                <p className="mt-1 text-xs text-muted">{category.description}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
