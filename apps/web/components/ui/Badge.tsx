import type { ReactNode } from "react";

type BadgeProps = {
  children: ReactNode;
  className?: string;
  tone?: "primary" | "success" | "warning" | "neutral";
};

export default function Badge({
  children,
  className = "",
  tone = "primary",
}: BadgeProps) {
  const toneClasses: Record<NonNullable<BadgeProps["tone"]>, string> = {
    primary: "border-primary/20 bg-primary-light text-primary-dark",
    success: "border-success/20 bg-emerald-50 text-emerald-700",
    warning: "border-warning/30 bg-amber-50 text-amber-700",
    neutral: "border-border bg-background text-muted",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
