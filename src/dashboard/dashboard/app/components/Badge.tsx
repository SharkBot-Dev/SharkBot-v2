"use client";

interface BadgeProps {
  text: string; // バッジに表示する文字
  color?: string; // 色（任意）
}

export default function Badge({ text, color }: BadgeProps) {
  return (
    <span
      className={`inline-block text-xs font-semibold px-2 py-1 rounded-full ${color ?? "bg-blue-600"} text-white`}
    >
      {text}
    </span>
  );
}