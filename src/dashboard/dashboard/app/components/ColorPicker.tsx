"use client";

import { useState, useRef } from "react";

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
  const hiddenInputRef = useRef<HTMLInputElement>(null);

  const notifyChange = (color: string) => {
    setSelected(color);
    if (onChange) onChange(color);

    if (hiddenInputRef.current) {
      hiddenInputRef.current.value = color;
      hiddenInputRef.current.dispatchEvent(new Event("input", { bubbles: true }));
    }
  };

  const handleSelect = (color: string) => {
    notifyChange(color);
  };

  const handleCustomColor = (e: React.ChangeEvent<HTMLInputElement>) => {
    notifyChange(e.target.value);
  };

  return (
    <div className="flex items-center gap-3">
      <input 
        ref={hiddenInputRef} 
        type="hidden" 
        name={name} 
        value={selected} 
      />

      {colors.map((color) => (
        <button
          key={color}
          type="button"
          onClick={() => handleSelect(color)}
          style={{ backgroundColor: color }}
          className={`w-8 h-8 rounded-full border-2 ${
            selected.toLowerCase() === color.toLowerCase() ? "border-black shadow-md" : "border-transparent"
          }`}
        />
      ))}

      <label className="relative w-8 h-8 cursor-pointer">
        <input
          type="color"
          value={selected}
          onChange={handleCustomColor}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div 
          style={{ backgroundColor: selected }}
          className="w-full h-full rounded-full border-2 border-gray-300 flex items-center justify-center text-xs"
        >
          ＋
        </div>
      </label>

      <span className="font-mono text-sm">{selected.toUpperCase()}</span>
    </div>
  );
}