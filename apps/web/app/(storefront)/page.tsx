import HeroSection from "../../components/storefront/HeroSection";
import CategoryGrid from "../../components/storefront/CategoryGrid";
import LiveCatalog from "../../components/storefront/LiveCatalog";

export default function StorefrontHomePage() {
  return (
    <>
      <HeroSection />
      <CategoryGrid />
      <div id="featured-products" className="bg-[#f5f5f5]">
        <LiveCatalog compact />
      </div>
    </>
  );
}
