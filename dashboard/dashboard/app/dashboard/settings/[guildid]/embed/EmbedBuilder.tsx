"use client";

import { useState } from "react";
import EmbedPreview from "./EmbedPreview";
import ColorPalette from "@/app/components/ColorPicker";

interface embedBuilder {
  guild: any,
  channels: any,
  sendData: any
}

export default function EmbedBuilder({ guild, channels, sendData }: embedBuilder) {
    const [title, setTitle] = useState("");
    const [desc, setDesc] = useState("");
    const [color, setColor] = useState("#57f287");
    const [image, setImage] = useState("");
    const [thumb, setThumb] = useState("");

    return (
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-8">
            <form action={sendData} className="flex flex-col gap-2">
                <h2 className="text-xl font-bold mt-6">タイトル・説明</h2>
                <input
                    name="title"
                    placeholder="タイトル"
                    className="border p-2 bg-gray-50 text-black"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
                <textarea
                    name="desc"
                    placeholder="説明"
                    className="border p-2 bg-gray-50 text-black"
                    value={desc}
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
                    className="border p-2 bg-gray-50 text-black"
                    value={image}
                    onChange={(e) => setImage(e.target.value)}
                />
                <input
                    name="thumbnail_url"
                    placeholder="サムネイルURL"
                    className="border p-2 bg-gray-50 text-black"
                    value={thumb}
                    onChange={(e) => setThumb(e.target.value)}
                />

                <h2 className="text-xl font-bold mt-6">チャンネル選択・送信</h2>
                <select
                    name="channel"
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500"
                >
                    {channels
                        .filter((c: any) => c.type === 0)
                        .map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                #{ch.name}
                            </option>
                        ))}
                </select>

                <button className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded transition mt-4">
                    送信する
                </button>
            </form>

            <div>
                <h2 className="text-xl font-bold mt-6 mb-4">プレビュー</h2>
                <EmbedPreview
                    title={title}
                    description={desc}
                    color={color}
                    image={image}
                    thumbnail={thumb}
                    onTitleChange={setTitle}
                    onDescChange={setDesc}
                    onImageChange={setImage}
                    onThumbChange={setThumb}
                />
            </div>
        </div>
    );
}