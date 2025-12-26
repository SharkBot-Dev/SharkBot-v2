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

    return (
        <>
            <input
                type="text"
                placeholder="コマンド名・説明で検索"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="mb-6 w-full rounded bg-gray-800 text-white px-4 py-2 outline-none border border-gray-700 focus:border-blue-500"
            />

            {(Object.entries(grouped) as [string, Command[]][]).map(
                ([category, cmds]) => (
                    <div key={category} className="mb-8">
                        <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-1">
                            {category}
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
                                            defaultValue={
                                                !disabledCommands.includes(cmd.name)
                                            }
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