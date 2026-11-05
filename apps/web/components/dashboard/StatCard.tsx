type StatCardProps = {
  label: string;
  value: string;
  change: string;
  icon: string;
};

export default function StatCard({ label, value, change, icon }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-muted">{label}</p>
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-light text-xl">
          {icon}
        </span>
      </div>

      <div className="mt-5 flex items-end justify-between gap-3">
        <h3 className="text-3xl font-bold tracking-tight text-foreground">{value}</h3>
      </div>

      <p className="mt-4 text-sm font-medium text-primary-dark">{change}</p>
    </div>
  );
}
