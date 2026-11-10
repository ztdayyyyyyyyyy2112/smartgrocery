"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { addToCart, api, money, type Product } from "../../lib/demo";

export default function LiveCatalog({ compact = false }: { compact?: boolean }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    api<{ items: Product[] }>("/api/v1/products?page_size=100")
      .then(data => setProducts(data.items.filter(item => /^SKU\d+$/.test(item.sku))))
      .catch(err => setError(err.message)).finally(() => setLoading(false));
  }, []);
  const visible = products.filter(item => `${item.sku} ${item.name}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
  return <section className="sg-container py-12">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-sm font-semibold uppercase text-primary-dark">Catalog thật từ API</p>
        <h1 className="mt-2 text-3xl font-bold text-foreground">Sản phẩm SmartGrocery</h1></div>
      <input aria-label="Tìm sản phẩm" value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm tên hoặc SKU" className="rounded-xl border border-border px-4 py-3" />
    </div>
    {notice && <p role="status" className="mt-4 text-primary-dark">{notice}</p>}
    {loading && <p className="mt-6">Đang tải sản phẩm…</p>}
    {error && <p role="alert" className="mt-6 text-red-700">{error}</p>}
    {!loading && !error && visible.length === 0 && <p className="mt-6">Không có sản phẩm phù hợp.</p>}
    <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
      {(compact ? visible.slice(0, 8) : visible).map(product => <article key={product.id} className="flex flex-col rounded-2xl border border-border bg-white p-5 shadow-sm">
        <span className="text-xs font-semibold text-primary">{product.sku}</span>
        <Link href={`/products/${product.id}`} className="mt-2 text-xl font-semibold hover:text-primary">{product.name}</Link>
        <p className="mt-2 text-sm text-muted">Tồn khả dụng: {product.available_qty} {product.unit}</p>
        <p className="mt-3 text-lg font-bold text-primary-dark">{money(product.selling_price)}</p>
        <button type="button" disabled={Number(product.available_qty) <= 0} onClick={() => { addToCart(product); setNotice(`Đã thêm ${product.name} vào giỏ`); }} className="mt-auto rounded-xl bg-primary px-4 py-2.5 font-semibold text-white disabled:opacity-50">Thêm vào giỏ</button>
      </article>)}
    </div>
    {compact && <Link href="/products" className="mt-6 inline-block font-semibold text-primary-dark underline">Xem tất cả sản phẩm →</Link>}
  </section>;
}
