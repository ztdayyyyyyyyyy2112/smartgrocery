import HeroSection from "../../components/storefront/HeroSection";
import CategoryGrid from "../../components/storefront/CategoryGrid";
import FeaturedProducts from "../../components/storefront/FeaturedProducts";

export default function StorefrontHomePage() {
  return (
    <>
      <HeroSection />
      <CategoryGrid />
      <FeaturedProducts />

      <section className="border-t border-border bg-white">
        <div className="sg-container py-16 md:py-20">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center rounded-full border border-primary-light bg-primary-light px-3 py-1 text-sm font-semibold text-primary-dark">
              Smart intelligence
            </span>

            <h2 className="mt-6 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
              Smarter grocery shopping for modern households
            </h2>

            <p className="mt-4 text-base text-muted md:text-lg">
              SmartGrocery combines fresh product discovery, demand-aware replenishment,
              and operational insight to help customers and merchants make faster,
              better grocery decisions.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
