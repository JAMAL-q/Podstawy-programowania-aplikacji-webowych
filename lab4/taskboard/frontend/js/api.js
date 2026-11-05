const API_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(status, message, errors = []) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const problem = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      problem?.detail ?? response.statusText,
      problem?.errors ?? []
    );
  }
  return response;
}

export async function fetchTasks(status = "") {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await request(`/tasks${query}`);
  const data = await response.json();
  const totalHeader = response.headers.get("X-Total-Count");
  return { items: data.items, totalHeader };
}

export async function createTask(payload) {
  const response = await request("/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function deleteTask(id) {
  await request(`/tasks/${id}`, { method: "DELETE" });
}