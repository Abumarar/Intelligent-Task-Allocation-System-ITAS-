
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../auth/hooks";
import { fetchProjects, createProject } from "../../api/projects";


export default function Projects() {
    const { user } = useAuth();
    const qc = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({ title: "", description: "" });
    const [submitting, setSubmitting] = useState(false);
    const [msg, setMsg] = useState<{ text: string; tone: "error" | "success" } | null>(null);

    // Fetch projects
    const { data: projects, isLoading, error } = useQuery({
        queryKey: ["projects"],
        queryFn: fetchProjects,
    });

    const createMutation = useMutation({
        mutationFn: createProject,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["projects"] });
            setIsModalOpen(false);
            setFormData({ title: "", description: "" });
            setMsg(null);
        },
        onError: (err: any) => {
            const message = err.response?.data?.detail || err.message || "Failed to create project.";
            setMsg({ text: message, tone: "error" });
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title) return;
        setSubmitting(true);
        setMsg(null);
        createMutation.mutate(formData, {
            onSettled: () => setSubmitting(false)
        });
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "ACTIVE": return "bg-emerald-100 text-emerald-700 border-emerald-200";
            case "COMPLETED": return "bg-blue-100 text-blue-700 border-blue-200";
            default: return "bg-slate-100 text-slate-700 border-slate-200";
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-indigo-600/20 border-t-indigo-600 rounded-full animate-spin" />
                    <p className="text-slate-500 font-medium animate-pulse">Loading projects...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page">
                <div className="alert" data-tone="error">Failed to load projects.</div>
            </div>
        );
    }

    const projectList = projects || [];

    return (
        <div className="page">
            <div className="page-hero">
                <div>
                    <div className="eyebrow text-indigo-600 font-bold tracking-wider mb-2">PORTFOLIO</div>
                    <h1 className="page-title text-slate-900">Projects</h1>
                    <p className="lead mt-2">Oversee all active initiatives and their progress.</p>
                </div>
                {user?.role === "PM" && (
                    <button
                        className="btn btn-primary"
                        onClick={() => setIsModalOpen(true)}
                    >
                        + New Project
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projectList.length === 0 ? (
                    <div className="col-span-full border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 text-3xl mb-4">📂</div>
                        <h3 className="text-lg font-bold text-slate-700">No projects yet</h3>
                        <p className="text-slate-500 mt-1 max-w-sm">Create your first project to start tracking tasks and assignments.</p>
                        {user?.role === "PM" && (
                            <button
                                className="btn btn-outline mt-6"
                                onClick={() => setIsModalOpen(true)}
                            >
                                Create Project
                            </button>
                        )}
                    </div>
                ) : (
                    projectList.map(project => (
                        <Link
                            key={project.id}
                            to={`/pm/projects/${project.id}`}
                            className="card group hover:border-indigo-300 transition-all hover:shadow-lg hover:-translate-y-1 block h-full flex flex-col"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border ${getStatusColor(project.status)}`}>
                                    {project.status}
                                </div>
                                <span className="text-xs text-slate-400">
                                    {new Date(project.updated_at).toLocaleDateString()}
                                </span>
                            </div>

                            <h3 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-indigo-700 transition-colors">
                                {project.title}
                            </h3>

                            <p className="text-sm text-slate-500 line-clamp-3 mb-6 flex-1">
                                {project.description || "No description provided."}
                            </p>

                            <div className="mt-auto">
                                <div className="flex items-center justify-between text-xs font-medium text-slate-600 mb-2">
                                    <span>Progress</span>
                                    <span>{project.completed_task_count} / {project.task_count} Tasks</span>
                                </div>
                                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${project.task_count > 0 ? (project.completed_task_count / project.task_count) * 100 : 0}%` }}
                                    />
                                </div>
                            </div>
                        </Link>
                    ))
                )}
            </div>

            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="modal card w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Create New Project</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="field mb-4">
                                <label className="field-label">Project Title</label>
                                <input
                                    className="input"
                                    value={formData.title}
                                    onChange={e => setFormData({ ...formData, title: e.target.value })}
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className="field mb-6">
                                <label className="field-label">Description</label>
                                <textarea
                                    className="textarea"
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                    rows={3}
                                />
                            </div>

                            {msg && (
                                <div className="alert mb-4" data-tone={msg.tone}>
                                    {msg.text}
                                </div>
                            )}

                            <div className="flex justify-end gap-3">
                                <button
                                    type="button"
                                    className="btn btn-ghost"
                                    onClick={() => setIsModalOpen(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={submitting}
                                >
                                    {submitting ? "Creating..." : "Create Project"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
