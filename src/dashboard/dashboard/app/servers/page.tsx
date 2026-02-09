import { connectDB } from "@/lib/mongodb";
import Link from "next/link";

export const dynamic = "force-dynamic";

type Props = {
  searchParams: Promise<{ page?: string }>;
};

export default async function ServersPage({ searchParams }: Props) {
  const resolvedParams = await searchParams;
  const currentPage = Number(resolvedParams.page) || 1;
  
  const limit = 9;
  const skip = (currentPage - 1) * limit;

  const db = await connectDB();
  const cp = db.db("Main").collection("Register");

  const totalServers = await cp.countDocuments();
  const totalPages = Math.ceil(totalServers / limit);

  const pipeline = [
    {
      $addFields: {
        has_up: {
          $cond: [{ $ifNull: ["$Up", false] }, 1, 0],
        },
      },
    },
    {
      $sort: {
        has_up: -1,
        Up: -1,
      },
    },
    { $skip: skip },
    { $limit: limit },
  ];

  const servers = await cp.aggregate(pipeline).toArray();

  return (
    <main key={currentPage} className="px-4 py-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">
        Discordサーバー掲示板
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {servers.map((server: any) => (
          <div
            key={server._id.toString()}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3 shadow-md"
          >
            <div className="flex items-center gap-3">
              <img
                src={server.Icon}
                alt=""
                className="w-12 h-12 rounded-full bg-zinc-700"
              />
              <div className="flex-1">
                <h2 className="font-semibold text-lg leading-tight">
                  {server.Name}
                </h2>
              </div>
            </div>
            <p className="text-sm text-zinc-300 line-clamp-3">
              {server.Description || "説明はありません"}
            </p>
            <a
              href={server.Invite}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-auto text-center bg-indigo-600 hover:bg-indigo-500 transition rounded-lg py-2 text-sm font-medium"
            >
              サーバーに参加
            </a>
          </div>
        ))}
      </div>

      <div className="mt-10 flex justify-center items-center gap-4">
        {currentPage > 1 && (
          <Link
            href={`?page=${currentPage - 1}`}
            prefetch={false}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition"
          >
            前のページ
          </Link>
        )}
        
        <span className="text-sm text-zinc-400">
          {currentPage} / {totalPages}
        </span>

        {currentPage < totalPages && (
          <Link
            href={`?page=${currentPage + 1}`}
            prefetch={false}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition"
          >
            次のページ
          </Link>
        )}
      </div>
    </main>
  );
}