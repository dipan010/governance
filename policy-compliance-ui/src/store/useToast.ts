import { useSyncExternalStore } from "react";

export interface Toast {
  id: number;
  tone: "success" | "error" | "info";
  message: string;
}

let toasts: Toast[] = [];
let nextId = 1;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function snapshot(): Toast[] {
  return toasts;
}

export function pushToast(tone: Toast["tone"], message: string): void {
  const toast: Toast = { id: nextId++, tone, message };
  toasts = [...toasts, toast];
  emit();
  setTimeout(() => dismissToast(toast.id), tone === "error" ? 7000 : 4000);
}

export function dismissToast(id: number): void {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

export function useToasts(): Toast[] {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
