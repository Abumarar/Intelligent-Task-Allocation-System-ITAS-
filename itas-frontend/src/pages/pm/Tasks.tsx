
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchTasks, updateTask, assignTask, type Task } from "../../api/tasks";
import { fetchEmployees } from "../../api/employees";

// Define TaskStatus type for type safety
type TaskStatus = "DRAFT" | "UNASSIGNED" | "ASSIGNED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

const COLUMNS: { id: string; title: string; statuses: TaskStatus[]; color: string; bgGradient: string }[] = [
    { id: "todo", title: "To Do", statuses: ["DRAFT", "UNASSIGNED"], color: "text-gray-400", bgGradient: "from-gray-500/10 to-transparent" },
    { id: "assigned", title: "Assigned", statuses: ["ASSIGNED"], color: "text-blue-400", bgGradient: "from-blue-500/10 to-transparent" },
    { id: "inprogress", title: "In Progress", statuses: ["IN_PROGRESS"], color: "text-amber-400", bgGradient: "from-amber-500/10 to-transparent" },
    { id: "done", title: "Done", statuses: ["COMPLETED"], color: "text-emerald-400", bgGradient: "from-emerald-500/10 to-transparent" },
];

export default function Tasks() {
    const queryClient = useQueryClient();

    // Fetch tasks
    const { data: tasks, isLoading: isLoadingTasks } = useQuery({
        queryKey: ["tasks"],
        queryFn: () => fetchTasks(),
    });

    // Fetch employees for assignment (limit 100 to get all)
    const { data: employeesData } = useQuery({
        queryKey: ["employees"],
        queryFn: () => fetchEmployees({ limit: 100 }),
    });

    const employees = employeesData || [];

    // Update Task Mutation
    const updateTaskMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) => updateTask(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
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
            case "HIGH": return "bg-red-500/10 text-red-400 border-red-500/20";
            case "MEDIUM": return "bg-amber-500/10 text-amber-400 border-amber-500/20";
            case "LOW": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
            default: return "bg-white/5 text-gray-400 border-white/10";
        }
    };

    // Group tasks by column
    const getTasksByColumn = (columnId: string) => {
        const column = COLUMNS.find(c => c.id === columnId);
        if (!column) return [];
        return tasks?.filter(t => column.statuses.includes(t.status as TaskStatus)) || [];
    };

    if (isLoadingTasks) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="h-[calc(100vh-4rem)] flex flex-col p-8 overflow-hidden bg-gradient-to-br from-[#0f1117] via-[#13161c] to-[#0f1117]">
            {/* Header */}
            <div className="flex justify-between items-end mb-8 relative z-10">
                <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight mb-2">Canban Board</h1>
                    <p className="text-secondary/70 text-sm font-medium">Manage your team's workflow with precision.</p>
                </div>
                <Link to="/pm/tasks/new" className="group relative px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-medium shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-300 overflow-hidden">
                    <span className="relative z-10 flex items-center gap-2">
                        <svg className="w-5 h-5 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        New Task
                    </span>
                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                </Link>
            </div>

            {/* Board */}
            <div className="flex gap-6 overflow-x-auto h-full pb-4 custom-scrollbar snap-x snap-mandatory">
                {COLUMNS.map((col) => (
                    <div key={col.id} className="snap-center w-[360px] flex-shrink-0 flex flex-col rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm overflow-hidden transition-colors duration-300 hover:bg-white/[0.04]">

                        {/* Column Header */}
                        <div className={`p-4 flex items-center justify-between border-b border-white/5 bg-gradient-to-b ${col.bgGradient}`}>
                            <div className="flex items-center gap-3">
                                <div className={`w-2 h-2 rounded-full ring-2 ring-current ${col.color}`} />
                                <h2 className="font-semibold text-white tracking-wide">{col.title}</h2>
                            </div>
                            <span className="bg-white/5 text-xs font-mono px-2.5 py-0.5 rounded-full text-secondary/80 border border-white/5">
                                {getTasksByColumn(col.id).length}
                            </span>
                        </div>

                        {/* Tasks Container */}
                        <div className="p-3 flex-1 overflow-y-auto space-y-3 custom-scrollbar">
                            {getTasksByColumn(col.id).length === 0 ? (
                                <div className="h-24 flex items-center justify-center text-white/10 text-sm font-light italic border-2 border-dashed border-white/5 rounded-xl mx-2 mt-2">
                                    Empty
                                </div>
                            ) : (
                                getTasksByColumn(col.id).map((task) => (
                                    <div key={task.id} className="group relative bg-[#1e2330]/60 p-4 rounded-xl border border-white/5 shadow-sm hover:shadow-lg hover:border-primary/30 hover:-translate-y-0.5 transition-all duration-300 backdrop-blur-md">

                                        {/* Colored Glow on Hover */}
                                        <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl pointer-events-none" />

                                        {/* Priority & Due Date */}
                                        <div className="flex justify-between items-start mb-3 relative z-10">
                                            <span className={`text-[10px] px-2.5 py-1 rounded-md border font-semibold uppercase tracking-wider ${getPriorityStyle(task.priority)}`}>
                                                {task.priority}
                                            </span>
                                            {task.due_date && (
                                                <div className="flex items-center gap-1.5 text-[11px] text-secondary group-hover:text-white/80 transition-colors">
                                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                    </svg>
                                                    {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                </div>
                                            )}
                                        </div>

                                        {/* Title */}
                                        <h3 className="text-white font-medium text-[15px] mb-2 leading-relaxed group-hover:text-primary-light transition-colors relative z-10">{task.title}</h3>

                                        {/* Skills */}
                                        {task.requiredSkills && task.requiredSkills.length > 0 && (
                                            <div className="flex flex-wrap gap-1.5 mb-4 relative z-10">
                                                {task.requiredSkills.slice(0, 3).map(skill => (
                                                    <span key={skill} className="text-[10px] bg-white/5 text-secondary px-2 py-0.5 rounded border border-white/5 group-hover:border-white/10 transition-colors">
                                                        {skill}
                                                    </span>
                                                ))}
                                                {task.requiredSkills.length > 3 && (
                                                    <span className="text-[10px] text-secondary px-1 py-0.5">+{task.requiredSkills.length - 3}</span>
                                                )}
                                            </div>
                                        )}

                                        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-3" />

                                        {/* Actions */}
                                        <div className="flex items-center justify-between gap-3 relative z-10">
                                            {/* Status Select - Styled */}
                                            <div className="relative flex-shrink-0">
                                                <select
                                                    className="appearance-none bg-black/40 text-xs text-secondary/90 rounded-lg pl-2 pr-6 py-1.5 border border-white/10 outline-none focus:border-primary/50 focus:text-white transition-all cursor-pointer hover:bg-black/60 w-[100px]"
                                                    value={task.status}
                                                    onChange={(e) => handleStatusChange(task.id, e.target.value as TaskStatus)}
                                                >
                                                    <option value="DRAFT">Draft</option>
                                                    <option value="UNASSIGNED">Unassigned</option>
                                                    <option value="ASSIGNED">Assigned</option>
                                                    <option value="IN_PROGRESS">In Progress</option>
                                                    <option value="COMPLETED">Done</option>
                                                    <option value="CANCELLED">X</option>
                                                </select>
                                                <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-secondary/50">
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                    </svg>
                                                </div>
                                            </div>

                                            {/* Assignee - Visual/Select */}
                                            <div className="relative flex-1 min-w-0">
                                                <div className="relative">
                                                    <select
                                                        className={`appearance-none w-full text-xs rounded-lg pl-8 pr-6 py-1.5 border outline-none focus:border-primary/50 transition-all cursor-pointer text-right ${task.assigned_to
                                                            ? "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
                                                            : "bg-black/40 text-secondary/70 border-white/10 hover:bg-black/60"
                                                            }`}
                                                        value={task.assigned_to || ""}
                                                        onChange={(e) => handleAssign(task.id, e.target.value)}
                                                    >
                                                        <option value="" disabled>Assign...</option>
                                                        {employees.map((emp) => (
                                                            <option key={emp.id} value={emp.id}>
                                                                {emp.name}
                                                            </option>
                                                        ))}
                                                    </select>

                                                    {/* Avatar / Icon Overlay */}
                                                    <div className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                                        {task.assigned_to ? (
                                                            <div className="w-5 h-5 rounded-full bg-primary text-[9px] font-bold text-white flex items-center justify-center">
                                                                {/* Simple initials logic or icon */}
                                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                                </svg>
                                                            </div>
                                                        ) : (
                                                            <svg className="w-4 h-4 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                                            </svg>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
