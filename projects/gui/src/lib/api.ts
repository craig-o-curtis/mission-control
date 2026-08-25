import { MISSIONS_API, CHECKLISTS_API } from "./config";

export interface Mission {
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

export interface MissionInput {
  mission_name: string;
  commander: string;
  mission_type: string;
  description?: string | null;
  phase?: string | null;
  priority?: number | null;
  launch_date?: string | null;
}

export interface ChecklistItem {
  id: number;
  checklist_item: string;
  description: string | null;
  criticality: number | null;
  executed: boolean;
  mission_id: number | null;
  notes: string | null;
  seeded: boolean;
}

export interface ChecklistItemInput {
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

async function missionsReq(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${MISSIONS_API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw await parseError(res);
  return res;
}

export const missionsApi = {
  list: async (): Promise<Mission[]> => (await missionsReq("/missions")).json(),
  create: async (input: MissionInput): Promise<Mission> =>
    (await missionsReq("/missions", { method: "POST", body: JSON.stringify(input) })).json(),
  update: async (id: number, input: Partial<MissionInput>): Promise<Mission> =>
    (
      await missionsReq(`/missions/${id}`, {
        method: "PUT",
        body: JSON.stringify(input),
      })
    ).json(),
  remove: async (id: number): Promise<void> => {
    await missionsReq(`/missions/${id}`, { method: "DELETE" });
  },
  reset: async (): Promise<void> => {
    await missionsReq("/missions/reset", { method: "POST" });
  },
};

async function checklistsReq(path: string, token: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${CHECKLISTS_API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    ...init,
  });
  if (!res.ok) throw await parseError(res);
  return res;
}

export const checklistsApi = {
  login: async (username: string, password: string): Promise<string> => {
    const body = new URLSearchParams({ username, password });
    const res = await fetch(`${CHECKLISTS_API}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw await parseError(res);
    const data = (await res.json()) as { access_token: string };
    return data.access_token;
  },
  // The checklists collection route is registered as `/checklists/` (trailing slash), so we
  // call it with the slash to avoid a 307 redirect that breaks the SPA fetch.
  list: async (token: string): Promise<ChecklistItem[]> =>
    (await checklistsReq("/checklists/", token)).json(),
  create: async (token: string, input: ChecklistItemInput): Promise<ChecklistItem> =>
    (
      await checklistsReq("/checklists/", token, {
        method: "POST",
        body: JSON.stringify(input),
      })
    ).json(),
  update: async (token: string, id: number, input: Partial<ChecklistItemInput>): Promise<void> => {
    await checklistsReq(`/checklists/${id}`, token, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },
  remove: async (token: string, id: number): Promise<void> => {
    await checklistsReq(`/checklists/${id}`, token, { method: "DELETE" });
  },
  reset: async (token: string): Promise<void> => {
    await checklistsReq("/admin/checklists/reset", token, { method: "POST" });
  },
};
