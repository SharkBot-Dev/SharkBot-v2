"use client";

import { useState, useMemo, useRef } from "react";
import ToggleButton from "@/app/components/ToggleButton";

type Command = {
    name: string;
    description: string;
    category: string;
};

type Role = {
    id: string;
    name: string;
};

export default function CommandList({
    commands,
    disabledCommands,
    initialRoleRestrictions = {},
    roles
}: {
    commands: Command[];
    disabledCommands: string[];
    initialRoleRestrictions?: Record<string, string>;
    roles: Role[];
}) {
    const [query, setQuery] = useState("");
    const [disabled, setDisabled] = useState<string[]>(disabledCommands);

    const [roleRestrictions, setRoleRestrictions] = useState<Record<string, string>>(initialRoleRestrictions);

    const [editingCommand, setEditingCommand] = useState<Command | null>(null);
    const dialogRef = useRef<HTMLDialogElement>(null);

    const openModal = (cmd: Command) => {
        setEditingCommand(cmd);
        dialogRef.current?.showModal();
    };

    const closeModal = () => {
        dialogRef.current?.close();
        setEditingCommand(null);
    };

    const filtered = useMemo(() => {
        const q = query.toLowerCase();
        return commands.filter(
            (cmd) =>
                cmd.name.toLowerCase().includes(q) ||
                cmd.description.toLowerCase().includes(q)
        );
    }, [query, commands]);

    const grouped = useMemo(() => {
        return filtered.reduce((acc: Record<string, Command[]>, cmd) => {
            if (!acc[cmd.category]) acc[cmd.category] = [];
            acc[cmd.category].push(cmd);
            return acc;
        }, {});
    }, [filtered]);

    const disableCategory = (is_disable: boolean, category: string, cmds: Command[]) => {
        const names = cmds.map(c => c.name);
        setDisabled(prev => {
            const set = new Set(prev);
            if (is_disable) {
                names.forEach(n => set.add(n));
            } else {
                names.forEach(n => set.delete(n));
            }
            return Array.from(set);
        });
    };

    const isCategoryEnabled = (categoryCmds: Command[]) => {
        return categoryCmds.some(cmd => !disabled.includes(cmd.name));
    };

    return (
        <>
            <input type="hidden" name="disabledCommands" value={JSON.stringify(disabled)} />
            <input type="hidden" name="roleRestrictions" value={JSON.stringify(roleRestrictions)} />

            <input
                type="text"
                placeholder="コマンド名・説明で検索..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="mb-6 w-full rounded-lg bg-gray-800 text-white px-4 py-3 outline-none border border-gray-700 focus:border-blue-500 transition-all"
            />

            <div className="mb-8">
                <h2 className="text-xl font-bold text-white mb-4 border-l-4 border-blue-500 pl-3">
                    一括設定
                </h2>
                <div className="bg-gray-900 p-5 rounded-xl border border-gray-700 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-4">
                    <div>
                        <h3 className="text-lg font-semibold text-white">すべて切り替え</h3>
                        <p className="text-sm text-gray-400 mt-1">
                            全コマンドを一度に有効化・無効化します。
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={() => disableCategory(true, "", commands)}
                            className="px-4 py-2 text-sm font-medium bg-red-600/20 text-red-400 border border-red-600/30 rounded-md hover:bg-red-600 hover:text-white transition-all"
                        >
                            すべて無効
                        </button>
                        <button
                            type="button"
                            onClick={() => disableCategory(false, "", commands)}
                            className="px-4 py-2 text-sm font-medium bg-green-600/20 text-green-400 border border-green-600/30 rounded-md hover:bg-green-600 hover:text-white transition-all"
                        >
                            すべて有効
                        </button>
                    </div>
                </div>
            </div>

            {(Object.entries(grouped) as [string, Command[]][]).map(([category, cmds]) => {
                const categoryEnabled = isCategoryEnabled(cmds);

                return (
                    <div key={category} className="mb-10">
                        <div className="flex items-center justify-between mb-4 border-b border-gray-800 pb-2">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                {category}
                                <span className="text-xs font-normal text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
                                    {cmds.length}
                                </span>
                            </h2>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500 uppercase tracking-wider">Category Toggle</span>
                                <ToggleButton
                                    name={`category-${category}`}
                                    value={categoryEnabled}
                                    onChange={(v) => disableCategory(!v, category, cmds)}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {cmds.map((cmd) => (
                                <div
                                    key={cmd.name}
                                    className={`flex flex-row items-center justify-between bg-gray-900 p-4 rounded-xl border transition-colors ${
                                        disabled.includes(cmd.name) ? "border-gray-800 opacity-60" : "border-gray-700"
                                    }`}
                                >
                                    <div className="flex-1 pr-4">
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-md font-bold text-white">/{cmd.name}</h3>
                                            {roleRestrictions[cmd.name] && (
                                                <span className="text-[10px] bg-blue-900/50 text-blue-300 px-1.5 py-0.5 rounded border border-blue-700/50">
                                                    限定
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                                            {cmd.description}
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <button
                                            type="button"
                                            onClick={() => openModal(cmd)}
                                            className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                                            title="権限設定"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                            </svg>
                                        </button>
                                        <ToggleButton
                                            name={cmd.name}
                                            value={!disabled.includes(cmd.name)}
                                            onChange={(v) => {
                                                setDisabled(prev =>
                                                    v ? prev.filter(n => n !== cmd.name) : [...prev, cmd.name]
                                                );
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}

            <dialog
                ref={dialogRef}
                onClick={(e) => e.target === dialogRef.current && closeModal()}
                className="rounded-xl p-0 shadow-2xl bg-gray-900 text-white border border-gray-700 
                            w-[90%] max-w-md 
                            fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                            backdrop:bg-black/70 backdrop:backdrop-blur-sm"
            >
                <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold">ロール制限設定</h2>
                        <button onClick={closeModal} className="text-gray-500 hover:text-white">✕</button>
                    </div>
                    
                    <p className="text-sm text-gray-400 mb-6">
                        <span className="text-blue-400 font-mono">/{editingCommand?.name}</span> を実行できるロールを選択してください。
                    </p>

                    <div className="space-y-4">
                        <label className="text-xs font-bold text-gray-500 uppercase">許可するロール</label>
                        <select
                            value={editingCommand ? (roleRestrictions[editingCommand.name] || "") : ""}
                            onChange={(e) => {
                                if (editingCommand) {
                                    setRoleRestrictions(prev => ({
                                        ...prev,
                                        [editingCommand.name]: e.target.value
                                    }));
                                }
                            }}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                        >
                            <option value="">制限なし (全員)</option>
                            {roles.map((r) => (
                                <option key={r.id} value={r.id}>{r.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex gap-3 mt-8">
                        <button 
                            type="button"
                            onClick={closeModal}
                            className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors font-medium"
                        >
                            閉じる
                        </button>
                        <button 
                            type="button"
                            onClick={closeModal}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors font-bold"
                        >
                            完了
                        </button>
                    </div>
                </div>
            </dialog>
        </>
    );
}