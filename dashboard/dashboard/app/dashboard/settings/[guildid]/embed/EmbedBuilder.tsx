"use client";

import { useState } from "react";
import EmbedPreview from "./EmbedPreview";
import ColorPalette from "@/app/components/ColorPicker";

interface embedBuilder {
  guild: any,
  channels: any,
  sendData: any
}

export default function embedBuilder({ guild, channels, sendData }: embedBuilder) {
    const [title, setTitle] = useState("");
    const [desc, setDesc] = useState("");
    const [color, setColor] = useState("#57f287");
    const [image, setImage] = useState("");
    const [thumb, setThumb] = useState("");

    return (
        <div className="p-4">
            <form action={sendData} className="flex flex-col gap-2">
                <h2 className="text-xl font-bold mt-6">タイトル・説明</h2>
                <input
                    name="title"
                    placeholder="タイトル"
                    className="border p-2"
                    onChange={(e) => setTitle(e.target.value)}
                />
                <textarea
                    name="desc"
                    placeholder="説明"
                    className="border p-2"
                    onChange={(e) => setDesc(e.target.value)}
                />

                <h2 className="text-xl font-bold mt-6">色</h2>
                <ColorPalette
                    name="color"
                    onChange={(color: any) => setColor(color)}
                />

                <h2 className="text-xl font-bold mt-6">画像・サムネイル</h2>
                <input
                    name="image_url"
                    placeholder="画像URL"
                    className="border p-2"
                    onChange={(e) => setImage(e.target.value)}
                />
                <input
                    name="thumbnail_url"
                    placeholder="サムネイルURL"
                    className="border p-2"
                    onChange={(e) => setThumb(e.target.value)}
                />

                <select
                    name="channel"
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500"
                >
                    {channels
                        .filter((c: any) => c.type === 0)
                        .map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                        ))}
                </select>

                <button className="bg-blue-500 text-white p-2 rounded">
                    送信する
                </button>
            </form>

            {/* プレビュー */}
            <h2 className="text-xl font-bold mt-6">プレビュー</h2>
            <EmbedPreview
                title={title}
                description={desc}
                color={color}
                image={image}
                thumbnail={thumb}
            />
        </div>
    );
}