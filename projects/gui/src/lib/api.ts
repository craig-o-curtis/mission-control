import { BOOKS_API, TASKS_API } from "./config";

export interface Book {
  id: number;
  mission_name: string;
  commander: string;
  mission_type: string;
  description: string | null;
  phase: string | null;
  priority: number | null;
  launch_date: string | null;
  seeded: boolean;
}

export interface BookInput {
  mission_name: string;
  commander: string;
  mission_type: string;
  description?: string | null;
  phase?: string | null;
  priority?: number | null;
  launch_date?: string | null;
}

export interface Task {
  id: number;
  checklist_item: string;
  description: string | null;
  criticality: number | null;
  executed: boolean;
  mission_id: number | null;
  notes: string | null;
  seeded: boolean;
}

export interface TaskInput {
  checklist_item: string;
  description?: string | null;
  criticality?: number | null;
  executed?: boolean;
  mission_id?: number | null;
  notes?: string | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let detail = res.statusText;
  try {
    const data = (await res.json()) as {
      detail?: string | { msg: string }[];
    };
    if (typeof data.detail === "string") detail = data.detail;
    else if (Array.isArray(data.detail)) detail = data.detail.map((d) => d.msg).join("; ");
  } catch {
    /* response had no JSON body */
  }
  return new ApiError(res.status, detail);
}

async function booksReq(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${BOOKS_API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw await parseError(res);
  return res;
}

export const booksApi = {
  list: async (): Promise<Book[]> => (await booksReq("/books")).json(),
  create: async (input: BookInput): Promise<Book> =>
    (await booksReq("/books", { method: "POST", body: JSON.stringify(input) })).json(),
  update: async (id: number, input: Partial<BookInput>): Promise<Book> =>
    (
      await booksReq(`/books/${id}`, {
        method: "PUT",
        body: JSON.stringify(input),
      })
    ).json(),
  remove: async (id: number): Promise<void> => {
    await booksReq(`/books/${id}`, { method: "DELETE" });
  },
  reset: async (): Promise<void> => {
    await booksReq("/books/reset", { method: "POST" });
  },
};

async function tasksReq(path: string, token: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${TASKS_API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    ...init,
  });
  if (!res.ok) throw await parseError(res);
  return res;
}

export const tasksApi = {
  login: async (username: string, password: string): Promise<string> => {
    const body = new URLSearchParams({ username, password });
    const res = await fetch(`${TASKS_API}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw await parseError(res);
    const data = (await res.json()) as { access_token: string };
    return data.access_token;
  },
  // The tasks collection route is registered as `/tasks/` (trailing slash), so we
  // call it with the slash to avoid a 307 redirect that breaks the SPA fetch.
  list: async (token: string): Promise<Task[]> => (await tasksReq("/tasks/", token)).json(),
  create: async (token: string, input: TaskInput): Promise<Task> =>
    (
      await tasksReq("/tasks/", token, {
        method: "POST",
        body: JSON.stringify(input),
      })
    ).json(),
  update: async (token: string, id: number, input: Partial<TaskInput>): Promise<void> => {
    await tasksReq(`/tasks/${id}`, token, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },
  remove: async (token: string, id: number): Promise<void> => {
    await tasksReq(`/tasks/${id}`, token, { method: "DELETE" });
  },
  reset: async (token: string): Promise<void> => {
    await tasksReq("/admin/tasks/reset", token, { method: "POST" });
  },
};
