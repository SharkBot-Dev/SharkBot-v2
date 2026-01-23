"use client";

export default function ItemBox({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-700 p-4 bg-gray-900/50 shadow-md">
      <h2 className="text-lg font-semibold mb-2">{title}</h2>
      <div className="text-sm text-gray-300">{children}</div>
    </div>
  );
}