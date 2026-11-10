export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type User = { id: string; email: string; full_name: string; role: "customer" | "merchant" | "admin" };
export type Session = { access_token: string; refresh_token: string; user: User };
export type Product = { id: string; sku: string; name: string; unit: string; selling_price: string; available_qty: string; image_url: string | null; description: string | null };
export type Store = { id: string; code: string; name: string };
export type CartItem = { product: Product; quantity: number };
export type Order = { id: string; store_id: string; status: string; total: string; items: { product_id: string; quantity: string; unit_price: string }[] };
export type Inventory = { store_id: string; product_id: string; sku: string; name: string; on_hand: string; reserved: string; available: string; alerts: string[] };
export type Recommendation = { id: string; store_id: string; product_id: string; suggested_qty: string; safety_stock: string; reorder_point: string; reason: string; status: string };
export type Forecast = { id: string; store_id: string; product_id: string; target_date: string; predicted_qty: string; model_name: string; model_version: string };
export type Supplier = { id: string; name: string; lead_time_days: number };
export type PurchaseOrder = { id: string; store_id: string; supplier_id: string; status: string; items?: { product_id: string; quantity_ordered: string; quantity_received: string; unit_cost: string }[] };

const SESSION_KEY = "smartgrocery.demo.session";
const CART_KEY = "smartgrocery.demo.cart";

export function session(): Session | null {
  if (typeof window === "undefined") return null;
  try { return JSON.parse(localStorage.getItem(SESSION_KEY) || "null"); } catch { return null; }
}
export function saveSession(value: Session) { localStorage.setItem(SESSION_KEY, JSON.stringify(value)); }
export function logout() { localStorage.removeItem(SESSION_KEY); }
export function cart(): CartItem[] {
  if (typeof window === "undefined") return [];
  try { return JSON.parse(localStorage.getItem(CART_KEY) || "[]"); } catch { return []; }
}
export function saveCart(items: CartItem[]) { localStorage.setItem(CART_KEY, JSON.stringify(items)); window.dispatchEvent(new Event("smartgrocery:cart")); }
export function addToCart(product: Product) {
  const items = cart();
  const existing = items.find(item => item.product.id === product.id);
  if (existing) existing.quantity = Math.min(existing.quantity + 1, Number(product.available_qty));
  else items.push({ product, quantity: 1 });
  saveCart(items);
}
export function money(value: string | number) { return `${Number(value).toLocaleString("vi-VN")}₫`; }

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const current = session();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (current?.access_token) headers.set("Authorization", `Bearer ${current.access_token}`);
  let response: Response;
  try { response = await fetch(`${API_URL}${path}`, { ...options, headers, cache: "no-store" }); }
  catch { throw new Error("Không kết nối được API. Kiểm tra dịch vụ ở cổng 8000."); }
  if (response.status === 401 && retry && current?.refresh_token && path !== "/api/v1/auth/refresh") {
    const refreshed = await fetch(`${API_URL}/api/v1/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: current.refresh_token }) });
    if (refreshed.ok) { saveSession(await refreshed.json()); return api<T>(path, options, false); }
    logout();
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `API trả lỗi ${response.status}`);
  return body as T;
}

export function wsUrl() {
  const token = session()?.access_token;
  return token ? `${API_URL.replace(/^http/, "ws")}/ws/events?access_token=${encodeURIComponent(token)}` : null;
}
