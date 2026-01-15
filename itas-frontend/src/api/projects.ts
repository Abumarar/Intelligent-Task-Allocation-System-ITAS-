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
    const { data } = await api.get<any>("/projects/");

    if (Array.isArray(data)) {
        return data;
    }

    if (data && typeof data === 'object' && Array.isArray(data.results)) {
        return data.results;
    }

    console.error("Expected array or paginated results from /projects/, got:", data);
    return [];
};

export const createProject = async (projectData: Partial<Project>) => {
    const { data } = await api.post<Project>("/projects/", projectData);
    return data;
};
