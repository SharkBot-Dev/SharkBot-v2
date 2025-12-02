"use client";

import { useState } from "react";

export default function RoleSelectorList({ roles }: { roles: any[] }) {
  const [selectors, setSelectors] = useState([{ id: 1 }]);

  const addSelector = () => {
    if (selectors.length >= 10) return;
    setSelectors([...selectors, { id: Date.now() }]);
  };

  const removeSelector = (id: number) => {
    if (selectors.length <= 1) return;
    setSelectors(selectors.filter((sel) => sel.id !== id));
  };

  return (
    <div className="flex flex-col gap-3">
      {selectors.map((sel, index) => (
        <div
          key={sel.id}
          className="flex items-center gap-3 bg-gray-800 p-3 rounded border border-gray-700"
        >
          <div className="flex-1">
            <label className="text-sm block mb-1">ロール {index + 1}</label>

            <select
              name={`role${index + 1}`}
              className="border p-2 rounded bg-gray-900 text-white w-full"
              required={index === 0}
            >
              <option value="">選択しない</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          {selectors.length > 1 && (
            <button
              type="button"
              onClick={() => removeSelector(sel.id)}
              className="p-2 bg-red-600 hover:bg-red-700 rounded text-white"
            >
              削除
            </button>
          )}
        </div>
      ))}

      <button
        type="button"
        onClick={addSelector}
        disabled={selectors.length >= 10}
        className="p-2 bg-blue-600 hover:bg-blue-700 rounded mt-2 disabled:bg-gray-600 text-white"
      >
        ロールを追加（最大10）
      </button>
    </div>
  );
}