"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, money, session, wsUrl, type Forecast, type Inventory, type Order, type Product, type PurchaseOrder, type Recommendation, type Store, type Supplier } from "../../lib/demo";

type View = "overview" | "inventory" | "orders" | "forecasting" | "recommendations" | "suppliers" | "procurement";
type Job = { job_id: string; status: string; as_of?: string; error_message?: string };
const button = "rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-white disabled:opacity-50";
const card = "rounded-xl border border-border bg-white p-5 shadow-sm";

export default function LiveDashboard({ view }: { view: View }) {
  const router = useRouter();
  const [stores, setStores] = useState<Store[]>([]);
  const [storeId, setStoreId] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const [supplierName, setSupplierName] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const [ready, setReady] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, p, i, o, f, r, su, po] = await Promise.all([
        api<Store[]>("/api/v1/stores"), api<{ items: Product[] }>("/api/v1/products?page_size=100"),
        api<Inventory[]>("/api/v1/inventory"), api<Order[]>("/api/v1/orders"),
        api<Forecast[]>("/api/v1/forecasts"), api<Recommendation[]>("/api/v1/recommendations"),
        api<Supplier[]>("/api/v1/suppliers"), api<PurchaseOrder[]>("/api/v1/purchase-orders"),
      ]);
      const assigned = session()?.user.store_id;
      setStores(s.filter(x => /^S\d+$/.test(x.code) && (!assigned || x.id === assigned))); setProducts(p.items); setInventory(i);
      setOrders(o); setForecasts(f); setRecommendations(r); setSuppliers(su); setPurchaseOrders(po);
      setStoreId(current => assigned || current || s.find(x => x.code === "S001")?.id || "");
      setError("");
    } catch (err) { setError((err as Error).message); } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const current = session();
    if (!current || current.user.role === "customer") { router.replace("/login"); return; }
    queueMicrotask(() => { setReady(true); void load(); });
    const saved = localStorage.getItem("smartgrocery.demo.lastJob");
    if (saved) queueMicrotask(() => setJob({ job_id: saved, status: "queued" }));
  }, [load, router]);

  useEffect(() => {
    if (!ready) return;
    let socket: WebSocket | null = null, timer: ReturnType<typeof setTimeout> | null = null, stopped = false;
    function connect() {
      const url = wsUrl(); if (!url || stopped) return;
      socket = new WebSocket(url);
      socket.onopen = () => { setLive(true); void load(); };
      socket.onmessage = () => { void load(); };
      socket.onclose = () => { setLive(false); if (!stopped) timer = setTimeout(connect, 3000); };
      socket.onerror = () => socket?.close();
    }
    connect();
    return () => { stopped = true; if (timer) clearTimeout(timer); socket?.close(); };
  }, [ready, load]);

  useEffect(() => {
    if (!job?.job_id || ["succeeded", "failed"].includes(job.status)) return;
    const timer = setInterval(() => {
      api<Job>(`/api/v1/jobs/${job.job_id}`).then(next => { setJob(next); if (next.status === "succeeded") void load(); }).catch(err => setError(err.message));
    }, 2500);
    return () => clearInterval(timer);
  }, [job?.job_id, job?.status, load]);

  async function action(path: string, body?: unknown) {
    setBusy(true); setError(""); setNotice("");
    try { const result = await api<Record<string, unknown>>(path, { method: "POST", ...(body ? { body: JSON.stringify(body) } : {}) });
      setNotice(`Thành công: ${String(result.status || "đã lưu")}`); await load(); return result;
    } catch (err) { setError((err as Error).message); return null; } finally { setBusy(false); }
  }
  async function runForecast() {
    if (!storeId) return;
    const result = await action("/api/v1/jobs/forecasts", { store_id: storeId, horizon_days: 7 });
    if (result?.job_id) { const id = String(result.job_id); localStorage.setItem("smartgrocery.demo.lastJob", id); setJob({ job_id: id, status: String(result.status) }); }
  }
  async function receive(poId: string) {
    setBusy(true); setError("");
    try {
      const po = await api<PurchaseOrder>(`/api/v1/purchase-orders/${poId}`);
      const items = (po.items || []).filter(item => Number(item.quantity_ordered) > Number(item.quantity_received)).map((item, index) => ({
        product_id: item.product_id, quantity: Number(item.quantity_ordered) - Number(item.quantity_received),
        unit_cost: item.unit_cost, lot_code: `DEMO-${Date.now()}-${index}`,
      }));
      if (!items.length) throw new Error("PO không còn số lượng cần nhận.");
      await api(`/api/v1/purchase-orders/${poId}/receive`, { method: "POST", body: JSON.stringify({ items }) });
      setNotice("Đã nhận hàng; tồn kho đã tăng."); await load();
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  const productName = (id: string) => products.find(x => x.id === id)?.name || id.slice(0, 8);
  const selectedStore = stores.find(x => x.id === storeId);
  const stock = inventory.filter(x => x.store_id === storeId && /^SKU\d+$/.test(x.sku));
  const recs = recommendations.filter(x => x.store_id === storeId);
  const fcs = forecasts.filter(x => x.store_id === storeId);
  const pos = purchaseOrders.filter(x => x.store_id === storeId);
  const low = stock.filter(x => Number(x.available) <= 5);

  if (!ready) return <p>Đang kiểm tra tài khoản merchant…</p>;
  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-2xl font-bold">{({ overview: "Tổng quan", inventory: "Tồn kho", orders: "Đơn hàng", forecasting: "Dự báo AI", recommendations: "Gợi ý nhập", suppliers: "Nhà cung cấp", procurement: "Nhập hàng" })[view]}</h2><p className="text-sm text-muted">Dữ liệu từ API · WebSocket {live ? "đang kết nối" : "đang nối lại"}</p></div>
      <div className="flex gap-2"><select aria-label="Cửa hàng" value={storeId} onChange={e => setStoreId(e.target.value)} className="rounded-lg border border-border p-2">{stores.map(s => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select><button onClick={() => void load()} className={button}>Tải lại</button></div></div>
    {loading && <p>Đang tải dữ liệu…</p>}{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-700">{error}</p>}{notice && <p role="status" className="rounded-lg bg-green-50 p-3 text-green-800">{notice}</p>}
    {view === "overview" && <div className="grid gap-4 md:grid-cols-4">{[["Sản phẩm có tồn", stock.length], ["Đơn đang xử lý", orders.filter(x => x.status === "confirmed").length], ["SKU tồn thấp", low.length], ["Gợi ý chờ duyệt", recs.filter(x => x.status === "pending").length]].map(([label, value]) => <div key={String(label)} className={card}><p className="text-sm text-muted">{label}</p><strong className="mt-2 block text-3xl text-primary-dark">{value}</strong></div>)}</div>}
    {view === "inventory" && <div className={card}><p className="mb-3">{selectedStore?.name} · {stock.length} SKU</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">SKU</th><th className="p-2">Sản phẩm</th><th className="p-2">Tồn</th><th className="p-2">Giữ chỗ</th><th className="p-2">Khả dụng</th><th className="p-2">Cảnh báo</th></tr></thead><tbody>{stock.map(x => <tr key={x.product_id} className="border-t border-border"><td className="p-2">{x.sku}</td><td className="p-2">{x.name}</td><td className="p-2">{x.on_hand}</td><td className="p-2">{x.reserved}</td><td className="p-2">{x.available}</td><td className="p-2">{x.alerts.join(", ") || "—"}</td></tr>)}</tbody></table></div></div>}
    {view === "orders" && <div className="space-y-3">{orders.filter(x => x.store_id === storeId).map(order => <div key={order.id} className={card}><p className="font-semibold">Đơn {order.id.slice(0, 8)} · {order.status} · {money(order.total)}</p><p className="text-sm">{order.items.map(item => `${productName(item.product_id)} × ${item.quantity}`).join(", ")}</p><p className="text-sm">Giao cho: {order.recipient_name || "Chưa có"} · {order.delivery_phone || ""} · {order.delivery_address || ""}</p>{order.status === "confirmed" && <button disabled={busy} className={`mt-3 ${button}`} onClick={() => void action(`/api/v1/orders/${order.id}/fulfil`)}>Xuất kho / hoàn tất</button>}</div>)}{orders.length === 0 && <p>Chưa có đơn.</p>}</div>}
    {view === "forecasting" && <div className="space-y-4"><div className={card}><p>AI dùng lịch sử bán tổng hợp đến 09/11/2026; tồn kho lấy từ backend hiện tại. Kết quả chỉ là dự báo demo.</p><button disabled={busy || !storeId} className={`mt-3 ${button}`} onClick={() => void runForecast()}>Chạy dự báo 7 ngày</button>{job && <p className="mt-3">Job {job.job_id.slice(0, 8)} · {job.status} {job.as_of && `· dữ liệu đến ${job.as_of}`} {job.error_message}</p>}</div><div className={card}><h3 className="font-semibold">Dự báo đã lưu ({fcs.length} dòng)</h3><div className="mt-3 max-h-96 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th>Ngày</th><th>Sản phẩm</th><th>Nhu cầu dự báo</th><th>Model</th></tr></thead><tbody>{fcs.slice(-100).map(x => <tr key={x.id} className="border-t border-border"><td className="p-2">{x.target_date}</td><td className="p-2">{productName(x.product_id)}</td><td className="p-2">{x.predicted_qty}</td><td className="p-2">{x.model_version}</td></tr>)}</tbody></table></div></div></div>}
    {view === "recommendations" && <div className="space-y-3">{recs.map(rec => <div key={rec.id} className={card}><p className="font-semibold">{productName(rec.product_id)} · {rec.status}</p><p>Gợi ý nhập {rec.suggested_qty} · Safety stock {rec.safety_stock} · ROP {rec.reorder_point}</p><p className="mt-2 text-sm text-muted">{rec.reason}</p>{rec.status === "pending" && <div className="mt-3 flex gap-2"><button disabled={busy || !suppliers.length} className={button} onClick={() => void action(`/api/v1/recommendations/${rec.id}/approve`, { convert_to_po: true, supplier_id: suppliers.find(s => s.name === "SmartGrocery Demo Supplier")?.id || suppliers[0].id })}>Duyệt và tạo PO</button><button disabled={busy} className="rounded-lg border border-border px-3 py-2" onClick={() => void action(`/api/v1/recommendations/${rec.id}/reject`)}>Từ chối</button></div>}</div>)}{recs.length === 0 && <p>Chưa có gợi ý. Hãy chạy dự báo trước.</p>}</div>}
    {view === "suppliers" && <div className="space-y-3">{suppliers.map(x => <div key={x.id} className={card}><strong>{x.name}</strong><p>Lead time: {x.lead_time_days} ngày</p></div>)}<form className={card} onSubmit={async e => { e.preventDefault(); if (!supplierName.trim()) return; setBusy(true); try { await api("/api/v1/suppliers", { method: "POST", body: JSON.stringify({ name: supplierName }) }); setSupplierName(""); await load(); } catch (err) { setError((err as Error).message); } finally { setBusy(false); } }}><label>Thêm nhà cung cấp <input value={supplierName} onChange={e => setSupplierName(e.target.value)} className="ml-2 rounded-lg border border-border p-2" /></label><button disabled={busy} className={`ml-3 ${button}`}>Lưu</button></form></div>}
    {view === "procurement" && <div className="space-y-3">{pos.map(po => <div key={po.id} className={card}><p className="font-semibold">PO {po.id.slice(0, 8)} · {po.status}</p><div className="mt-3 flex flex-wrap gap-2">{po.status === "pending_approval" && <button disabled={busy} className={button} onClick={() => void action(`/api/v1/purchase-orders/${po.id}/approve`)}>Duyệt</button>}{po.status === "approved" && <button disabled={busy} className={button} onClick={() => void action(`/api/v1/purchase-orders/${po.id}/send`)}>Gửi nhà cung cấp</button>}{["sent", "partially_received"].includes(po.status) && <button disabled={busy} className={button} onClick={() => void receive(po.id)}>Nhận hàng</button>}</div></div>)}{pos.length === 0 && <p>Chưa có PO. Duyệt một gợi ý nhập hàng để tạo PO.</p>}</div>}
  </div>;
}
