"use client";
import { useState, useEffect, useRef } from "react";

export default function ToggleButton({
  name,
  value,
  defaultValue = false,
  onChange,
}: {
  name: string;
  value?: boolean;
  defaultValue?: boolean;
  onChange?: (v: boolean) => void;
}) {
  const [isOn, setIsOn] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (typeof value === "boolean") {
      setIsOn(value);

      if (inputRef.current) {
        inputRef.current.value = String(value);
        inputRef.current.dispatchEvent(
          new Event("input", { bubbles: true })
        );
      }
    }
  }, [value]);

  const toggle = () => {
    const nextValue = !isOn;
    setIsOn(nextValue);

    if (inputRef.current) {
      inputRef.current.value = String(nextValue);
      inputRef.current.dispatchEvent(
        new Event("input", { bubbles: true })
      );
    }

    onChange?.(nextValue);
  };

  return (
    <>
      <button
        type="button"
        onClick={toggle}
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

      <input
        ref={inputRef}
        type="hidden"
        name={name}
        value={String(isOn)}
      />
    </>
  );
}