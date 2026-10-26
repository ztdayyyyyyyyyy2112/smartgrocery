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

function CartIcon({ className }: { className: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 3h2l2.4 12.2a2 2 0 0 0 2 1.6h8.8a2 2 0 0 0 1.9-1.4L22 8H6" />
      <circle cx="10" cy="20" r="1" />
      <circle cx="18" cy="20" r="1" />
    </svg>
  );
}

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
    <header className="sticky top-0 z-50 border-b border-primary-dark bg-primary-dark">
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
          <span className="text-lg font-extrabold tracking-tight text-white sm:text-xl">
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
            title="Shopping cart"
            aria-current={pathname === "/cart" ? "page" : undefined}
            className="flex h-11 w-11 items-center justify-center rounded-lg text-white transition hover:bg-white/10"
          >
            <CartIcon className="h-7 w-7 text-white" />
          </Link>
          <Link
            href="/login"
            className="rounded-lg bg-white px-4 py-2.5 font-semibold text-primary-dark transition hover:bg-primary-light"
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

      <nav aria-label="Main navigation" className="hidden border-t border-white/15 bg-primary sm:block">
        <div className="sg-container flex items-center gap-7 py-2.5">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              className={`text-sm font-medium transition-colors ${
                isActive(item.href) ? "text-white underline underline-offset-4" : "text-white/85 hover:text-white"
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
              aria-label="Shopping cart"
              aria-current={pathname === "/cart" ? "page" : undefined}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-primary-light"
              onClick={() => setMenuOpen(false)}
            >
              <CartIcon className="h-5 w-5 text-primary-dark" />
              <span>Shopping cart</span>
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