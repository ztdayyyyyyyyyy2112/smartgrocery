"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, saveSession, type Session } from "../../../lib/demo";
export default function LoginPage() {
  const router = useRouter();
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("customer@smartgrocery.example.com");
  const [password, setPassword] = useState("DemoPass123!");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await api<Session>(`/api/v1/auth/${register ? "register" : "login"}`, { method: "POST", body: JSON.stringify(register ? { email, password, full_name: name } : { email, password }) });
      saveSession(result);
      router.push(result.user.role === "customer" ? "/products" : "/dashboard");
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  return <section className="sg-container py-16"><div className="mx-auto max-w-lg rounded-2xl border border-border bg-white p-8 shadow-sm">
    <h1 className="text-3xl font-bold">{register ? "Tạo tài khoản" : "Đăng nhập"}</h1>
    <p className="mt-3 text-sm text-muted">Demo: customer@smartgrocery.example.com hoặc merchant@smartgrocery.example.com · mật khẩu DemoPass123!</p>
    <form onSubmit={submit} className="mt-7 space-y-4">
      {register && <label className="block">Họ tên<input required value={name} onChange={e => setName(e.target.value)} className="mt-1 w-full rounded-xl border border-border p-3" /></label>}
      <label className="block">Email<input type="email" required value={email} onChange={e => setEmail(e.target.value)} className="mt-1 w-full rounded-xl border border-border p-3" /></label>
      <label className="block">Mật khẩu<input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="mt-1 w-full rounded-xl border border-border p-3" /></label>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      <button disabled={busy} className="w-full rounded-xl bg-primary px-4 py-3 font-semibold text-white disabled:opacity-50">{busy ? "Đang xử lý…" : register ? "Đăng ký" : "Đăng nhập"}</button>
    </form>
    <button type="button" onClick={() => { setRegister(!register); setError(""); }} className="mt-4 text-primary underline">{register ? "Đã có tài khoản? Đăng nhập" : "Tạo tài khoản khách hàng"}</button>
  </div></section>;
}
