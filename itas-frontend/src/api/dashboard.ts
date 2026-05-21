import { api } from "./client";

export type DashboardStats = {
    active_tasks: number;
    unassigned_tasks: number;
    employee_capacity: number;
    skills_coverage: number;
};

export async function fetchDashboardStats(): Promise<DashboardStats> {
    const res = await api.get("/dashboard/stats");
    return res.data;
}
