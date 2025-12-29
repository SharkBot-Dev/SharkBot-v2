"use client";

import { useState } from "react";

export default function CreateSlashCommand({ createCommand, buttons }: any) {
  const [buttonSelectors, setSelectors] = useState([{ id: 1 }]);

  const addSelector = () => {
    if (buttonSelectors.length >= 5) return;
    setSelectors([...buttonSelectors, { id: Date.now() }]);
  };

  const removeSelector = (id: number) => {
    if (buttonSelectors.length <= 1) return;
    setSelectors(buttonSelectors.filter((sel) => sel.id !== id));
  };

  return (
    <form action={createCommand} className="space-y-4">
      <span className="font-semibold mb-1">コマンド名</span>
      <input name="name" required className="border p-2 w-full" />
      <span className="font-semibold mb-1">説明</span>
      <input name="description" required className="border p-2 w-full" />
      <span className="font-semibold mb-1">返信する内容</span>
      <textarea name="replytext" required className="border p-2 w-full" />

      <span className="font-semibold mb-1">ボタン</span>
      {buttonSelectors.map((sel, index) => (
        <div key={sel.id} className="flex gap-3">
          <select
            name={`button${index + 1}`}
            className="border p-2 w-full"
            required={index === 0}
          >
            <option value="none">選択しない</option>
            {buttons.map((b: any) => (
              <option key={b.customid ?? b.url} value={b.customid ?? b.url}>
                {b.label}
              </option>
            ))}
          </select>

          {buttonSelectors.length > 1 && (
            <button type="button" onClick={() => removeSelector(sel.id)}>
              削除
            </button>
          )}
        </div>
      ))}

      <button type="button" onClick={addSelector} disabled={buttonSelectors.length >= 5} className="bg-blue-600 text-white px-4 py-2 rounded-md">
        ボタン追加
      </button><br/>

      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md">登録</button>
    </form>
  );
}