"use client";

interface LineAndTextLayout {
  text: string
}

export default function LineAndTextLayout({
  text
}: LineAndTextLayout) {
  return (
    <div className="flex items-center my-8">
      <div className="flex-grow h-px bg-gray-300" />
      <span className="px-4 text-gray-500">{text}</span>
      <div className="flex-grow h-px bg-gray-300" />
    </div>
  );
}