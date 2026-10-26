import ProductCard from "./ProductCard";
import { featuredProducts } from "../../lib/mock-data";

export default function FeaturedProducts() {
  return (
    <section className="bg-white py-16 md:py-20">
      <div className="sg-container">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
              Featured products
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
              Fresh picks for your next order
            </h2>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {featuredProducts.map((product) => (
            <ProductCard
              key={product.id}
              name={product.name}
              category={product.category}
              price={product.price}
              unit={product.unit}
              stock={product.stock}
              imageLabel={product.imageLabel}
              description={product.description}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
