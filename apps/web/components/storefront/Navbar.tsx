"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navigation = [
  { label: "Home", href: "/" },
  { label: "Products", href: "/products" },
  { label: "Merchant", href: "/dashboard" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  function isActive(href: string) {
    if (href === "/") {
      return pathname === "/";
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-white/95 backdrop-blur-sm">
      <div className="sg-container flex h-20 items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2" onClick={() => setMenuOpen(false)}>
          <span className="text-2xl" aria-hidden="true">🥬</span>
          <span className="text-xl font-extrabold tracking-tight text-primary-dark">SmartGrocery</span>
        </Link>

        <nav aria-label="Main navigation" className="hidden items-center gap-7 md:flex">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              className={`font-medium transition-colors ${
                isActive(item.href) ? "text-primary" : "text-foreground hover:text-primary"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/cart"
            className="rounded-lg border border-border px-4 py-2 font-medium text-foreground transition-colors hover:border-primary hover:text-primary"
          >
            🛒 Cart
          </Link>

          <Link href="/login" className="rounded-xl bg-primary px-4 py-2.5 font-semibold text-white transition hover:bg-primary-dark">
            Login
          </Link>
        </div>

        <button
          type="button"
          className="rounded-lg border border-border p-2.5 md:hidden"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          onClick={() => setMenuOpen((previous) => !previous)}
        >
          <span aria-hidden="true" className="text-xl">
            {menuOpen ? "✕" : "☰"}
          </span>
        </button>
      </div>

      {menuOpen && (
        <nav id="mobile-navigation" aria-label="Mobile navigation" className="border-t border-border bg-white md:hidden">
          <div className="sg-container flex flex-col gap-4 py-5">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive(item.href) ? "page" : undefined}
                className={
                  isActive(item.href)
                    ? "font-semibold text-primary"
                    : "font-medium text-foreground hover:text-primary"
                }
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}

            <Link href="/cart" onClick={() => setMenuOpen(false)} className="font-medium text-foreground hover:text-primary">
              🛒 Cart
            </Link>

            <Link href="/login" onClick={() => setMenuOpen(false)} className="rounded-xl bg-primary px-4 py-2.5 text-center font-semibold text-white hover:bg-primary-dark">
              Login
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}