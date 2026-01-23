export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-3xl mb-6">SharkBot ダッシュボード</h1>
      <a
        href="/api/auth/login"
        className="bg-blue-600 text-white px-4 py-2 rounded-md"
      >
        Discordでログイン
      </a><br></br>

      <h4>Discordでログインすると規約に同意したものとみなされます。</h4>
    </main>
  );
}
