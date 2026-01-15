import { api } from "./client";

export interface Project {
    id: string;
    title: string;
    description: string;
    manager: string; /* ID */
    manager_name: string;
    status: "ACTIVE" | "COMPLETED" | "ARCHIVED";
    created_at: string;
    updated_at: string;
    task_count: number;
    completed_task_count: number;
}

export const fetchProjects = async () => {
    const { data } = await api.get<Project[]>("/projects/");
    // Safeguard: Ensure we return an array. Using SPA proxy or misconfigured backend might return HTML.
    if (!Array.isArray(data)) {
        console.error("Expected array from /projects/, got:", data);
        return [];
    }
    return data;
};

export const createProject = async (projectData: Partial<Project>) => {
    const { data } = await api.post<Project>("/projects/", projectData);
    return data;
};
