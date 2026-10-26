import Badge from "../ui/Badge";
import Button from "../ui/Button";

export type ProductCardProps = {
  name: string;
  category: string;
  price: number;
  unit: string;
  stock: "In stock" | "Low stock";
  imageLabel: string;
  description: string;
};

export default function ProductCard({
  name,
  category,
  price,
  unit,
  stock,
  imageLabel,
  description,
}: ProductCardProps) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between gap-3">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-light text-4xl shadow-sm">
          {imageLabel}
        </div>
        <Badge tone={stock === "In stock" ? "success" : "warning"}>{stock}</Badge>
      </div>

      <div className="mt-5 flex-1">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">{category}</p>
        <h3 className="mt-2 text-xl font-semibold text-foreground">{name}</h3>
        <p className="mt-2 text-sm text-muted">{description}</p>
      </div>

      <div className="mt-5 flex items-end justify-between gap-3">
        <div>
          <p className="text-2xl font-bold text-primary-dark">{price.toLocaleString("vi-VN")}₫</p>
          <p className="text-sm text-muted">{unit}</p>
        </div>
      </div>

      <Button type="button" variant="primary" className="mt-5 w-full" disabled aria-label={`Demo add ${name} to cart`}>
        Demo: Add to cart
      </Button>
    </article>
  );
}
