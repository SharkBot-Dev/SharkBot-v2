"use client";

export default function ItemRow({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
      {children}
    </div>
  );
}