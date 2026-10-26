"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import DashboardIcon, { type DashboardIconName } from "./DashboardIcon";

const navigation: { label: string; href: string; icon: DashboardIconName }[] = [
  { label: "Overview", href: "/dashboard", icon: "overview" },
  { label: "Inventory", href: "/dashboard/inventory", icon: "inventory" },
  { label: "Orders", href: "/dashboard/orders", icon: "orders" },
  { label: "AI Forecasting", href: "/dashboard/forecasting", icon: "forecasting" },
  { label: "Recommendations", href: "/dashboard/recommendations", icon: "recommendations" },
  { label: "Suppliers", href: "/dashboard/suppliers", icon: "suppliers" },
  { label: "Procurement", href: "/dashboard/procurement", icon: "procurement" },
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
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
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
          <Link
            href="/"
            aria-label="SmartGrocery home"
            className="flex items-center gap-3 rounded-lg focus-visible:outline-offset-4"
          >
            <Image
              src="/logo.png"
              alt=""
              width={48}
              height={48}
              className="h-10 w-10 object-contain"
            />
            <div>
              <p className="text-lg font-extrabold text-primary-dark">SmartGrocery</p>
              <p className="text-xs uppercase tracking-[0.2em] text-muted">Merchant</p>
            </div>
          </Link>
        </div>

        <nav aria-label="Dashboard navigation" className="space-y-2">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? "page" : undefined}
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-3 rounded-xl border px-3 py-3 text-sm font-medium transition ${
                isActive(item.href)
                  ? "border-primary/20 bg-primary-light text-primary-dark"
                  : "border-border bg-white text-foreground hover:border-primary/40 hover:bg-primary-light/40 hover:text-primary-dark"
              }`}
            >
              <span
                aria-hidden="true"
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                  isActive(item.href)
                    ? "bg-white text-primary"
                    : "bg-background text-muted"
                }`}
              >
                <DashboardIcon name={item.icon} />
              </span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
    </>
  );
}
