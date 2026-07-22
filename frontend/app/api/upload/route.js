export async function POST(request) {
  const formData = await request.formData();
  const res = await fetch("http://api:8000/upload", {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
