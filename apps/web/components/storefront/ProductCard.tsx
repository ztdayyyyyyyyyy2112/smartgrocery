import Image from "next/image";
import Badge from "../ui/Badge";
import Button from "../ui/Button";

export type ProductCardProps = {
  name: string;
  category: string;
  price: number;
  unit: string;
  stock: "In stock" | "Low stock";
  imageSrc: string;
  description: string;
};

export default function ProductCard({
  name,
  category,
  price,
  unit,
  stock,
  imageSrc,
  description,
}: ProductCardProps) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl bg-primary-light">
        <Image
          src={imageSrc}
          alt={name}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
          className="object-cover"
        />
        <div className="absolute right-3 top-3">
          <Badge tone={stock === "In stock" ? "success" : "warning"}>{stock}</Badge>
        </div>
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
