import { api } from "./client";

export type Employee = {
    id: string;
    name: string;
    title?: string;
    email?: string;
    skills?: string[];
    cvStatus?: "NOT_UPLOADED" | "PROCESSING" | "READY" | "FAILED";

    cvUpdatedAt?: string;
    current_workload?: number;
};

export async function fetchEmployees(params?: { page?: number; limit?: number }): Promise<Employee[]> {
    const res = await api.get("/employees/", {
        params: {
            page: params?.page,
            page_size: params?.limit || 100 // Default to 100 to get "all" for dropdowns
        }
    });
    return Array.isArray(res.data) ? res.data : (res.data.results || []);
}

export async function createEmployee(data: { name: string; email: string; title: string }) {
    const res = await api.post("/employees/", data);
    return res.data;
}

export async function updateEmployee(id: string, data: Partial<{ name: string; email: string; title: string }>) {
    const res = await api.patch(`/employees/${id}/`, data);
    return res.data;
}

export async function deleteEmployee(id: string) {
    const res = await api.delete(`/employees/${id}/`);
    return res.data;
}

export async function uploadEmployeeCV(employeeId: string, file: File) {
    const form = new FormData();
    form.append("file", file);

    const res = await api.post(`/employees/${employeeId}/cv/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
}

export async function analyzeEmployeeCV(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api.post("/employees/analyze/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data; // { name, email, role }
}
