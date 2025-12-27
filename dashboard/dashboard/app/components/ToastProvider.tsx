"use client";
import { createContext, useContext, useState } from "react";

export type Toast = {
  id: number;
  title: string;
  message: string;
};

const ToastContext = createContext<any>(null);

export function useToast() {
  return useContext(ToastContext);
}

export default function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  function push(title: string, message: string, timeout = 4000) {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, title, message }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, timeout);
  }

  return (
    <ToastContext.Provider value={{ toasts, push }}>
      {children}
    </ToastContext.Provider>
  );
}