"use client";

import { FormEvent, useState } from "react";

export default function ScraperAdminPage() {
  const [token, setToken] = useState("local-admin");
  const [form, setForm] = useState({ password: "", email: "", email_password: "", auth_token: "", ct0: "" });
  const [accounts, setAccounts] = useState<Array<{ username: string; active: boolean; logged_in: boolean; error_msg?: string }>>([]);
  const [message, setMessage] = useState("");

  async function refresh() {
    const response = await fetch("/api/admin/scraper/accounts", { headers: { "x-coordinx-admin-token": token } });
    const data = await response.json();
    if (!response.ok) return setMessage(data.error || "Gagal membaca status akun");
    setAccounts(data.accounts || []);
    setMessage("");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("Memproses login twscrape...");
    const response = await fetch("/api/admin/scraper/accounts", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-coordinx-admin-token": token },
      body: JSON.stringify(form),
    });
    const data = await response.json();
    setForm({ password: "", email: "", email_password: "", auth_token: "", ct0: "" });
    setMessage(response.ok && data.account?.active ? "Akun aktif dan siap digunakan." : data.account?.error_msg || data.error || data.detail || "Login gagal");
    await refresh();
  }

  return (
    <main className="mx-auto min-h-screen max-w-xl px-6 py-12">
      <h1 className="text-2xl font-bold text-[var(--foreground)]">Local Scraper Admin</h1>
      <p className="mt-2 text-sm text-[var(--muted-foreground)]">Kredensial hanya dikirim ke backend lokal dan tidak ditampilkan kembali.</p>
      <label className="mt-8 block text-sm font-semibold">Admin token<input type="password" value={token} onChange={(event) => setToken(event.target.value)} className="mt-2 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] p-3" /></label>
      <button type="button" onClick={() => void refresh()} disabled={!token} className="mt-4 rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-semibold disabled:opacity-50">Cek status akun</button>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-xl border border-[var(--border)] p-5">
        <p className="text-sm text-[var(--muted-foreground)]">Gunakan cookie session dari browser lokal. Username dan password X tidak diperlukan.</p>
        {(["auth_token", "ct0"] as const).map((field) => <label key={field} className="block text-sm font-semibold">{field}<input required type="password" value={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.value })} className="mt-2 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] p-3" /></label>)}
        <button type="submit" disabled={!token} className="w-full rounded-lg bg-[var(--primary)] p-3 font-semibold text-white disabled:opacity-50">Simpan session dan cek</button>
      </form>
      {message && <p className="mt-4 text-sm text-[var(--muted-foreground)]">{message}</p>}
      <section className="mt-8 space-y-3"><h2 className="font-bold">Status akun</h2>{accounts.map((account) => <div key={account.username} className="rounded-lg border border-[var(--border)] p-4 text-sm"><strong>{account.username}</strong><div>Active: {String(account.active)} · Logged in: {String(account.logged_in)}</div>{account.error_msg && <div className="text-red-600">{account.error_msg}</div>}</div>)}</section>
    </main>
  );
}
