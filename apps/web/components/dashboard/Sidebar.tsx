"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: "📊" },
  { label: "Inventory", href: "/dashboard/inventory", icon: "📦" },
  { label: "Orders", href: "/dashboard/orders", icon: "🧾" },
  { label: "AI Forecasting", href: "/dashboard/forecasting", icon: "📈" },
  { label: "Recommendations", href: "/dashboard/recommendations", icon: "🤖" },
  { label: "Suppliers", href: "/dashboard/suppliers", icon: "🏭" },
  { label: "Procurement", href: "/dashboard/procurement", icon: "🛒" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <>
      <button
        type="button"
        className="fixed left-4 top-4 z-40 rounded-xl border border-border bg-white p-2.5 shadow-sm lg:hidden"
        aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
        aria-expanded={isOpen}
        aria-controls="dashboard-sidebar"
        onClick={() => setIsOpen((current) => !current)}
      >
        <span aria-hidden="true" className="text-xl">☰</span>
      </button>

      <aside
        id="dashboard-sidebar"
        className={`${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } fixed inset-y-0 left-0 z-30 w-72 border-r border-border bg-white p-5 shadow-lg transition-transform duration-200 lg:static lg:w-72 lg:translate-x-0 lg:shadow-none ${
          isOpen ? "block" : "hidden lg:block"
        }`}
      >
        <div className="flex items-center justify-between gap-3 pb-6">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-lg font-black text-white"
            >
              S
            </span>
            <div>
              <p className="text-lg font-extrabold text-primary-dark">SmartGrocery</p>
              <p className="text-xs uppercase tracking-[0.2em] text-muted">Merchant</p>
            </div>
          </div>
        </div>

        <nav aria-label="Dashboard navigation" className="space-y-2">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                isActive(item.href)
                  ? "bg-primary-light text-primary-dark"
                  : "text-foreground hover:bg-background hover:text-primary"
              }`}
            >
              <span aria-hidden="true" className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
    </>
  );
}
