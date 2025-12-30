import { cookies } from "next/headers";
import { connectDB } from "@/lib/mongodb";

export default async function DashboardPage() {
  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;

  if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

  const db = await connectDB();
  const session = await db.db('Dashboard').collection("Sessions").findOne({ session_id: sessionId });

  if (!session) return <p>セッションが無効です。</p>;

  const user = session.user;
  const guilds = session.guilds;

  return (
    <main className="p-10">
      <div className="flex flex-col items-center mb-10">
        <img
          src={`https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`}
          alt="avatar"
          width={80}
          height={80}
          className="rounded-full"
        />
        <h1 className="text-2xl mt-3">{user.username}#{user.discriminator}</h1>
      </div>

      <h2 className="text-xl mb-4">あなたが持っているサーバー</h2>
      <ul className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {guilds.map((g: any) => (
          g.owner ? (
            <a href={`/dashboard/settings/${g.id}/`} className="bg-gray-800 text-white p-4 rounded-lg">
              <li key={g.id}>
                
                  <img
                    src={g.icon
                      ? `https://cdn.discordapp.com/icons/${g.id}/${g.icon}.png`
                      : "https://cdn.discordapp.com/embed/avatars/0.png"}
                    alt="guild"
                    className="w-16 h-16 rounded-full mx-auto"
                  />
                  <p className="mt-2 text-center">{g.name}</p>
                
              </li>
            </a>
          ) : null
        ))}
      </ul><br/>

      <h2 className="text-xl mb-4">その他の手続き</h2>
      <a
        href="/api/auth/logout"
        className="bg-red-600 text-white px-4 py-2 rounded-md"
      >
        ログアウト
      </a>
      <br></br>
    </main>
  );
}