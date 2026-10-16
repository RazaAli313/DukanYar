import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a rupee amount the way a shopkeeper reads it: ₨ 12,400 */
export function pkr(amount: number, opts?: { sign?: boolean }): string {
  const n = Math.round(amount);
  const body = Math.abs(n).toLocaleString("en-PK");
  const sign = opts?.sign && n > 0 ? "+" : n < 0 ? "−" : "";
  return `${sign}₨ ${body}`;
}
