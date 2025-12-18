"use client";

import { useState, useRef, useEffect, useCallback } from "react";

export default function Form({
  children,
  action,
  buttonlabel,
}: {
  children: React.ReactNode;
  action: any;
  buttonlabel: string;
}) {
  const [isDirty, setIsDirty] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const initialData = useRef<string>("");

  useEffect(() => {
    if (formRef.current) {
      const formData = new FormData(formRef.current);
      initialData.current = JSON.stringify(Object.fromEntries(formData));
    }
  }, []);

  const handleInput = useCallback(() => {
    if (formRef.current) {
      const currentData = new FormData(formRef.current);
      const currentDataJson = JSON.stringify(Object.fromEntries(currentData));
      
      setIsDirty(currentDataJson !== initialData.current);
    }
  }, []);

  return (
    <form
      ref={formRef}
      action={action}
      onInput={handleInput}
      onChange={handleInput}
      className="flex flex-col gap-3"
    >
      {children}

      {isDirty && (
        <div className="col-span-full flex justify-start mt-4 animate-in fade-in duration-200">
          <button
            type="submit"
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition"
          >
            {buttonlabel}
          </button>
        </div>
      )}
    </form>
  );
}