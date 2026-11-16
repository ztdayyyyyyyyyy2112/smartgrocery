"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, cart, loadCart, logout, selectedStore, session, type Product, type Session } from "../../lib/demo";

const navigation = [
  { label: "Trang chủ", href: "/" },
  { label: "Sản phẩm", href: "/products" },
  { label: "Đơn hàng", href: "/orders" },
  { label: "Kênh người bán", href: "/dashboard" },
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
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [current, setCurrent] = useState<Session | null>(null);
  const [count, setCount] = useState(0);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  useEffect(() => {
    const sync = () => { setCurrent(session()); setCount(cart().reduce((sum, item) => sum + item.quantity, 0)); };
    const accountChanged = () => { sync(); if (session()?.user.role === "customer") void loadCart().catch(() => {}); };
    accountChanged(); window.addEventListener("smartgrocery:session", accountChanged); window.addEventListener("smartgrocery:cart", sync); window.addEventListener("storage", accountChanged);
    return () => { window.removeEventListener("smartgrocery:session", accountChanged); window.removeEventListener("smartgrocery:cart", sync); window.removeEventListener("storage", accountChanged); };
  }, []);
  useEffect(() => { if (!query.trim()) return; let cancelled = false; const timer = setTimeout(() => { const store = selectedStore(); api<{ items: Product[] }>(`/api/v1/products?q=${encodeURIComponent(query.trim())}&page_size=6${store ? `&store_id=${store}` : ""}`).then(result => { if (!cancelled) setSuggestions(result.items); }).catch(() => { if (!cancelled) setSuggestions([]); }); }, 180); return () => { cancelled = true; clearTimeout(timer); }; }, [query]);
  const nav = navigation.filter(item => item.href !== "/dashboard" || current?.user.role === "merchant" || current?.user.role === "admin");

  function isActive(href: string) {
    if (href === "/") {
      return pathname === "/";
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <header className="sticky top-0 z-50 shadow-sm">
      <div className="bg-[#123d91] text-white">
        <div className="sg-container flex min-h-8 items-center justify-between gap-3 py-1 text-xs">
          <span className="hidden sm:inline">Mua sắm thông minh cùng SmartGrocery</span>
          {current ? (
            <span className="ml-auto truncate">Xin chào, {current.user.full_name}</span>
          ) : (
            <Link href="/login" className="ml-auto hover:underline">
              Đăng nhập / Đăng ký
            </Link>
          )}
        </div>
      </div>

      <div className="bg-gradient-to-r from-[#0754bd] to-[#1676dc] text-white">
        <div className="sg-container flex min-h-[76px] flex-wrap items-center gap-3 py-3 md:flex-nowrap md:gap-6">
          <Link
            href="/"
            aria-label="SmartGrocery - Trang chủ"
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

          <form
            className="relative order-3 flex min-w-0 basis-full rounded-lg bg-white md:order-none md:flex-1 md:basis-auto"
            onSubmit={(event) => {
              event.preventDefault();
              router.push(`/products?q=${encodeURIComponent(query.trim())}`);
              window.dispatchEvent(
                new CustomEvent("smartgrocery:search", { detail: query.trim() }),
              );
              setSuggestions([]);
            }}
          >
            <input
              aria-label="Tìm sản phẩm"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                if (!event.target.value.trim()) setSuggestions([]);
              }}
              placeholder="Tìm sản phẩm hoặc SKU"
              className="min-w-0 flex-1 rounded-lg px-3 py-2.5 text-foreground outline-none"
            />
            <button
              type="submit"
              aria-label="Tìm kiếm"
              className="m-1 flex w-12 items-center justify-center rounded-md bg-primary text-white transition hover:bg-primary-dark"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <circle cx="11" cy="11" r="7" />
                <path d="m16 16 4 4" />
              </svg>
            </button>
            {query.trim() && suggestions.length > 0 && (
              <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-lg border bg-white p-2 text-foreground shadow-lg">
                {suggestions.map((product) => (
                  <Link
                    key={product.id}
                    href={`/products/${product.id}`}
                    onClick={() => {
                      setQuery("");
                      setSuggestions([]);
                    }}
                    className="block rounded px-2 py-2 text-sm hover:bg-primary-light"
                  >
                    {product.name} · {product.sku}
                  </Link>
                ))}
              </div>
            )}
          </form>

          <div className="ml-auto hidden shrink-0 items-center gap-3 md:flex">
            {current?.user.role === "customer" && (
              <Link
                href="/cart"
                aria-label="Giỏ hàng"
                title="Giỏ hàng"
                aria-current={pathname === "/cart" ? "page" : undefined}
                className="relative flex h-11 w-11 items-center justify-center rounded-lg text-white transition hover:bg-white/10"
              >
                <CartIcon className="h-7 w-7 text-white" />
                {count > 0 && (
                  <span className="absolute -right-1 -top-1 rounded-full bg-red-600 px-1.5 text-xs font-bold text-white">
                    {count}
                  </span>
                )}
              </Link>
            )}
            {current ? (
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  router.push("/");
                }}
                className="rounded-lg bg-white px-3 py-2 text-sm font-semibold text-primary-dark"
              >
                Đăng xuất
              </button>
            ) : (
              <Link
                href="/login"
                className="rounded-lg bg-white px-4 py-2.5 font-semibold text-primary-dark"
              >
                Đăng nhập
              </Link>
            )}
          </div>

          <button
            type="button"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/40 bg-white text-primary-dark md:hidden"
            aria-label={menuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={menuOpen}
            aria-controls="mobile-navigation"
            onClick={() => setMenuOpen((previous) => !previous)}
          >
            <span aria-hidden="true" className="text-xl">
              {menuOpen ? "✕" : "☰"}
            </span>
          </button>
        </div>
      </div>

      <nav
        aria-label="Điều hướng chính"
        className="hidden border-t border-white/15 bg-primary-dark md:block"
      >
        <div className="sg-container flex items-center gap-7 py-2.5">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              className={`text-sm font-medium text-white transition-colors ${
                isActive(item.href) ? "underline underline-offset-4" : "hover:underline"
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
          aria-label="Điều hướng di động"
          className="border-t border-sky-200 bg-white md:hidden"
        >
          <div className="sg-container flex flex-col gap-1 py-3">
            {nav.map((item) => (
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
            {current?.user.role === "customer" && (
              <Link
                href="/cart"
                aria-label="Giỏ hàng"
                aria-current={pathname === "/cart" ? "page" : undefined}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-primary-light"
                onClick={() => setMenuOpen(false)}
              >
                <CartIcon className="h-5 w-5 text-primary-dark" />
                <span>Giỏ hàng</span>
                {count > 0 && (
                  <span className="rounded-full bg-red-600 px-2 text-xs text-white">
                    {count}
                  </span>
                )}
              </Link>
            )}
            {current ? (
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  router.push("/");
                }}
                className="rounded-lg px-3 py-2.5 text-left"
              >
                {current.user.full_name} · Đăng xuất
              </button>
            ) : (
              <Link
                href="/login"
                className="rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-primary-light"
                onClick={() => setMenuOpen(false)}
              >
                Đăng nhập
              </Link>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
