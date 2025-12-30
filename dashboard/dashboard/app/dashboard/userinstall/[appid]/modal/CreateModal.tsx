"use client";

import { useState } from "react";

type Props = {
  createCommand: (formData: FormData) => void;
};

export default function CreateModal({ createCommand }: Props) {
  const [inputSelectors, setSelectors] = useState<{ id: number }[]>([
    { id: 1 },
  ]);

  const addSelector = () => {
    if (inputSelectors.length >= 5) return;
    setSelectors([...inputSelectors, { id: Date.now() }]);
  };

  const removeSelector = (id: number) => {
    if (inputSelectors.length <= 1) return;
    setSelectors(inputSelectors.filter((sel) => sel.id !== id));
  };

  return (
    <form action={createCommand} className="space-y-4">
      <span className="font-semibold">タイトル</span>
      <input name="title" required className="border p-2 w-full" />

      <span className="font-semibold">モーダル custom_id</span>
      <input
        name="cid"
        required
        className="border p-2 w-full"
        placeholder="example_modal"
      />

      <span className="font-semibold">送信後の返信</span>
      <textarea
        name="replytext"
        required
        className="border p-2 w-full"
      />

      <span className="font-semibold">質問内容</span>

      {inputSelectors.map((sel, index) => (
        <div key={sel.id} className="border p-3 rounded space-y-2">
          <div>
            <label className="text-sm">
              質問 {index + 1} のラベル
            </label>
            <input
              name={`input${index + 1}`}
              required={index === 0}
              className="border p-2 w-full"
              placeholder={`質問${index + 1}`}
            />
          </div>

          <div>
            <label className="text-sm">
              質問 {index + 1} の custom_id
            </label>
            <input
              name={`customid${index + 1}`}
              required={index === 0}
              className="border p-2 w-full"
              placeholder={`field_${index + 1}`}
            />
          </div>

          {inputSelectors.length > 1 && (
            <button
              type="button"
              onClick={() => removeSelector(sel.id)}
              className="text-red-500 text-sm"
            >
              削除
            </button>
          )}
        </div>
      ))}

      <button
        type="button"
        onClick={addSelector}
        disabled={inputSelectors.length >= 5}
        className="bg-blue-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
      >
        質問追加
      </button><hr/>

      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded-md"
      >
        登録
      </button>
    </form>
  );
}