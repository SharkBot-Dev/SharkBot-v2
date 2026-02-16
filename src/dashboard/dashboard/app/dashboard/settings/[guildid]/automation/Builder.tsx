"use client";

import Form from "@/app/components/Form";
import { useState } from "react";

interface BuilderProps {
  guild: any;
  channels: any[];
  sendData: (formData: FormData) => void;
}

export default function AutoMationBuilder({ guild, channels, sendData }: BuilderProps) {
  const [conditions, setConditions] = useState([{ id: Date.now(), type: "if_included" }]);
  const [actions, setActions] = useState([{ id: Date.now(), type: "sendmsg" }]);

  const addCondition = () => {
    if (conditions.length >= 5) return;
    setConditions([...conditions, { id: Date.now(), type: "if_included" }]);
  };

  const addAction = () => {
    if (actions.length >= 5) return;
    setActions([...actions, { id: Date.now(), type: "sendmsg" }]);
  };

  const updateItem = (setter: any, items: any[], id: number, field: string, value: string) => {
    setter(items.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  return (
    <div className="flex flex-col gap-3">
      <Form action={sendData} buttonlabel="オートメーションを作成">
        
        <Section title="1. トリガー" color="text-blue-400">
          <select name="trigger" className="border p-2 rounded bg-gray-800 text-white" required>
            <option value="on_message">メッセージが送信された時</option>
          </select>
        </Section>

        <Section title="2. 条件（すべて満たした場合）" color="text-green-400">
          {conditions.map((cond, index) => (
            <div key={cond.id} className="card-style">
              <div className="flex gap-2 mb-2">
                <select
                  name={`condition_type_${index}`}
                  className="border p-2 rounded bg-gray-800 text-white"
                  value={cond.type}
                  onChange={(e) => updateItem(setConditions, conditions, cond.id, "type", e.target.value)}
                >
                  <option value="if_included">本文にキーワードを含む</option>
                  <option value="if_equal">本文が完全に一致する</option>
                  <option value="is_channel">特定のチャンネル内</option>
                </select>
                {conditions.length > 1 && (
                  <button type="button" onClick={() => setConditions(conditions.filter(c => c.id !== cond.id))} className="px-3 bg-red-600 rounded text-sm">削除</button>
                )}
              </div>

              {cond.type === "is_channel" ? (
                <select name={`condition_value_${index}`} className="border p-2 rounded bg-gray-800 text-white" required>
                  {channels?.map(ch => (
                    <option key={ch.id} value={ch.id}>#{ch.name}</option>
                  ))}
                </select>
              ) : (
                <input 
                  name={`condition_value_${index}`}
                  placeholder="キーワードを入力..."
                  className="border p-2 rounded bg-gray-800 text-white"
                  required
                />
              )}
            </div>
          ))}
          <div className="card-style">
            <button 
              type="button" 
              onClick={addCondition} 
              disabled={conditions.length >= 5}
              className="border p-2 rounded bg-gray-800 text-white"
            >
              {conditions.length >= 5 ? "条件は最大5個までです" : "+ 条件を追加"}
            </button>
          </div>
        </Section>

        <Section title="3. 実行するアクション" color="text-yellow-400">
          {actions.map((act, index) => (
            <div key={act.id} className="card-style">
              <div className="flex gap-2 mb-2">
                <select
                  name={`action_type_${index}`}
                  className="border p-2 rounded bg-gray-800 text-white"
                  value={act.type}
                  onChange={(e) => updateItem(setActions, actions, act.id, "type", e.target.value)}
                >
                  <option value="sendmsg">メッセージを送信</option>
                  <option value="reply">メッセージに返信</option>
                  <option value="delmsg">メッセージを削除</option>
                  <option value="add_reaction">リアクションを追加</option>
                </select>
                {actions.length > 1 && (
                  <button type="button" onClick={() => setActions(actions.filter(a => a.id !== act.id))} className="px-3 bg-red-600 rounded text-sm">削除</button>
                )}
              </div>

              {act.type !== "delmsg" ? (act.type === "add_reaction" ? (
                <input 
                  name={`action_value_${index}`}
                  placeholder="絵文字 (例: ✅)"
                  className="border p-2 rounded bg-gray-800 text-white"
                  required
                />
              ) : (
                <textarea 
                  name={`action_value_${index}`}
                  placeholder={"送信するメッセージを入力..."}
                  className="border p-2 rounded bg-gray-800 text-white"
                  required
                />
              )):
                <input 
                  name={`action_value_${index}`}
                  placeholder="ここは見えない"
                  className="border p-2 rounded bg-gray-800 text-white"
                  defaultValue="delmsg"
                  hidden
                />
              }
            </div>
          ))}
          <div className="card-style">
            <button 
              type="button" 
              onClick={addAction} 
              disabled={actions.length >= 5}
              className="border p-2 rounded bg-gray-800 text-white"
            >
              {actions.length >= 5 ? "行動は最大5個までです" : "+ 行動を追加"}
            </button>
          </div>
        </Section>

      </Form>
    </div>
  );
}

function Section({ title, color, children }: { title: string, color: string, children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <label className={`text-sm font-bold block mb-2 ${color}`}>{title}</label>
      <div className="flex flex-col gap-3">{children}</div>
    </div>
  );
}