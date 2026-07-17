export default async function Home() {
  const res = await fetch("http://api:8000/hello", { cache: "no-store" });
  const data = await res.json();

  return (
    <main>
      <h1>Frontend</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  );
}
