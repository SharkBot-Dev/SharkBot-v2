"use client";
import { useState } from "react";

export default function ToggleButton({
  name,
  defaultValue = false,
}: {
  name: string;
  defaultValue?: boolean;
}) {
  const [isOn, setIsOn] = useState(defaultValue);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOn(!isOn)}
        className={`relative inline-flex items-center h-6 w-12 rounded-full transition-colors duration-300 ${
          isOn ? "bg-green-500" : "bg-gray-400"
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-300 ${
            isOn ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
      <input type="hidden" name={name} value={String(isOn)} />
    </>
  );
}