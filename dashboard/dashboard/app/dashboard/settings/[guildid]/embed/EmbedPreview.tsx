"use client";

import { useRef, useEffect } from "react";

interface embedPreview {
    title: string, 
    description: string,
    color: any,
    image: string,
    thumbnail: string,
    onTitleChange: (val: string) => void,
    onDescChange: (val: string) => void,
    onImageChange: (val: string) => void, // 追加
    onThumbChange: (val: string) => void  // 追加
}

export default function EmbedPreview({ 
    title, 
    description, 
    color, 
    image, 
    thumbnail,
    onTitleChange,
    onDescChange,
    onImageChange,
    onThumbChange
}: embedPreview) {
    const titleRef = useRef<HTMLDivElement>(null);
    const descRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (titleRef.current && titleRef.current.innerText !== title) {
            titleRef.current.innerText = title;
        }
    }, [title]);

    useEffect(() => {
        if (descRef.current && descRef.current.innerText !== description) {
            descRef.current.innerText = description;
        }
    }, [description]);

    const handleEditImage = (type: 'image' | 'thumb') => {
        const currentUrl = type === 'image' ? image : thumbnail;
        const newUrl = window.prompt(`${type === 'image' ? 'メイン画像' : 'サムネイル'}のURLを入力してください:`, currentUrl);
        
        if (newUrl !== null) {
            if (type === 'image') onImageChange(newUrl);
            else onThumbChange(newUrl);
        }
    };

    return (
        <div
            className="mt-4 p-4 rounded-lg border bg-[#2f3136] text-white max-w-lg min-h-[100px] transition-all"
            style={{ borderLeft: `4px solid ${color}` }}
        >
            <div 
                onClick={() => handleEditImage('thumb')}
                className={`w-16 h-16 float-right ml-2 rounded cursor-pointer border-2 border-dashed border-transparent hover:border-white/30 transition flex items-center justify-center bg-black/10 ${!thumbnail && 'border-white/20'}`}
            >
                {thumbnail ? (
                    <img src={thumbnail} className="w-full h-full object-cover rounded" alt="" />
                ) : (
                    <span className="text-[10px] text-gray-400">Thumb</span>
                )}
            </div>

            <div
                ref={titleRef}
                contentEditable
                suppressContentEditableWarning
                onInput={(e) => onTitleChange(e.currentTarget.innerText)}
                className="text-xl font-bold mb-1 outline-none hover:bg-white/5 focus:bg-white/10 rounded px-1 transition cursor-text empty:before:content-['タイトルを入力...'] empty:before:text-gray-500"
            />

            <div
                ref={descRef}
                contentEditable
                suppressContentEditableWarning
                onInput={(e) => onDescChange(e.currentTarget.innerText)}
                className="whitespace-pre-wrap mb-2 outline-none hover:bg-white/5 focus:bg-white/10 rounded px-1 transition cursor-text min-h-[1.5rem] empty:before:content-['説明を入力...'] empty:before:text-gray-500"
            />

            <div 
                onClick={() => handleEditImage('image')}
                className={`mt-3 rounded cursor-pointer border-2 border-dashed border-transparent hover:border-white/30 transition overflow-hidden bg-black/10 flex items-center justify-center ${!image && 'h-20 border-white/20'}`}
            >
                {image ? (
                    <img src={image} className="max-h-60 w-full object-cover" alt="" />
                ) : (
                    <span className="text-sm text-gray-400 font-bold">メイン画像を追加 (Click)</span>
                )}
            </div>
        </div>
    );
}