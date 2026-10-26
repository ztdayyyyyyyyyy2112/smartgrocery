import Navbar from "../../components/storefront/Navbar";
import Footer from "../../components/storefront/Footer";

export default function StorefrontLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main id="main-content" className="flex-1">
        {children}
      </main>

      <Footer />
    </div>
  );
}
