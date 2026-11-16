"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Image from "next/image";
import { addToCart, api, money, selectedStore, session, type Product } from "../../lib/demo";
export default function ProductDetail({ id }: { id: string }) {
  const router = useRouter();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState("");
  const [added, setAdded] = useState(false);
  useEffect(() => { const store = selectedStore(); api<Product>(`/api/v1/products/${id}${store ? `?store_id=${store}` : ""}`).then(setProduct).catch(e => setError(e.message)); }, [id]);
  return <section className="sg-container py-14"><Link href="/products" className="text-primary underline">← Sản phẩm</Link>
    {error && <p role="alert" className="mt-6 text-red-700">{error}</p>}
    {!product && !error && <p className="mt-6">Đang tải…</p>}
    {product && <div className="mt-6 max-w-2xl rounded-2xl border border-border bg-white p-8">
      {product.image_url && <div className="relative mb-4 aspect-[4/3]"><Image src={product.image_url} alt={product.name} fill sizes="(max-width: 768px) 100vw, 700px" className="rounded-xl object-cover" /></div>}
      <p className="text-sm text-muted">{product.sku}</p><h1 className="mt-2 text-3xl font-bold">{product.name}</h1>
      <p className="mt-4">{product.description || "Sản phẩm trong catalog demo SmartGrocery."}</p>
      <p className="mt-4 text-2xl font-bold text-primary-dark">{money(product.selling_price)}</p>
      <p className="mt-2">Tồn khả dụng: {product.available_qty} {product.unit}</p>
      <button type="button" disabled={Number(product.available_qty) <= 0} onClick={() => { if (session()?.user.role !== "customer") { router.push("/login"); return; } void addToCart(product).then(() => setAdded(true)).catch(err => setError(err.message)); }} className="mt-6 rounded-xl bg-primary px-6 py-3 font-semibold text-white disabled:opacity-50">Thêm vào giỏ</button>
      {added && <p role="status" className="mt-3">Đã thêm vào giỏ. <Link href="/cart" className="underline">Xem giỏ hàng</Link></p>}
    </div>}
  </section>;
}
