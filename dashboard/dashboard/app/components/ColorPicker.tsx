// components/FormColorPalette.tsx
"use client";

import { useState } from "react";

interface FormColorPaletteProps {
  name: string;
  colors?: string[];
  defaultValue?: string;
  onChange?: (color: string) => void;
}

export default function ColorPalette({
  name,
  colors = ["#E74C3C", "#57f287", "#2b2b9c", "#ecec1f", "#df23df", "#23dfdf", "#292929", "#FFFFFF"],
  defaultValue,
  onChange
}: FormColorPaletteProps) {
  const [selected, setSelected] = useState(defaultValue || colors[0]);

  const handleSelect = (color: string) => {
    setSelected(color);
    if (onChange) onChange(color);
  };

  const handleCustomColor = (e: React.ChangeEvent<HTMLInputElement>) => {
    const color = e.target.value;
    setSelected(color);
    if (onChange) onChange(color);
  };

  return (
    <div className="flex items-center gap-3">

      {/* hidden input */}
      <input type="hidden" name={name} value={selected} />

      {/* パレットボタン */}
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

      {/* 自由色選択 */}
      <label className="relative w-8 h-8 cursor-pointer">
        <input
          type="color"
          value={selected}
          onChange={handleCustomColor}
          className="w-full h-full p-0 border-2 rounded-full cursor-pointer appearance-none"
          style={{ borderColor: selected === selected ? "black" : "transparent" }}
        />
      </label>

      {/* 選択中の色コード */}
      <span>{selected}</span>
    </div>
  );
}