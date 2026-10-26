import Link from "next/link";

const navigation = [
  { label: "Home", href: "/" },
  { label: "Products", href: "/products" },
  { label: "Cart", href: "/cart" },
  { label: "Login", href: "/login" },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-white">
      <div className="sg-container py-10 md:py-12">
        <div className="grid gap-8 md:grid-cols-[1.3fr_0.7fr_1fr]">
          <div>
            <div className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-black text-white"
              >
                S
              </span>
              <span className="text-xl font-extrabold tracking-tight text-primary-dark">SmartGrocery</span>
            </div>
            <p className="mt-4 max-w-md text-sm text-muted">
              SmartGrocery helps households discover quality groceries, manage essentials,
              and explore an intelligent shopping experience built for modern living.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted">Quick links</h3>
            <ul className="mt-4 space-y-3 text-sm text-foreground">
              {navigation.map((item) => (
                <li key={item.href}>
                  <Link href={item.href} className="hover:text-primary">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted">Academic project</h3>
            <p className="mt-4 text-sm text-muted">
              SmartGrocery is a university project demonstrating a modern grocery commerce
              experience with storefront and merchant dashboard interfaces.
            </p>
          </div>
        </div>

        <div className="mt-8 border-t border-border pt-6 text-sm text-muted">
          © {year} SmartGrocery. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
