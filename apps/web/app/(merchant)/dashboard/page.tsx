import StatCard from "../../../components/dashboard/StatCard";

const stats = [
  { label: "Total Products", value: "2,486", change: "+12% vs last month", icon: "📦" },
  { label: "Active Orders", value: "184", change: "+8% today", icon: "🧾" },
  { label: "Low Stock Items", value: "27", change: "Needs review", icon: "⚠️" },
  { label: "Forecast Accuracy", value: "94.8%", change: "+2.4 pts", icon: "📈" },
];

export default function DashboardOverviewPage() {
  return (
    <div className="space-y-8">
      <section>
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
            Overview
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Merchant performance dashboard
          </h1>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <StatCard
              key={stat.label}
              label={stat.label}
              value={stat.value}
              change={stat.change}
              icon={stat.icon}
            />
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-foreground">Smart inventory management</h2>
        <p className="mt-4 max-w-3xl text-base text-muted">
          SmartGrocery uses demand insights, intelligent replenishment signals, and stock
          visibility to help merchants respond faster to seasonal trends, store demand, and
          supplier ordering cycles without disrupting the customer experience.
        </p>
      </section>
    </div>
  );
}
