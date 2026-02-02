import { api } from "./client";

export type TaskStats = {
    total: number;
    completed: number;
    assigned: number;
    completion_rate: number;
};

export type WorkloadItem = {
    name: string;
    title: string;
    workload: number;
};

export type ReportsData = {
    task_stats: TaskStats;
    workload_distribution: WorkloadItem[];
    recent_assignments: number;
};

export async function fetchReports(): Promise<ReportsData> {
    const res = await api.get("/reports");
    return res.data;
}
