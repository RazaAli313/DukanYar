/**
 * Backend API client — the FastAPI service.
 *
 * Every call carries the shopkeeper's Supabase access token; the backend
 * resolves their shop from it. Dashboard and khata reads go through the
 * backend (service_role) rather than querying Supabase directly, so they do
 * not depend on RLS / app_metadata.
 */

import { createClient } from "../../utils/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function token(): Promise<string> {
  const {
    data: { session },
  } = await createClient().auth.getSession();
  if (!session) throw new Error("Session khatam ho gaya. Dobara login karein.");
  return session.access_token;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${await token()}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error((await res.text().catch(() => "")) || `Error ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${await token()}`,
    },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((json as { detail?: string }).detail || `Error ${res.status}`);
  return json as T;
}

// ── types ────────────────────────────────────────────────────────────────────

export interface DashboardToday {
  date: string;
  totals: {
    sale: number;
    profit: number;
    udhaar_today: number;
    kharcha: number;
    outstanding_udhaar: number;
  };
  low_stock: { id: string; name: string; stock: number }[];
  recent: {
    kind: "sale" | "payment" | "expense";
    label: string;
    amount: number;
    tag: string;
    at: string;
  }[];
}

export interface Product {
  id: string;
  name: string;
  sale_price: number;
  cost_price: number;
  stock: number;
}

export interface SaleConfirmResult {
  ok: boolean;
  sale_id: string;
  card: {
    kind: string;
    status: string;
    title: string;
    lines: { label: string; value: string; flag?: boolean }[];
    total?: string;
    note?: string | null;
  };
  stock_alerts: { product_id: string; name: string; stock: number }[];
}

// ── endpoints ────────────────────────────────────────────────────────────────

export interface LedgerTxn {
  kind: "sale" | "udhaar" | "payment" | "expense";
  detail: string;
  qism: string;
  amount: number;
  direction: "in" | "out";
  at: string;
}

export interface Customer {
  id: string;
  khata_number: number;
  name: string;
  cnic: string;
  balance: number;
}

export const api = {
  dashboardToday: () => get<DashboardToday>("/dashboard/today"),
  products: (lowOnly = false) =>
    get<{ products: Product[] }>(`/dashboard/products${lowOnly ? "?low_only=true" : ""}`),
  ledger: (filter: "all" | "sale" | "udhaar" | "kharcha" = "all") =>
    get<{ transactions: LedgerTxn[] }>(`/khata/ledger?filter=${filter}`),
  customers: () => get<{ customers: Customer[] }>("/khata/customers"),
  confirmSale: (body: {
    items: { name: string; quantity: number }[];
    stated_total: number;
    payment?: "cash" | "udhaar";
    khata_number?: number | null;
  }) => post<SaleConfirmResult>("/conversations/sale/confirm", body),
  confirmExpense: (body: { amount: number; desc?: string | null }) =>
    post<SaleConfirmResult>("/conversations/expense/confirm", body),
  confirmUdhaar: (body: {
    amount: number;
    kind: "udhaar" | "payment";
    khata_number?: number | null;
    customer_name?: string | null;
    cnic?: string | null;
    new_customer?: boolean;
  }) => post<SaleConfirmResult>("/conversations/udhaar/confirm", body),
};
