// components/FormColorPalette.tsx
"use client";

import { useState } from "react";

interface FormColorPaletteProps {
  name: string;
  colors?: string[];
  defaultValue?: string;
}

export default function ColorPalette({
  name,
  colors = ["#E74C3C", "#57f287", "#2b2b9c", "#ecec1f", "#df23df", "#23dfdf", "#292929", "#FFFFFF"],
  defaultValue,
}: FormColorPaletteProps) {
  const [selected, setSelected] = useState(defaultValue || colors[0]);

  const handleSelect = (color: string) => {
    setSelected(color);
  };

  return (
    <div className="flex items-center gap-2">
      {/* 選択した色をフォームで送信可能に */}
      <input type="hidden" name={name} value={selected} />

      {colors.map((color) => (
        <button
          key={color}
          type="button"
          onClick={() => handleSelect(color)}
          style={{ backgroundColor: color }}
          className={`w-8 h-8 rounded-full border-2 ${
            selected === color ? "border-black" : "border-transparent"
          }`}
        />
      ))}

      <span>{selected}</span>
    </div>
  );
}