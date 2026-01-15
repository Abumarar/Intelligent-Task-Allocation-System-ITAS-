import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchTasks, updateTask, assignTask, type Task } from "../../api/tasks";
import { fetchEmployees } from "../../api/employees";

// Define TaskStatus type for type safety
type TaskStatus = "DRAFT" | "UNASSIGNED" | "ASSIGNED" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "CANCELLED";

const COLUMNS: { id: string; title: string; statuses: TaskStatus[]; color: string; border: string; bg: string }[] = [
    { id: "todo", title: "To Do", statuses: ["DRAFT", "UNASSIGNED"], color: "text-slate-600", border: "border-slate-200", bg: "bg-slate-50/50" },
    { id: "assigned", title: "Assigned", statuses: ["ASSIGNED"], color: "text-blue-600", border: "border-blue-200", bg: "bg-blue-50/50" },
    { id: "inprogress", title: "In Progress", statuses: ["IN_PROGRESS"], color: "text-amber-600", border: "border-amber-200", bg: "bg-amber-50/50" },
    { id: "blocked", title: "Blocked", statuses: ["BLOCKED"], color: "text-red-600", border: "border-red-200", bg: "bg-red-50/50" },
    { id: "done", title: "Done", statuses: ["COMPLETED"], color: "text-emerald-600", border: "border-emerald-200", bg: "bg-emerald-50/50" },
];

