"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, money, session, type Order } from "../../../lib/demo";
export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { if (!session()) { queueMicrotask(() => { setError("Đăng nhập để xem đơn hàng."); setLoading(false); }); return; } api<Order[]>("/api/v1/orders").then(setOrders).catch(e => setError(e.message)).finally(() => setLoading(false)); }, []);
  return <section className="sg-container py-14"><h1 className="text-3xl font-bold">Đơn hàng của tôi</h1>
    {loading && <p className="mt-5">Đang tải…</p>}{error && <p role="alert" className="mt-5 text-red-700">{error} <Link href="/login" className="underline">Đăng nhập</Link></p>}
    {!loading && !error && orders.length === 0 && <p className="mt-5">Chưa có đơn hàng.</p>}
    <div className="mt-6 space-y-3">{orders.map(order => <div key={order.id} className="rounded-xl border border-border bg-white p-5"><p className="font-semibold">Đơn {order.id.slice(0, 8)} · {order.status}</p><p>{order.items.length} sản phẩm · {money(order.total)}</p></div>)}</div>
  </section>;
}
