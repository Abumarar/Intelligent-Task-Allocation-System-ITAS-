import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchTasks, updateTask, assignTask, ratePerformance, type Task, type PerformanceRatingData } from "../../api/tasks";
import { fetchEmployees } from "../../api/employees";

// Define TaskStatus type for type safety
type TaskStatus = "DRAFT" | "UNASSIGNED" | "ASSIGNED" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "CANCELLED";

const COLUMNS: { id: string; title: string; statuses: TaskStatus[]; color: string; border: string; bg: string }[] = [
    { id: "todo", title: "To Do", statuses: ["DRAFT", "UNASSIGNED"], color: "text-slate-600 dark:text-slate-400", border: "border-slate-200 dark:border-slate-700", bg: "bg-slate-50/50 dark:bg-slate-800/50" },
    { id: "assigned", title: "Assigned", statuses: ["ASSIGNED"], color: "text-blue-600 dark:text-blue-400", border: "border-blue-200 dark:border-blue-800", bg: "bg-blue-50/50 dark:bg-blue-950/30" },
    { id: "inprogress", title: "In Progress", statuses: ["IN_PROGRESS"], color: "text-amber-600 dark:text-amber-400", border: "border-amber-200 dark:border-amber-800", bg: "bg-amber-50/50 dark:bg-amber-950/30" },
    { id: "blocked", title: "Blocked", statuses: ["BLOCKED"], color: "text-red-600 dark:text-red-400", border: "border-red-200 dark:border-red-800", bg: "bg-red-50/50 dark:bg-red-950/30" },
    { id: "done", title: "Done", statuses: ["COMPLETED"], color: "text-emerald-600 dark:text-emerald-400", border: "border-emerald-200 dark:border-emerald-800", bg: "bg-emerald-50/50 dark:bg-emerald-950/30" },
];

