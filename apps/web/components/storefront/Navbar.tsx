"use client";

import Image from "next/image";
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
    <header className="sticky top-0 z-50 border-b border-sky-200 bg-primary-light">
      <div className="sg-container flex min-h-20 items-center gap-4 py-3 md:gap-8">
        <Link
          href="/"
          aria-label="SmartGrocery home"
          className="flex shrink-0 items-center gap-2"
          onClick={() => setMenuOpen(false)}
        >
          <Image
            src="/logo.png"
            alt=""
            width={48}
            height={48}
            priority
            className="h-10 w-10 object-contain sm:h-12 sm:w-12"
          />
          <span className="text-lg font-extrabold tracking-tight text-primary-dark sm:text-xl">
            SmartGrocery
          </span>
        </Link>

        <Link
          href="/products"
          aria-label="Browse grocery products"
          className="flex min-w-0 flex-1 items-center justify-center gap-3 rounded-lg border border-sky-200 bg-white px-3 py-2.5 text-sm text-muted shadow-sm transition hover:border-primary sm:justify-between"
        >
          <span className="hidden min-w-0 flex-1 truncate sm:inline">
            Browse products and categories
          </span>
          <span aria-hidden="true" className="flex h-8 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-white">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="10.8" cy="10.8" r="6.8" />
              <path d="m16 16 4.5 4.5" />
            </svg>
          </span>
        </Link>

        <div className="hidden shrink-0 items-center gap-3 sm:flex">
          <Link
            href="/cart"
            aria-label="Shopping cart"
            className="rounded-lg px-3 py-2 font-semibold text-primary-dark transition hover:bg-white/70"
          >
            Cart
          </Link>
          <Link
            href="/login"
            className="rounded-lg bg-primary px-4 py-2.5 font-semibold text-white transition hover:bg-primary-dark"
          >
            Login
          </Link>
        </div>

        <button
          type="button"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-sky-300 bg-white text-primary-dark sm:hidden"
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

      <nav aria-label="Main navigation" className="hidden border-t border-sky-200/80 sm:block">
        <div className="sg-container flex items-center gap-7 py-2.5">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              className={`text-sm font-medium transition-colors ${
                isActive(item.href) ? "text-primary-dark" : "text-foreground hover:text-primary-dark"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>

      {menuOpen && (
        <nav
          id="mobile-navigation"
          aria-label="Mobile navigation"
          className="border-t border-sky-200 bg-white sm:hidden"
        >
          <div className="sg-container flex flex-col gap-1 py-3">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive(item.href) ? "page" : undefined}
                className={`rounded-lg px-3 py-2.5 font-medium ${
                  isActive(item.href)
                    ? "bg-primary-light text-primary-dark"
                    : "text-foreground hover:bg-primary-light"
                }`}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <Link
              href="/cart"
              className="rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-primary-light"
              onClick={() => setMenuOpen(false)}
            >
              Cart
            </Link>
            <Link
              href="/login"
              className="rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-primary-light"
              onClick={() => setMenuOpen(false)}
            >
              Login
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}