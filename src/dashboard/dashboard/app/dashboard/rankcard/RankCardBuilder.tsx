"use client";

import React, { useState, useEffect, useRef } from "react";

export const generateRankCard = async (
  color: string | [number, number, number],
  username: string,
  guildIconUrl: string | null,
  avatarUrl: string,
  level: number,
  xp: number,
  nextXp: number = 1000
): Promise<Blob> => {
  const W = 600;
  const H = 200;

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
  ctx.arc(100, 100, 63, 0, Math.PI * 2);
  ctx.fillStyle = baseColor;
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  ctx.arc(100, 100, 60, 0, Math.PI * 2);
  ctx.clip();
  ctx.drawImage(avatarImg, 40, 40, 120, 120);
  ctx.restore();

  ctx.textBaseline = "top";
  
  ctx.font = "bold 28px sans-serif";
  ctx.fillStyle = "#FFFFFF";
  ctx.fillText(username, 180, 40);

  const levelText = `LEVEL ${level}`;
  ctx.fillStyle = baseColor;
  const levelWidth = ctx.measureText(levelText).width;
  ctx.fillText(levelText, W - levelWidth - 30, 40);

  if (guildIconUrl) {
    try {
      const gIcon = await loadImage(guildIconUrl);
      ctx.save();
      ctx.beginPath();
      ctx.arc(195, 100, 15, 0, Math.PI * 2);
      ctx.clip();
      ctx.drawImage(gIcon, 180, 85, 30, 30);
      ctx.restore();
    } catch (e) {
      console.error("Guild icon load failed", e);
    }
  }

  const barX = 180, barY = 130, barW = 380, barH = 25;
  const progress = Math.min(xp / nextXp, 1.0);

  drawRoundedRect(ctx, barX, barY, barW, barH, 12, "#3c3c3c");
  
  if (progress > 0) {
    drawRoundedRect(ctx, barX, barY, barW * progress, barH, 12, baseColor);
  }

  ctx.font = "18px sans-serif";
  ctx.fillStyle = "#AAAAAA";
  ctx.fillText(`${xp} / ${nextXp} XP`, barX, barY + 35);

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
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
};

interface RankCardBuilderProps {
  initialData?: {
    username: string;
    level: number;
    xp: number;
    avatarUrl: string;
    color: string;
  };
  action: any
}

const COLOR_MAP = new Map<string, string>([
    ["red", "#7d344b"],
    ["yellow", "#889e1b"],
    ["blue", "#5058cc"],
    ["green", "#42f560"],
    ["gray", "#646464"]
]);

export default function RankCardBuilder({ initialData, action }: RankCardBuilderProps) {
  const [username, setUsername] = useState(initialData?.username || "Global User");
  const [level, setLevel] = useState(initialData?.level || 1);
  const [xp, setXp] = useState(initialData?.xp || 250);
  const [avatarUrl, setAvatarUrl] = useState(initialData?.avatarUrl || "https://via.placeholder.com/120");
  
  const [selected_color, setSelectedColor] = useState(initialData?.color || "gray");

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    const updatePreview = async () => {
      setIsGenerating(true);
      try {
        const blob = await generateRankCard(
          COLOR_MAP.get(selected_color) as string,
          username,
          null,
          avatarUrl,
          level,
          xp,
          100
        );
        
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setPreviewUrl(URL.createObjectURL(blob));
      } catch (err) {
        console.error("生成エラー:", err);
      } finally {
        setIsGenerating(false);
      }
    };

    const timer = setTimeout(updatePreview, 500);
    return () => clearTimeout(timer);
  }, [username, level, xp, COLOR_MAP.get(selected_color), avatarUrl]);

  return (
    <div className="p-6 text-white">
        <h2 className="text-2xl font-bold mb-6">ランクカード編集</h2>

        <div className="mb-8 border-2 border-dashed border-gray-600 p-4 rounded-lg flex bg-[#1e1f22]">
            {previewUrl ? (
            <img src={previewUrl} alt="Rank Card Preview" className="max-w-full h-auto rounded shadow-md" />
            ) : (
            <div className="h-[200px] w-[600px] flex">生成中...</div>
            )}
        </div>

        <form action={action}>
            <div className="flex flex-wrap gap-3 p-2 bg-[#1e1f22]">
                <input 
                    type="hidden" 
                    name="selected_color"
                    value={selected_color} 
                />

                {Array.from(COLOR_MAP).map(([name, hex]) => {
                    const isSelected = selected_color.toLowerCase() === hex.toLowerCase();
                    
                    return (
                    <button
                        key={name}
                        type="button"
                        title={name}
                        style={{ backgroundColor: hex }}
                        onClick={() => setSelectedColor(name)}
                        className={`w-10 h-10 rounded-full border-4 transition-all hover:scale-110 ${
                        isSelected 
                            ? "border-white shadow-[0_0_10px_rgba(255,255,255,0.5)] scale-110" 
                            : "border-transparent opacity-80 hover:opacity-100"
                        }`}
                    />
                    );
                })}
            </div><br/>

            <div className="flex flex-wrap gap-3 p-2 bg-[#1e1f22] rounded-lg">
                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-gray-400">レベル</label>
                    <input
                        type="number"
                        value={level}
                        onChange={(e) => setLevel(Number(e.target.value))}
                        className="p-2 rounded bg-[#383a40] border border-[#1e1f22]"
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-gray-400">現在のXP</label>
                    <input
                        type="number"
                        value={xp}
                        onChange={(e) => setXp(Number(e.target.value))}
                        className="p-2 rounded bg-[#383a40] border border-[#1e1f22]"
                    />
                </div>
            </div><br/>

            <div className="flex flex-wrap gap-3 p-2 bg-[#1e1f22] rounded-lg">
                <button
                    type="submit"
                    className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition"
                >
                    設定する
                </button>

                <a
                    href="/dashboard"
                    className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600 transition"
                >
                    戻る
                </a>
            </div>
        </form>
    </div>
  );
}