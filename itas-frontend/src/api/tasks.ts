import { api } from "./client";
import type { AxiosError } from "axios";

/** --------- Types --------- */

export type Priority = "LOW" | "MEDIUM" | "HIGH";

// If your backend uses other statuses, add them here.
// Keeping string fallback prevents breaking if backend returns an unknown value.
export type TaskStatus =
    | "UNASSIGNED"
    | "ASSIGNED"
    | "IN_PROGRESS"
    | "BLOCKED"
    | "DONE"
    | (string & {});

export type ISODateString = string;

export type Task = {
    id: string;
    title: string;
    description?: string;
    priority: Priority;
    status: TaskStatus;
    requiredSkills?: string[];

    created_at?: ISODateString;
    updated_at?: ISODateString;
    due_date?: ISODateString;

    assigned_to?: string;
    assigned_to_name?: string;
};

export type TaskCreateInput = {
    title: string;
    description?: string;
    priority: Priority;
    requiredSkills: string[];
    due_date?: ISODateString;
};

export type TaskUpdate = Partial<
    Pick<
        Task,
        | "title"
        | "description"
        | "priority"
        | "status"
        | "requiredSkills"
        | "due_date"
        | "assigned_to"
    >
>;

export type TaskMatch = {
    employee_id: string;
    employee_name: string;
    employee_title?: string;
    suitability_score: number; // 0..100 (or 0..1) depending on backend
    matching_skills: string[];
    missing_skills?: string[];
    current_workload: number; // number of tasks or hours depending on backend
};

type Paginated<T> = {
    results: T[];
    count?: number;
    next?: string | null;
    previous?: string | null;
};

export type TaskListResponse = Task[] | Paginated<Task>;

export type FetchTasksParams = {
    status?: TaskStatus;
    search?: string;
    ordering?: string; // e.g. "-created_at"
    page?: number;
    page_size?: number;
};

/** --------- Helpers --------- */

function normalizeList<T>(data: unknown): T[] {
    // Accept: array OR {results: array}
    if (Array.isArray(data)) return data as T[];
    if (data && typeof data === "object" && "results" in data && Array.isArray((data as { results: unknown[] }).results)) {
        return (data as { results: T[] }).results;
    }
    // Safer fallback instead of crashing
    return [];
}

export function getApiErrorMessage(err: unknown, fallback = "Request failed") {
    const e = err as AxiosError<{ message?: string; detail?: string }>;
    return (
        e?.response?.data?.message ||
        e?.response?.data?.detail ||
        (typeof e?.response?.data === "string" ? e.response.data : null) ||
        e?.message ||
        fallback
    );
}

/** If your backend expects trailing slashes (Django default), flip this to true. */
const USE_TRAILING_SLASH = true;
const withSlash = (path: string) => (USE_TRAILING_SLASH ? `${path}/` : path);

/** --------- API functions --------- */

export async function fetchTasks(params?: FetchTasksParams): Promise<Task[]> {
    const res = await api.get<TaskListResponse>(withSlash("/tasks"), { params });
    return normalizeList<Task>(res.data);
}

export async function fetchTask(taskId: string): Promise<Task> {
    const res = await api.get<Task>(withSlash(`/tasks/${taskId}`));
    return res.data;
}

export async function createTask(input: TaskCreateInput): Promise<Task> {
    const res = await api.post<Task>(withSlash("/tasks"), input);
    return res.data;
}

export async function updateTask(taskId: string, patch: TaskUpdate): Promise<Task> {
    const res = await api.patch<Task>(withSlash(`/tasks/${taskId}`), patch);
    return res.data;
}

export async function assignTask(taskId: string, employeeId: string): Promise<Task> {
    // Prefer returning the updated Task from backend if possible.
    const res = await api.post<Task>(withSlash(`/tasks/${taskId}/assign`), {
        employee_id: employeeId,
    });
    return res.data;
}

export async function unassignTask(taskId: string): Promise<Task> {
    const res = await api.post<Task>(withSlash(`/tasks/${taskId}/unassign`), {});
    return res.data;
}

export async function getTaskMatches(taskId: string): Promise<TaskMatch[]> {
    const res = await api.get(withSlash(`/tasks/${taskId}/matches`));
    return normalizeList<TaskMatch>(res.data);
}
