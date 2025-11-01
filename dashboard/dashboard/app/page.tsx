export default function Home() {
  const loginUrl = `https://discord.com/api/oauth2/authorize?client_id=${process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID}&redirect_uri=${encodeURIComponent(process.env.NEXT_PUBLIC_DISCORD_REDIRECT_URI!)}&response_type=code&scope=identify%20guilds`;

  return (
    <main className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-3xl mb-6">SharkBot ダッシュボード</h1>
      <a
        href={loginUrl}
        className="bg-blue-600 text-white px-4 py-2 rounded-md"
      >
        Discordでログイン
      </a>
    </main>
  );
}
