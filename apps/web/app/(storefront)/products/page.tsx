import ProductCard from "../../../components/storefront/ProductCard";
import { featuredProducts } from "../../../lib/mock-data";

export default function ProductsPage() {
  return (
    <section className="sg-container py-16 md:py-20">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
          Marketplace
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Grocery products
        </h1>
        <p className="mt-3 text-base text-muted">
          Explore sample products from the SmartGrocery demo catalog.
        </p>
      </div>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {featuredProducts.map((product) => (
          <ProductCard
            key={product.id}
            name={product.name}
            category={product.category}
            price={product.price}
            unit={product.unit}
            stock={product.stock}
            imageSrc={product.imageSrc}
            description={product.description}
          />
        ))}
      </div>
    </section>
  );
}
