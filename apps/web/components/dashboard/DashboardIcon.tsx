import type { ReactNode } from "react";

export type DashboardIconName =
  | "overview"
  | "inventory"
  | "orders"
  | "forecasting"
  | "recommendations"
  | "suppliers"
  | "procurement";

const icons: Record<DashboardIconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="8" height="8" rx="1.5" />
      <rect x="13" y="3" width="8" height="5" rx="1.5" />
      <rect x="13" y="10" width="8" height="11" rx="1.5" />
      <rect x="3" y="13" width="8" height="8" rx="1.5" />
    </>
  ),
  inventory: (
    <>
      <path d="m12 3 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5M3 16l9 5 9-5M12 13v8" />
    </>
  ),
  orders: (
    <>
      <path d="M7 3h8l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
      <path d="M15 3v5h5M9 13h6M9 17h6" />
    </>
  ),
  forecasting: (
    <>
      <path d="M3 3v18h18" />
      <path d="m7 14 4-4 3 3 6-7" />
    </>
  ),
  recommendations: (
    <>
      <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
      <path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14ZM5 16l.7 1.3L7 18l-1.3.7L5 20l-.7-1.3L3 18l1.3-.7L5 16Z" />
    </>
  ),
  suppliers: (
    <>
      <path d="M3 21V8l6 3V8l6 3V4h5v17H3Z" />
      <path d="M7 15h2M12 15h2M17 15h1M7 18h2M12 18h2M17 18h1" />
    </>
  ),
  procurement: (
    <>
      <path d="M3 3h2l2.4 12.2a2 2 0 0 0 2 1.6h8.8a2 2 0 0 0 1.9-1.4L22 8H6" />
      <circle cx="10" cy="20" r="1" />
      <circle cx="18" cy="20" r="1" />
    </>
  ),
};

type DashboardIconProps = {
  name: DashboardIconName;
  className?: string;
};

export default function DashboardIcon({
  name,
  className = "h-4 w-4",
}: DashboardIconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {icons[name]}
    </svg>
  );
}
