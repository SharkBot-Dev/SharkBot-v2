"use client";

import { useState, useMemo } from "react";
import ToggleButton from "@/app/components/ToggleButton";

type Command = {
    name: string;
    description: string;
    category: string;
};

export default function CommandList({
    commands,
    disabledCommands,
}: {
    commands: Command[];
    disabledCommands: string[];
}) {
    const [query, setQuery] = useState("");
    const [disabled, setDisabled] = useState<string[]>(disabledCommands);

    const filtered = useMemo(() => {
        const q = query.toLowerCase();
        return commands.filter(
            (cmd) =>
                cmd.name.toLowerCase().includes(q) ||
                cmd.description.toLowerCase().includes(q)
        );
    }, [query, commands]);

    const grouped = useMemo(() => {
        return filtered.reduce((acc: any, cmd) => {
            if (!acc[cmd.category]) acc[cmd.category] = [];
            acc[cmd.category].push(cmd);
            return acc;
        }, {});
    }, [filtered]);

    function disableCategory(is_disable: boolean, category: string, cmds: Command[]) {
        const names = cmds.map(c => c.name);

        if (is_disable) {
            setDisabled(prev => {
                const set = new Set(prev);
                names.forEach(n => set.add(n));
                return Array.from(set);
            });
        } else {
            setDisabled(prev => {
                const set = new Set(prev);
                names.forEach(n => set.delete(n));
                return Array.from(set);
            });
        }
    }

    return (
        <>
            <input
                type="text"
                placeholder="コマンド名・説明で検索"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="mb-6 w-full rounded bg-gray-800 text-white px-4 py-2 outline-none border border-gray-700 focus:border-blue-500"
            />

            <div className="mb-8">
                <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-1">
                    グローバル設定
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    
                    <div className="flex flex-col justify-between bg-gray-900 p-5 rounded-xl border border-gray-700 shadow-sm">
                        <div>
                            <h3 className="text-lg font-semibold text-white">
                                グローバルな無効化
                            </h3>
                            <p className="text-sm text-gray-400 mt-2 leading-relaxed">
                                ボタンひとつですべてのコマンドを一括で有効化、または無効化できます。
                            </p>
                        </div>

                        <div className="flex items-center justify-end gap-3 mt-6">
                            <button
                                type="button"
                                onClick={() => disableCategory(true, "", commands)}
                                className="px-4 py-2 text-sm font-medium bg-red-600/90 text-white rounded-md hover:bg-red-500 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                            >
                            すべて無効
                            </button>
                            <button
                                type="button"
                                onClick={() => disableCategory(false, "", commands)}
                                className="px-4 py-2 text-sm font-medium bg-green-600/90 text-white rounded-md hover:bg-green-500 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                            >
                            すべて有効
                            </button>
                        </div>
                    </div>

                </div>
            </div>

            {(Object.entries(grouped) as [string, Command[]][]).map(
                ([category, cmds]) => (
                    <div key={category} className="mb-8">
                        <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-1">
                            {category}

                            <button
                                type="button"
                                className="ml-4 bg-red-500 text-white rounded hover:bg-red-600 transition"
                                onClick={() => disableCategory(true, category, cmds)}
                            >
                                無効化
                            </button>
                            <button
                                type="button"
                                className="ml-4 bg-green-500 text-white rounded hover:bg-green-600 transition"
                                onClick={() => disableCategory(false, category, cmds)}
                            >
                                有効化
                            </button>

                        </h2>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {cmds.map((cmd) => (
                                <div
                                    key={cmd.name}
                                    className="flex flex-col justify-between bg-gray-900 p-4 rounded-lg border border-gray-700"
                                >
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">
                                            {cmd.name}
                                        </h3>
                                        <p className="text-sm text-gray-400 mt-1">
                                            {cmd.description}
                                        </p>
                                    </div>

                                    <div className="flex justify-end mt-3">
                                        <ToggleButton
                                            name={cmd.name}
                                            value={!disabled.includes(cmd.name)}
                                            defaultValue={!disabled.includes(cmd.name)}
                                            onChange={(v) => {
                                                setDisabled(prev =>
                                                    v
                                                        ? prev.filter(n => n !== cmd.name)
                                                        : [...prev, cmd.name]
                                                );
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            )}
        </>
    );
}