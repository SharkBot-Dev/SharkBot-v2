"use client";

import { useState } from "react";

type Button = {
  label: string;
  customid?: string;
  url?: string;
};

type Modal = {
  customid: string;
  title: string;
};


export default function CreateSlashCommand({
  createCommand,
  buttons,
  modals,
}: {
  createCommand: (formData: FormData) => void;
  buttons: Button[];
  modals: Modal[];
}) {
  const [buttonSelectors, setSelectors] = useState<{ id: number }[]>([
    { id: 1 },
  ]);
  const [replyType, setReplyType] = useState<"text" | "modal">("text");

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

      <span className="font-semibold mb-1">返信タイプ</span>
      <select
        name="replytype"
        className="border p-2 w-full"
        required
        value={replyType}
        onChange={(e) =>
          setReplyType(e.target.value as "text" | "modal")
        }
      >
        <option value="text">テキスト返信</option>
        <option value="modal">モーダル送信</option>
      </select>

      <span className="font-semibold mb-1">送信するモーダル</span>
      <select
        name="opensModal"
        className="border p-2 w-full"
        required={replyType === "modal"}
        disabled={replyType === "text"}
      >
        <option value="">選択してください</option>
        {modals.map((m) => (
          <option key={m.customid} value={m.customid}>
            {m.title}（{m.customid}）
          </option>
        ))}
      </select>

      <span className="font-semibold mb-1">返信する内容</span>
      <textarea
        name="replytext"
        required={replyType === "text"}
        disabled={replyType === "modal"}
        className="border p-2 w-full disabled:bg-gray-100"
      />

      <span className="font-semibold mb-1">ボタン</span>
      {buttonSelectors.map((sel, index) => (
        <div key={sel.id} className="flex gap-3">
          <select
            name={`button${index + 1}`}
            className="border p-2 w-full"
            required={index === 0}
            disabled={replyType === "modal"}
          >
            <option value="none">選択しない</option>
            {buttons.map((b) => (
              <option
                key={b.customid ?? b.url}
                value={b.customid ?? b.url}
              >
                {b.label}
              </option>
            ))}
          </select>

          {buttonSelectors.length > 1 && (
            <button
              type="button"
              onClick={() => removeSelector(sel.id)}
              className="text-red-500"
            >
              削除
            </button>
          )}
        </div>
      ))}

      <button
        type="button"
        onClick={addSelector}
        disabled={buttonSelectors.length >= 5}
        className="bg-blue-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
      >
        ボタン追加
      </button>

      <br />

      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded-md"
      >
        登録
      </button>
    </form>
  );
}