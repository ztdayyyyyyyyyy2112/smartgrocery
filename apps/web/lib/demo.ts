export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type User = { id: string; email: string; full_name: string; role: "customer" | "merchant" | "admin"; store_id: string | null; phone: string | null; default_address: string | null };
export type Session = { user: User; access_token?: string; refresh_token?: string };
export type Product = { id: string; sku: string; name: string; unit: string; selling_price: string; available_qty: string; image_url: string | null; description: string | null };
export type Store = { id: string; code: string; name: string };
export type CartItem = { product: Product; quantity: number };
export type Order = { id: string; store_id: string; status: string; total: string; recipient_name: string; delivery_phone: string; delivery_address: string; items: { product_id: string; quantity: string; unit_price: string }[] };
export type Inventory = { store_id: string; product_id: string; sku: string; name: string; on_hand: string; reserved: string; available: string; alerts: string[] };
export type Recommendation = { id: string; store_id: string; product_id: string; suggested_qty: string; safety_stock: string; reorder_point: string; reason: string; status: string };
export type Forecast = { id: string; store_id: string; product_id: string; target_date: string; predicted_qty: string; model_name: string; model_version: string };
export type Supplier = { id: string; name: string; lead_time_days: number };
export type PurchaseOrder = { id: string; store_id: string; supplier_id: string; status: string; items?: { product_id: string; quantity_ordered: string; quantity_received: string; unit_cost: string }[] };

const SESSION_KEY = "smartgrocery.demo.session";
const STORE_KEY = "smartgrocery.demo.store";
let cartCache: CartItem[] = [];
let cartAccountId: string | null = null;

export function session(): Session | null {
  if (typeof window === "undefined") return null;
  try { return JSON.parse(localStorage.getItem(SESSION_KEY) || "null"); } catch { return null; }
}
export function saveSession(value: Session) { if (session()?.user.id !== value.user.id) { cartCache = []; cartAccountId = null; window.dispatchEvent(new Event("smartgrocery:cart")); } localStorage.setItem(SESSION_KEY, JSON.stringify({ user: { ...value.user, phone: null, default_address: null } })); window.dispatchEvent(new Event("smartgrocery:session")); }
export async function logout() { try { await fetch(`${API_URL}/api/v1/auth/logout`, { method: "POST", credentials: "include" }); } catch { /* Clear this browser's account display even when offline. */ } finally { localStorage.removeItem(SESSION_KEY); localStorage.removeItem("smartgrocery.demo.cart"); cartCache = []; cartAccountId = null; window.dispatchEvent(new Event("smartgrocery:cart")); window.dispatchEvent(new Event("smartgrocery:session")); } }
export function selectedStore() { return typeof window === "undefined" ? "" : localStorage.getItem(STORE_KEY) || ""; }
export async function saveSelectedStore(id: string) {
  if (session()?.user.role === "customer") {
    await api("/api/v1/cart", { method: "PUT", body: JSON.stringify({ store_id: id, items: [] }) });
    cartCache = [];
    cartAccountId = session()?.user.id || null;
    window.dispatchEvent(new Event("smartgrocery:cart"));
  }
  localStorage.setItem(STORE_KEY, id);
  window.dispatchEvent(new Event("smartgrocery:store"));
}
export function cart(): CartItem[] {
  const account = session()?.user;
  return account?.role === "customer" && account.id === cartAccountId ? cartCache : [];
}
export async function loadCart() {
  if (session()?.user.role !== "customer") { cartCache = []; cartAccountId = null; window.dispatchEvent(new Event("smartgrocery:cart")); return []; }
  const accountId = session()?.user.id;
  const result = await api<{ store_id: string | null; items: CartItem[] }>("/api/v1/cart");
  if (session()?.user.id !== accountId) return cart();
  cartCache = result.items;
  cartAccountId = accountId || null;
  if (result.store_id) localStorage.setItem(STORE_KEY, result.store_id);
  window.dispatchEvent(new Event("smartgrocery:cart"));
  return cartCache;
}
export async function saveCart(items: CartItem[]) {
  if (session()?.user.role !== "customer") throw new Error("Đăng nhập bằng tài khoản khách hàng để dùng giỏ hàng.");
  const accountId = session()?.user.id;
  const storeId = selectedStore();
  if (!storeId) throw new Error("Hãy chọn cửa hàng trước.");
  const result = await api<{ items: CartItem[] }>("/api/v1/cart", { method: "PUT", body: JSON.stringify({ store_id: storeId, items: items.map(item => ({ product_id: item.product.id, quantity: item.quantity })) }) });
  if (session()?.user.id !== accountId) return cart();
  cartCache = result.items;
  cartAccountId = accountId || null;
  window.dispatchEvent(new Event("smartgrocery:cart"));
  return cartCache;
}
export async function addToCart(product: Product) {
  const items = cart().map(item => ({ ...item }));
  const existing = items.find(item => item.product.id === product.id);
  if (existing) existing.quantity = Math.min(existing.quantity + 1, Number(product.available_qty));
  else items.push({ product, quantity: 1 });
  return saveCart(items);
}
export function money(value: string | number) { return `${Number(value).toLocaleString("vi-VN")}₫`; }

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const current = session();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (["/api/v1/auth/login", "/api/v1/auth/register"].includes(path)) headers.set("X-SG-Browser-Session", "1");
  let response: Response;
  try { response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include", cache: "no-store" }); }
  catch { throw new Error("Không kết nối được API. Kiểm tra dịch vụ ở cổng 8000."); }
  if (response.status === 401 && retry && current && !path.startsWith("/api/v1/auth/")) {
    const refreshed = await fetch(`${API_URL}/api/v1/auth/refresh`, { method: "POST", headers: { "X-SG-Browser-Session": "1" }, credentials: "include" });
    if (refreshed.ok) { saveSession(await refreshed.json()); return api<T>(path, options, false); }
    void logout();
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `API trả lỗi ${response.status}`);
  return body as T;
}

export function wsUrl() {
  return session() ? `${API_URL.replace(/^http/, "ws")}/ws/events` : null;
}