export default function Tasks() {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

    // Fetch tasks
    const { data: tasksData, isLoading: isLoadingTasks } = useQuery({
        queryKey: ["tasks"],
        queryFn: () => fetchTasks(),
    });

    // Fetch employees for assignment
    const { data: employeesData } = useQuery({
        queryKey: ["employees"],
        queryFn: () => fetchEmployees({ limit: 100 }),
    });

    const employees = employeesData || [];

    // Filter tasks by project if a projectId is present
    const tasks = tasksData ? (projectId
        ? tasksData.filter((t: any) => String(t.project_id) === projectId)
        : tasksData
    ) : [];

    // Update Task Mutation
    const updateTaskMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) => updateTask(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
            queryClient.invalidateQueries({ queryKey: ["projects"] });
        },
    });

    // Assign Task Mutation
    const assignTaskMutation = useMutation({
        mutationFn: ({ id, employeeId }: { id: string; employeeId: string }) => assignTask(id, employeeId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
        },
    });

    const handleStatusChange = (taskId: string, newStatus: TaskStatus) => {
        updateTaskMutation.mutate({ id: taskId, data: { status: newStatus } });
    };

    const handleAssign = (taskId: string, employeeId: string) => {
        if (!employeeId) return;
        assignTaskMutation.mutate({ id: taskId, employeeId });
    };

    const getPriorityStyle = (priority: string) => {
        switch (priority) {
            case "HIGH": return "bg-red-50 text-red-600 border-red-100 ring-1 ring-red-100";
            case "MEDIUM": return "bg-amber-50 text-amber-600 border-amber-100 ring-1 ring-amber-100";
            case "LOW": return "bg-blue-50 text-blue-600 border-blue-100 ring-1 ring-blue-100";
            default: return "bg-slate-50 text-slate-500 border-slate-100";
        }
    };

    // Group tasks by column
    const getTasksByColumn = (columnId: string) => {
        const column = COLUMNS.find(c => c.id === columnId);
        if (!column) return [];
        return tasks.filter(t => column.statuses.includes(t.status as TaskStatus));
    };

    if (isLoadingTasks) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-indigo-600/20 border-t-indigo-600 rounded-full animate-spin" />
                    <p className="text-slate-500 font-medium animate-pulse">Loading tasks...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page pb-8">
            {/* Hero Section */}
            <div className="page-hero mb-8">
                <div>
                    <div className="eyebrow text-indigo-600 font-bold tracking-wider mb-2">PROJECT MANAGEMENT</div>
                    <h1 className="page-title text-slate-900">
                        {projectId ? "Project Tasks" : "Task Board"}
                    </h1>
                    <p className="lead mt-2">Manage assignments and track progress across your team.</p>
                </div>

                <Link
                    to="/pm/tasks/new"
                    state={{ projectId }} // Pass projectId to create page
                    className="group flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/25 hover:bg-indigo-700 hover:shadow-indigo-600/35 hover:-translate-y-0.5 transition-all duration-200"
                >
                    <svg className="w-5 h-5 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                    <span>New Task</span>
                </Link>
            </div>

            {projectId && (
                <div className="mb-6 flex items-center gap-2 text-sm text-slate-500">
                    <Link to="/pm/projects" className="hover:text-indigo-600 flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Back to Projects
                    </Link>
                </div>
            )}

            {/* Kanban Board */}
            <div className="kanban-board">
                {COLUMNS.map((col) => {
                    const columnTasks = getTasksByColumn(col.id);
                    return (
                        <div key={col.id} className="kanban-column">
                            {/* Column Header */}
                            <div className={`flex items-center justify-between p-3 rounded-xl border ${col.border} ${col.bg} backdrop-blur-sm`}>
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${col.color.replace('text-', 'bg-')}`} />
                                    <h2 className={`font-bold ${col.color}`}>{col.title}</h2>
                                </div>
                                <span className={`px-2 py-0.5 rounded-md text-xs font-bold bg-white/60 ${col.color}`}>
                                    {columnTasks.length}
                                </span>
                            </div>

                            {/* Task List */}
                            <div className="flex flex-col gap-3 min-h-[200px]">
                                {columnTasks.length === 0 ? (
                                    <div className="h-32 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center text-slate-400 text-sm font-medium italic bg-slate-50/50">
                                        No tasks
                                    </div>
                                ) : (
                                    columnTasks.map((task) => (
                                        <div
                                            key={task.id}
                                            className="group bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-3"
                                        >
                                            {/* Header: Priority & Date */}
                                            <div className="flex justify-between items-start">
                                                <span className={`px-2 py-1 rounded-lg text-[10px] font-bold tracking-wide uppercase ${getPriorityStyle(task.priority)}`}>
                                                    {task.priority}
                                                </span>
                                                {task.due_date && (
                                                    <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
                                                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                        </svg>
                                                        {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Body: Title */}
                                            <h3 className="font-semibold text-slate-800 leading-snug group-hover:text-indigo-700 transition-colors">
                                                {task.title}
                                            </h3>

                                            {/* Skills */}
                                            {task.requiredSkills && task.requiredSkills.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {task.requiredSkills.map(skill => (
                                                        <span key={skill} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-medium border border-slate-200">
                                                            {skill}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Divider */}
                                            <div className="h-px bg-slate-100" />

                                            {/* Footer: Controls */}
                                            <div className="flex items-center justify-between gap-2">
                                                {/* Status Selector */}
                                                <div className="relative">
                                                    <select
                                                        className="appearance-none pl-2 pr-6 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition-colors cursor-pointer outline-none focus:ring-2 focus:ring-indigo-500/20"
                                                        value={task.status}
                                                        onChange={(e) => handleStatusChange(task.id, e.target.value as TaskStatus)}
                                                    >
                                                        <option value="DRAFT">Draft</option>
                                                        <option value="UNASSIGNED">Unassigned</option>
                                                        <option value="ASSIGNED">Assigned</option>
                                                        <option value="IN_PROGRESS">In Progress</option>
                                                        <option value="BLOCKED">Blocked</option>
                                                        <option value="COMPLETED">Done</option>
                                                        <option value="CANCELLED">Cancel</option>
                                                    </select>
                                                    <div className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                        </svg>
                                                    </div>
                                                </div>

                                                {/* Assignee Selector */}
                                                <div className="relative flex-1 max-w-[200px]">
                                                    <select
                                                        className={`appearance-none w-full pl-7 pr-6 py-1 border rounded-lg text-xs font-semibold cursor-pointer outline-none transition-all ${task.assigned_to
                                                            ? "bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100"
                                                            : "bg-slate-50 border-slate-200 text-slate-400 hover:border-slate-300 hover:text-slate-600"
                                                            }`}
                                                        value={task.assigned_to || ""}
                                                        onChange={(e) => handleAssign(task.id, e.target.value)}
                                                    >
                                                        <option value="" disabled>Assign...</option>
                                                        {employees.map((emp) => (
                                                            <option key={emp.id} value={emp.id}>
                                                                {emp.name} {emp.title ? `(${emp.title})` : ""}
                                                            </option>
                                                        ))}
                                                    </select>

                                                    {/* Avatar Icon */}
                                                    <div className="absolute left-1.5 top-1/2 -translate-y-1/2 pointer-events-none">
                                                        {task.assigned_to ? (
                                                            <div className="w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[8px] font-bold">
                                                                <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                                </svg>
                                                            </div>
                                                        ) : (
                                                            <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                                            </svg>
                                                        )}
                                                    </div>

                                                    {/* Chevron */}
                                                    <div className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-current opacity-50">
                                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                        </svg>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
