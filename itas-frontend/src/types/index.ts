export interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    name: string;
    role: 'PM' | 'EMPLOYEE';
}

export interface Employee {
    id: string;
    name: string;
    title: string;
    email: string;
    skills: string[];
    cvStatus: 'NOT_UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED';
    cvUpdatedAt?: string;
    cvErrorMessage?: string;
    cvUrl?: string;
    current_workload: number;
    assigned_tasks: TaskAssignment[];
    average_performance?: number;
}

export interface Task {
    id: string;
    title: string;
    description: string;
    priority: 'LOW' | 'MEDIUM' | 'HIGH';
    status: 'DRAFT' | 'UNASSIGNED' | 'ASSIGNED' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED';
    requiredSkills: string[];
    created_by: string;
    created_by_name: string;
    created_at: string;
    updated_at: string;
    start_date?: string;
    due_date?: string;
    assigned_to?: string;
    assigned_to_name?: string;
    project_id?: string;
    project_title?: string;
}

export interface TaskAssignment {
    id: string;
    task: string;
    task_title: string;
    employee: string;
    employee_name: string;
    suitability_score: number;
    status: 'ASSIGNED' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED';
    assigned_at: string;
    started_at?: string;
    completed_at?: string;
    notes?: string;
    performance_rating?: number;
}

export interface Project {
    id: string;
    title: string;
    description: string;
    manager: string;
    manager_name: string;
    status: 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';
    created_at: string;
    updated_at: string;
    task_count: number;
    completed_task_count: number;
}
