"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, cart, money, saveCart, session, type CartItem, type Order, type Store } from "../../../lib/demo";
export default function CartPage() {
  const router = useRouter();
  const [items, setItems] = useState<CartItem[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [storeId, setStoreId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { queueMicrotask(() => setItems(cart())); api<Store[]>("/api/v1/stores").then(data => { const demo = data.filter(x => /^S\d+$/.test(x.code)); setStores(demo); setStoreId(demo[0]?.id || ""); }).catch(e => setError(e.message)); }, []);
  function update(id: string, quantity: number) { const next = items.map(item => item.product.id === id ? { ...item, quantity: Math.max(0, Math.min(quantity, Number(item.product.available_qty))) } : item).filter(item => item.quantity > 0); setItems(next); saveCart(next); }
  async function checkout() {
    if (!session()) { router.push("/login"); return; }
    if (!storeId || !items.length) return;
    setBusy(true); setError("");
    try {
      const order = await api<Order>("/api/v1/orders", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ store_id: storeId, items: items.map(item => ({ product_id: item.product.id, quantity: item.quantity })) }) });
      saveCart([]); setItems([]); router.push(`/orders?created=${order.id}`);
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  return <section className="sg-container py-14"><div className="mx-auto max-w-3xl rounded-2xl border border-border bg-white p-8 shadow-sm">
    <h1 className="text-3xl font-bold">Giỏ hàng</h1>
    {items.length === 0 ? <p className="mt-5">Giỏ hàng trống. <Link href="/products" className="text-primary underline">Chọn sản phẩm</Link></p> : <div className="mt-6 space-y-4">{items.map(item => <div key={item.product.id} className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
      <div><p className="font-semibold">{item.product.name}</p><p className="text-sm text-muted">{money(item.product.selling_price)} / {item.product.unit}</p></div>
      <label>Số lượng <input type="number" min="0" max={item.product.available_qty} value={item.quantity} onChange={e => update(item.product.id, Number(e.target.value))} className="ml-2 w-20 rounded-lg border border-border p-2" /></label>
      <strong>{money(Number(item.product.selling_price) * item.quantity)}</strong>
    </div>)}</div>}
    <p className="mt-5 text-right text-xl font-bold">Tổng: {money(items.reduce((sum, item) => sum + Number(item.product.selling_price) * item.quantity, 0))}</p>
    <label className="mt-5 block">Cửa hàng nhận đơn<select value={storeId} onChange={e => setStoreId(e.target.value)} className="ml-3 rounded-lg border border-border p-2">{stores.map(store => <option key={store.id} value={store.id}>{store.name}</option>)}</select></label>
    <p className="mt-2 text-sm text-muted">Chọn S001 cho luồng demo. Checkout xác nhận đơn và giữ tồn kho; không xử lý thanh toán.</p>
    {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}
    <button type="button" disabled={busy || !items.length || !storeId} onClick={checkout} className="mt-6 rounded-xl bg-primary px-6 py-3 font-semibold text-white disabled:opacity-50">{busy ? "Đang đặt hàng…" : "Đặt hàng"}</button>
  </div></section>;
}
