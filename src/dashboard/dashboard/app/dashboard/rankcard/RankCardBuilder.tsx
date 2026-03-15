"use client";

import React, { useState, useEffect } from "react";

interface CategoryData {
  label: string;
  level: number;
  xp: number;
}

export const generateRankCard = async (
  color: string | [number, number, number],
  username: string,
  avatarUrl: string,
  data: {
    Level: number; XP: number;
    TextLevel: number; TextXP: number;
    VoiceLevel: number; VoiceXP: number;
  },
  nextXp: number = 80
): Promise<Blob> => {
  const W = 600;
  const H = 240;

  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas context not found");

  const baseColor = Array.isArray(color) 
    ? `rgb(${color[0]}, ${color[1]}, ${color[2]})` 
    : color;

  ctx.fillStyle = "#1e2127";
  ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = baseColor;
  ctx.fillRect(0, 0, 15, H);

  const avatarImg = await loadImage(avatarUrl);
  
  ctx.beginPath();
  ctx.arc(90, 90, 53, 0, Math.PI * 2);
  ctx.fillStyle = baseColor;
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  ctx.arc(90, 90, 50, 0, Math.PI * 2);
  ctx.clip();
  ctx.drawImage(avatarImg, 40, 40, 100, 100);
  ctx.restore();

  ctx.textBaseline = "top";
  ctx.font = "bold 28px sans-serif";
  ctx.fillStyle = "#FFFFFF";
  ctx.fillText(username, 160, 30);

  const categories: CategoryData[] = [
    { label: "TOTAL", level: data.Level, xp: data.XP },
    { label: "TEXT", level: data.TextLevel, xp: data.TextXP },
    { label: "VOICE", level: data.VoiceLevel, xp: data.VoiceXP }
  ];

  let startY = 75;
  categories.forEach((cat) => {
    ctx.font = "24px sans-serif";
    ctx.fillStyle = "#FFFFFF";
    ctx.fillText(`${cat.label} Lv.${cat.level}`, 160, startY);

    const xpTxt = `${cat.xp}/${nextXp} XP`;
    ctx.font = "16px sans-serif";
    ctx.fillStyle = "#AAAAAA";
    ctx.fillText(xpTxt, 480, startY + 5);

    const barX = 160, barY = startY + 32, barW = 400, barH = 10;
    const progress = Math.min(cat.xp / nextXp, 1.0);

    drawRoundedRect(ctx, barX, barY, barW, barH, 5, "#3c3c3c");

    if (progress > 0) {
      drawRoundedRect(ctx, barX, barY, barW * progress, barH, 5, baseColor);
    }

    startY += 50;
  });

  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob!), "image/png");
  });
};

const loadImage = (url: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
};

const drawRoundedRect = (
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number, fill: string
) => {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.fillStyle = fill;
  ctx.fill();
};

export default function RankCardBuilder({ initialData, action }: any) {
  const [username, setUsername] = useState(initialData?.username || "Global User");
  const [selected_color, setSelectedColor] = useState(initialData?.color || "blue");
  
  const [level, setLevel] = useState(initialData?.level || 1);
  const [xp, setXp] = useState(initialData?.xp || 250);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const COLOR_MAP = new Map<string, string>([
    ["red", "#7d344b"],
    ["yellow", "#889e1b"],
    ["blue", "#5058cc"],
    ["green", "#42f560"],
    ["gray", "#646464"]
  ]);

  useEffect(() => {
    const updatePreview = async () => {
      const blob = await generateRankCard(
        COLOR_MAP.get(selected_color) || "#5058cc",
        username,
        initialData?.avatarUrl || "https://via.placeholder.com/100",
        {
          Level: level, XP: xp,
          TextLevel: Math.floor(level * 0.8), TextXP: Math.floor(xp * 0.6),
          VoiceLevel: Math.floor(level * 0.4), VoiceXP: Math.floor(xp * 0.4)
        }
      );
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(blob));
    };

    const timer = setTimeout(updatePreview, 500);
    return () => clearTimeout(timer);
  }, [username, level, xp, selected_color]);

  return (
    <div className="p-6 text-white bg-[#2b2d31] min-h-screen">
      <h2 className="text-2xl font-bold mb-6">ランクカード編集</h2>

      <div className="mb-8 border border-gray-700 p-4 rounded-lg flex justify-center bg-[#1e1f22]">
        {previewUrl && (
          <img src={previewUrl} alt="Preview" className="max-w-full h-auto rounded shadow-xl" />
        )}
      </div>

      <form action={action} className="space-y-6">
        <div className="p-4 bg-[#1e1f22] rounded-lg">
          <p className="text-sm mb-3 text-gray-400">テーマカラー</p>
          <div className="flex gap-3">
            {Array.from(COLOR_MAP).map(([name, hex]) => (
              <button
                key={name}
                type="button"
                onClick={() => setSelectedColor(name)}
                style={{ backgroundColor: hex }}
                className={`w-10 h-10 rounded-full border-4 transition-all ${
                  selected_color === name ? "border-white scale-110" : "border-transparent opacity-70"
                }`}
              />
            ))}
          </div>
        </div>

        <input name="selected_color" value={selected_color} readOnly hidden></input>

        <div className="flex gap-3">
          <button type="submit" className="bg-indigo-500 px-8 py-2 rounded font-bold hover:bg-indigo-600 transition">
            保存する
          </button>
          <a href="/dashboard" className="bg-gray-600 px-8 py-2 rounded font-bold hover:bg-gray-700 transition">
            キャンセル
          </a>
        </div>
      </form>
    </div>
  );
}