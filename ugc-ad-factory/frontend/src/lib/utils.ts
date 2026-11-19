import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtCredits(n?: number | null) {
  if (n === null || n === undefined) return "–";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
}

export function fmtDate(iso?: string | null) {
  if (!iso) return "–";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function fmtDuration(s?: number | null) {
  if (!s && s !== 0) return "–";
  return `${s.toFixed(1)}s`;
}
