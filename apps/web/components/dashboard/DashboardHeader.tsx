"use client";

import { usePathname } from "next/navigation";
import Badge from "../ui/Badge";

const titleMap: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/inventory": "Inventory",
  "/dashboard/orders": "Orders",
  "/dashboard/forecasting": "AI Forecasting",
  "/dashboard/recommendations": "Recommendations",
  "/dashboard/suppliers": "Suppliers",
  "/dashboard/procurement": "Procurement",
};

export default function DashboardHeader() {
  const pathname = usePathname();
  const currentTitle = titleMap[pathname] ?? "Overview";

  return (
    <header className="border-b border-border bg-white px-4 py-4 md:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary-dark">
            Merchant dashboard
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            {currentTitle}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Badge tone="success">Live demo</Badge>
          <div className="flex items-center gap-3 rounded-xl border border-border bg-background px-3 py-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-base font-bold text-white">
              M
            </span>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-semibold text-foreground">Merchant</p>
              <p className="text-xs text-muted">Operations view</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
