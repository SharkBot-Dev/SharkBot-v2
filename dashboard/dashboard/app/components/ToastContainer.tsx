"use client";
import { useToast } from "./ToastProvider";

export default function ToastContainer() {
  const { toasts } = useToast();

  return (
    <div className="toast-root">
      {toasts.map((t: any) => (
        <div key={t.id} className="toast">
          <div className="toast-title">{t.title}</div>
          <div className="toast-message">{t.message}</div>
        </div>
      ))}
    </div>
  );
}
