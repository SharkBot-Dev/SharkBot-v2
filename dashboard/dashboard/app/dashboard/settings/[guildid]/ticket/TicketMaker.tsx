"use client";

import { useState, useMemo } from "react";
import ToggleButton from "@/app/components/ToggleButton";
import Form from "@/app/components/Form";

export default function TickerMaker({
    channelsData,
    createTicketPanel
}: {
    channelsData: any;
    createTicketPanel: any;
}) {
    const [isThreadTicket, setIsThreadTicket] = useState(false);

    return (
        <Form action={createTicketPanel} buttonlabel="チケットパネルを送信する">

            <label>
                タイトル
                <input
                    name="title"
                    className="border p-2 w-full bg-gray-800 text-white"
                    placeholder="タイトルを入力"
                    required
                />
            </label>

            <label>
                説明
                <textarea
                    name="description"
                    className="border p-2 w-full bg-gray-800 text-white"
                    placeholder="説明を入力"
                />
            </label>

            <span className="font-semibold mb-1">チケットをスレッドに作成するか</span>
            <ToggleButton name="thread_create" defaultValue={isThreadTicket} onChange={(e) => setIsThreadTicket(e)} />

            {!isThreadTicket && (
                <><span className="font-semibold mb-1">チケットを作成するカテゴリチャンネル</span><select
                    name="category_select"
                    className="border p-2 rounded bg-gray-800 text-white"
                >
                    {channelsData
                        ?.filter((ch: any) => ch.type === 4)
                        .map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                        ))}
                </select></>
            )}

            <span className="font-semibold mb-1">パネルを送信するチャンネル</span>

            <select
                name="channel_select"
                className="border p-2 rounded bg-gray-800 text-white"
                required
            >
                {channelsData
                    ?.filter((ch: any) => ch.type === 0)
                    .map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                            {ch.name}
                        </option>
                        ))}
            </select>
        </Form>
    )
};