// app/guild/[guildid]/embed/EmbedPreview.tsx
"use client";

interface embedPreview {
    title: string, 
    description: string,
    color: any,
    image: string,
    thumbnail: string
}

export default function embedPreview({ title, description, color, image, thumbnail }: embedPreview) {
    return (
        <div
            className="mt-4 p-4 rounded-lg border bg-[#2f3136] text-white max-w-lg"
            style={{ borderLeft: `4px solid ${color}` }}
        >
            {title && <h2 className="text-xl font-bold mb-1">{title}</h2>}
            {description && <p className="whitespace-pre-wrap mb-2">{description}</p>}

            {thumbnail && (
                <img src={thumbnail} className="w-16 h-16 float-right ml-2 rounded" />
            )}

            {image && (
                <img src={image} className="mt-3 rounded max-h-60 object-cover" />
            )}
        </div>
    );
}