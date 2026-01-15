
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../auth/hooks";
import { fetchProjects, createProject, deleteProject, type Project } from "../../api/projects";


export default function Projects() {
    const { user } = useAuth();
    const qc = useQueryClient();

    // Create Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({ title: "", description: "" });
    const [submitting, setSubmitting] = useState(false);
    const [msg, setMsg] = useState<{ text: string; tone: "error" | "success" } | null>(null);

    // Delete Modal State
    const [deleteId, setDeleteId] = useState<string | null>(null);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [deleting, setDeleting] = useState(false);

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

    const deleteMutation = useMutation({
        mutationFn: deleteProject,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["projects"] });
            setIsDeleteModalOpen(false);
            setDeleteId(null);
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

    const handleDeleteClick = (e: React.MouseEvent, id: string) => {
        e.preventDefault();
        e.stopPropagation(); // Prevent navigation
        setDeleteId(id);
        setIsDeleteModalOpen(true);
    };

    const confirmDelete = () => {
        if (!deleteId) return;
        setDeleting(true);
        deleteMutation.mutate(deleteId, {
            onSettled: () => setDeleting(false)
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
                    <h1 className="page-title text-slate-900 dark:text-white">Projects</h1>
                    <p className="lead mt-2 text-slate-500 dark:text-slate-400">Oversee all active initiatives and their progress.</p>
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
                    <div className="col-span-full border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-300 dark:text-slate-600 text-3xl mb-4">📂</div>
                        <h3 className="text-lg font-bold text-slate-700 dark:text-slate-200">No projects yet</h3>
                        <p className="text-slate-500 dark:text-slate-400 mt-1 max-w-sm">Create your first project to start tracking tasks and assignments.</p>
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
                    projectList.map((project: Project) => (
                        <div key={project.id} className="relative group">
                            <Link
                                to={`/pm/projects/${project.id}`}
                                className="card group-hover:border-indigo-300 dark:group-hover:border-indigo-700 transition-all hover:shadow-lg hover:-translate-y-1 block h-full flex flex-col"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border ${getStatusColor(project.status)}`}>
                                        {project.status}
                                    </div>
                                    <span className="text-xs text-slate-400">
                                        {new Date(project.updated_at).toLocaleDateString()}
                                    </span>
                                </div>

                                <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2 group-hover:text-indigo-700 dark:group-hover:text-indigo-400 transition-colors">
                                    {project.title}
                                </h3>

                                <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-3 mb-6 flex-1">
                                    {project.description || "No description provided."}
                                </p>

                                <div className="mt-auto">
                                    <div className="flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-300 mb-2">
                                        <span>Progress</span>
                                        <span>{project.completed_task_count} / {project.task_count} Tasks</span>
                                    </div>
                                    <div className="h-2 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-indigo-500 rounded-full"
                                            style={{ width: `${project.task_count > 0 ? (project.completed_task_count / project.task_count) * 100 : 0}%` }}
                                        />
                                    </div>
                                </div>
                            </Link>

                            {user?.role === "PM" && (
                                <button
                                    onClick={(e) => handleDeleteClick(e, project.id)}
                                    className="absolute top-4 right-4 p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                    title="Delete Project"
                                >
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Create Project Modal */}
            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="modal card w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4 dark:text-white">Create New Project</h2>
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

            {/* Delete Confirmation Modal */}
            {isDeleteModalOpen && (
                <div className="modal-overlay">
                    <div className="modal card w-full max-w-sm text-center p-6">
                        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white">Delete Project?</h2>
                        <p className="text-slate-500 dark:text-slate-400 mb-6">
                            This action cannot be undone. All tasks within this project will be deleted or unassigned.
                        </p>
                        <div className="flex justify-center gap-3">
                            <button
                                className="btn btn-ghost"
                                onClick={() => setIsDeleteModalOpen(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn bg-red-600 text-white hover:bg-red-700 border-transparent shadow-lg shadow-red-600/20"
                                onClick={confirmDelete}
                                disabled={deleting}
                            >
                                {deleting ? "Deleting..." : "Delete Project"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