export default function Tasks() {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    
    const [ratingTask, setRatingTask] = useState<Task | null>(null);
    const [ratingData, setRatingData] = useState<PerformanceRatingData>({
        quality_rating: 5,
        timeliness_rating: 5,
        communication_rating: 5,
        technical_rating: 5,
        performance_comments: ""
    });

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

    // Rate Performance Mutation
    const ratePerformanceMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: PerformanceRatingData }) => ratePerformance(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
            queryClient.invalidateQueries({ queryKey: ["employees"] });
            setRatingTask(null);
        },
    });

    const handleStatusChange = (task: Task, newStatus: TaskStatus) => {
        updateTaskMutation.mutate({ id: task.id, data: { status: newStatus } }, {
            onSuccess: () => {
                if (newStatus === "COMPLETED") {
                    setRatingData({
                        quality_rating: 5,
                        timeliness_rating: 5,
                        communication_rating: 5,
                        technical_rating: 5,
                        performance_comments: ""
                    });
                    setRatingTask(task);
                }
            }
        });
    };

    const submitRating = () => {
        if (ratingTask) {
            ratePerformanceMutation.mutate({ id: ratingTask.id, data: ratingData });
        }
    };

    const handleAssign = (taskId: string, employeeId: string) => {
        if (!employeeId) return;
        assignTaskMutation.mutate({ id: taskId, employeeId });
    };

    const getPriorityStyle = (priority: string) => {
        switch (priority) {
            case "HIGH": return "bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800 ring-1 ring-red-100 dark:ring-red-800";
            case "MEDIUM": return "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800 ring-1 ring-amber-100 dark:ring-amber-800";
            case "LOW": return "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800 ring-1 ring-blue-100 dark:ring-blue-800";
            default: return "bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-100 dark:border-slate-700";
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
                    <p className="text-slate-500 dark:text-slate-400 font-medium animate-pulse">Loading tasks...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page pb-8">
            {/* Hero Section */}
            <div className="page-hero mb-8">
                <div>
                    <div className="eyebrow text-indigo-600 dark:text-indigo-400 font-bold tracking-wider mb-2">PROJECT MANAGEMENT</div>
                    <h1 className="page-title text-slate-900 dark:text-white">
                        {projectId ? "Project Tasks" : "Task Board"}
                    </h1>
                    <p className="lead mt-2">Manage assignments and track progress across your team.</p>
                </div>

                <Link
                    to="/pm/tasks/new"
                    state={{ projectId }} // Pass projectId to create page
                    className="group flex items-center gap-2 px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/25 hover:bg-indigo-700 dark:hover:bg-indigo-600 hover:shadow-indigo-600/35 hover:-translate-y-0.5 transition-all duration-200"
                >
                    <svg className="w-5 h-5 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                    <span>New Task</span>
                </Link>
            </div>

            {projectId && (
                <div className="mb-6 flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    <Link to="/pm/projects" className="hover:text-indigo-600 dark:hover:text-indigo-400 flex items-center gap-1">
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
                                <span className={`px-2 py-0.5 rounded-md text-xs font-bold bg-white/60 dark:bg-white/10 ${col.color}`}>
                                    {columnTasks.length}
                                </span>
                            </div>

                            {/* Task List */}
                            <div className="flex flex-col gap-3 min-h-[200px]">
                                {columnTasks.length === 0 ? (
                                    <div className="h-32 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl flex items-center justify-center text-slate-400 dark:text-slate-500 text-sm font-medium italic bg-slate-50/50 dark:bg-slate-800/30">
                                        No tasks
                                    </div>
                                ) : (
                                    columnTasks.map((task) => (
                                        <div
                                            key={task.id}
                                            className="group bg-white dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-700 hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-3"
                                        >
                                            {/* Header: Priority & Date */}
                                            <div className="flex justify-between items-start">
                                                <span className={`px-2 py-1 rounded-lg text-[10px] font-bold tracking-wide uppercase ${getPriorityStyle(task.priority)}`}>
                                                    {task.priority}
                                                </span>
                                                {task.due_date && (
                                                    <div className="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 font-medium">
                                                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                        </svg>
                                                        {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Body: Title */}
                                            <h3 className="font-semibold text-slate-800 dark:text-slate-100 leading-snug group-hover:text-indigo-700 dark:group-hover:text-indigo-400 transition-colors">
                                                {task.title}
                                            </h3>

                                            {/* Skills */}
                                            {task.requiredSkills && task.requiredSkills.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {task.requiredSkills.map(skill => (
                                                        <span key={skill} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-medium border border-slate-200 dark:border-slate-600">
                                                            {skill}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Employee Notes */}
                                            {task.employee_notes && (
                                                <div className="mt-2 p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-400 italic flex gap-2">
                                                    <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                                    </svg>
                                                    <span className="line-clamp-2" title={task.employee_notes}>
                                                        {task.employee_notes}
                                                    </span>
                                                </div>
                                            )}

                                            {/* Performance Rating */}
                                            {task.status === "COMPLETED" && (
                                                <div className="mt-1">
                                                    {task.performance_rating ? (
                                                        <div className="flex flex-col gap-1 p-2.5 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800/50 rounded-lg">
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400">PM Rating</span>
                                                                <div className="flex items-center gap-1">
                                                                    <svg className="w-3.5 h-3.5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                                                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                                    </svg>
                                                                    <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{task.performance_rating.toFixed(1)}/5</span>
                                                                </div>
                                                            </div>
                                                            {task.performance_comments && (
                                                                <div className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 line-clamp-2" title={task.performance_comments}>
                                                                    "{task.performance_comments}"
                                                                </div>
                                                            )}
                                                            <button 
                                                                onClick={() => {
                                                                    setRatingData({
                                                                        quality_rating: 5,
                                                                        timeliness_rating: 5,
                                                                        communication_rating: 5,
                                                                        technical_rating: 5,
                                                                        performance_comments: task.performance_comments || ""
                                                                    });
                                                                    setRatingTask(task);
                                                                }}
                                                                className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold text-right mt-1 hover:underline"
                                                            >
                                                                Update Rating
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <button 
                                                            onClick={() => {
                                                                setRatingData({
                                                                    quality_rating: 5,
                                                                    timeliness_rating: 5,
                                                                    communication_rating: 5,
                                                                    technical_rating: 5,
                                                                    performance_comments: ""
                                                                });
                                                                setRatingTask(task);
                                                            }}
                                                            className="w-full py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 rounded-lg text-xs font-bold hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors flex items-center justify-center gap-1.5"
                                                        >
                                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                                                            </svg>
                                                            Rate Performance
                                                        </button>
                                                    )}
                                                </div>
                                            )}

                                            {/* Divider */}
                                            <div className="h-px bg-slate-100 dark:bg-slate-700" />

                                            {/* Footer: Controls */}
                                            <div className="flex items-center justify-between gap-2">
                                                {/* Status Selector */}
                                                <div className="relative">
                                                    <select
                                                        className="appearance-none pl-2 pr-6 py-1 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-700 dark:hover:text-indigo-400 transition-colors cursor-pointer outline-none focus:ring-2 focus:ring-indigo-500/20"
                                                        value={task.status}
                                                        onChange={(e) => handleStatusChange(task, e.target.value as TaskStatus)}
                                                    >
                                                        <option value="DRAFT">Draft</option>
                                                        <option value="UNASSIGNED">Unassigned</option>
                                                        <option value="ASSIGNED">Assigned</option>
                                                        <option value="IN_PROGRESS">In Progress</option>
                                                        <option value="BLOCKED">Blocked</option>
                                                        <option value="COMPLETED">Done</option>
                                                        <option value="CANCELLED">Cancel</option>
                                                    </select>
                                                    <div className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 dark:text-slate-500">
                                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                        </svg>
                                                    </div>
                                                </div>

                                                {/* Assignee Selector */}
                                                <div className="relative flex-1 max-w-[200px]">
                                                    <select
                                                        className={`appearance-none w-full pl-7 pr-6 py-1 border rounded-lg text-xs font-semibold cursor-pointer outline-none transition-all ${task.assigned_to
                                                            ? "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-950/60"
                                                            : "bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-400 dark:text-slate-500 hover:border-slate-300 dark:hover:border-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
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
                                                            <svg className="w-4 h-4 text-slate-300 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

            {/* Performance Rating Modal */}
            {ratingTask && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 dark:bg-black/60 backdrop-blur-sm">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-200">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">Rate Performance</h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                            Provide detailed feedback for <span className="font-semibold text-slate-700 dark:text-slate-200">{ratingTask.assigned_to_name || 'the employee'}</span> on task: <span className="italic">{ratingTask.title}</span>
                        </p>

                        <div className="space-y-4 mb-6">
                            {['quality', 'timeliness', 'communication', 'technical'].map((metric) => {
                                const key = `${metric}_rating` as keyof PerformanceRatingData;
                                return (
                                    <div key={metric} className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">{metric}</label>
                                        <div className="flex gap-2">
                                            {[1, 2, 3, 4, 5].map((val) => (
                                                <button
                                                    key={val}
                                                    onClick={() => setRatingData({ ...ratingData, [key]: val })}
                                                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                                                        (ratingData[key] as number) >= val
                                                            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                                                            : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600'
                                                    }`}
                                                >
                                                    {val}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                            
                            <div className="pt-2">
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Additional Comments</label>
                                <textarea 
                                    className="w-full border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 rounded-xl p-3 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                                    rows={3}
                                    placeholder="Leave detailed feedback..."
                                    value={ratingData.performance_comments}
                                    onChange={(e) => setRatingData({...ratingData, performance_comments: e.target.value})}
                                ></textarea>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setRatingTask(null)}
                                className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                            >
                                Skip
                            </button>
                            <button
                                onClick={submitRating}
                                disabled={ratePerformanceMutation.isPending}
                                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-600/20 disabled:opacity-50"
                            >
                                {ratePerformanceMutation.isPending ? 'Saving...' : 'Submit Rating'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
