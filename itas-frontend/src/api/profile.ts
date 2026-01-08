import { api } from "./client";
import type { Employee } from "./employees";

export type EmployeeProfile = {
    employee: Employee;
    tasks: Array<{
        id: string;
        title: string;
        status: string;
        priority: string;
        suitability_score: number;
        due_date?: string;
    }>;
    workload: number;
};

export async function fetchMyProfile(): Promise<EmployeeProfile> {
    const res = await api.get("/employees/my-profile");
    return res.data;
}
