import { connectDB } from "@/lib/mongodb";
import Link from "next/link";

export const dynamic = "force-dynamic";

type Props = {
  searchParams: Promise<{ page?: string }>;
};

export default async function OpenVCPage({ searchParams }: Props) {
  const resolvedParams = await searchParams;
  const currentPage = Number(resolvedParams.page) || 1;
  
  const limit = 12;
  const skip = (currentPage - 1) * limit;

  const db = await connectDB();
  const collection = db.db("MainTwo").collection("OpenVC");

  const countPipeline = [
    { $unwind: "$channels" },
    { $count: "total" }
  ];
  const countResult = await collection.aggregate(countPipeline).toArray();
  const totalVCs = countResult[0]?.total || 0;
  const totalPages = Math.ceil(totalVCs / limit);

  const pipeline = [
    { $unwind: "$channels" },
    {
      $project: {
        guild_name: 1,
        guild_icon: 1,
        channel_name: "$channels.channel_name",
        invite_url: "$channels.invite_url",
        user_count: { $ifNull: ["$channels.user_count", 0] },
      }
    },
    { $skip: skip },
    { $limit: limit },
  ];

  const vcs = await collection.aggregate(pipeline).toArray();

  return (
    <main key={currentPage} className="px-4 py-6 max-w-6xl mx-auto">
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold mb-2">
          Discordボイスチャット掲示板
        </h1>
        <p className="text-zinc-400">今すぐ参加できるボイスチャット一覧</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {vcs.length > 0 ? (
          vcs.map((vc: any, index: number) => (
            <div
              key={`${vc._id}-${index}`}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col gap-4 shadow-xl hover:border-indigo-500/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <img 
                  src={vc.guild_icon} 
                  alt="" 
                  className="w-10 h-10 rounded-full bg-zinc-800 border border-zinc-700"
                />
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider truncate">
                    {vc.guild_name}
                  </span>
                  <h2 className="font-bold text-lg flex items-center gap-2 truncate">
                    {vc.channel_name}
                  </h2>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-zinc-400 bg-zinc-800/50 p-3 rounded-xl">
                <div className={`w-2 h-2 rounded-full ${vc.user_count > 0 ? 'bg-green-500 animate-pulse' : 'bg-zinc-600'}`} />
                {vc.user_count > 0 ? (
                  <span className="text-zinc-200 font-semibold">{vc.user_count} 人が参加中</span>
                ) : (
                  <span>誰もいないよ</span>
                )}
              </div>

              <a
                href={vc.invite_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 text-center bg-indigo-600 hover:bg-indigo-500 text-white transition-all rounded-xl py-3 font-bold shadow-lg shadow-indigo-900/20"
              >
                VCに参加する
              </a>
            </div>
          ))
        ) : (
          <p className="col-span-full text-center text-zinc-500 py-20">
            登録されているボイスチャットがありません。
          </p>
        )}
      </div>

      <div className="mt-12 flex justify-center items-center gap-6">
        {currentPage > 1 && (
          <Link
            href={`?page=${currentPage - 1}`}
            className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-full text-sm font-medium transition"
          >
            ← 前へ
          </Link>
        )}
        
        <span className="text-sm font-mono text-zinc-500">
          <span className="text-zinc-200">{currentPage}</span> / {totalPages}
        </span>

        {currentPage < totalPages && (
          <Link
            href={`?page=${currentPage + 1}`}
            className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-full text-sm font-medium transition"
          >
            次へ →
          </Link>
        )}
      </div>
    </main>
  );
}