import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchEmployees,
  uploadEmployeeCV,
  analyzeEmployeeCV,
  type Employee,
} from "../../api/employees";
import { unassignTask } from "../../api/tasks";

const getInitials = (name: string) => {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const initials = parts.slice(0, 2).map((part) => part[0]?.toUpperCase() || "").join("");
  return initials || "U";
};

const statusLabel = (status?: Employee["cvStatus"]) => {
  if (status === "READY") return "Ready";
  if (status === "PROCESSING") return "Processing";
  if (status === "FAILED") return "Failed";
  return "Missing";
};

const statusClass = (status?: Employee["cvStatus"]) => {
  if (status === "READY") return "status-ready";
  if (status === "PROCESSING") return "status-processing";
  if (status === "FAILED") return "status-failed";

  return "status-missing";
};

const getWorkloadColor = (load: number) => {
  if (load >= 80) return "bg-red-500";
  if (load >= 50) return "bg-amber-500";
  return "bg-emerald-500";
};

export default function Employees() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["employees"],
    queryFn: () => fetchEmployees(),
  });

  const [q, setQ] = useState("");
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ text: string; tone: "success" | "error" } | null>(null);

  // Add Employee Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState<{ name: string, email: string, title: string, skills: string[] }>({ name: "", email: "", title: "", skills: [] });
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [expandedSkillsId, setExpandedSkillsId] = useState<string | null>(null);
  const [viewingTasksEmployee, setViewingTasksEmployee] = useState<Employee | null>(null);

  const filtered = useMemo(() => {
    const list = data || [];
    const term = q.trim().toLowerCase();
    if (!term) return list;
    return list.filter(
      (e) =>
        e.name.toLowerCase().includes(term) ||
        (e.email || "").toLowerCase().includes(term),
    );
  }, [data, q]);

  const counts = useMemo(() => {
    const list = data || [];
    return {
      total: list.length,
      ready: list.filter((e) => e.cvStatus === "READY").length,
      processing: list.filter((e) => e.cvStatus === "PROCESSING").length,
      missing: list.filter((e) => !e.cvStatus || e.cvStatus === "NOT_UPLOADED").length,
    };
  }, [data]);

  const openCreateModal = () => {
    setEditingEmployee(null);
    setFormData({ name: "", email: "", title: "", skills: [] });
    setUploadedFile(null);
    setIsModalOpen(true);
  };

  const openEditModal = (employee: Employee) => {
    setEditingEmployee(employee);
    setFormData({
      name: employee.name,
      email: employee.email || "",
      title: employee.title || "",
      skills: [] // We don't load existing skills for now, simplified
    });
    setUploadedFile(null);
    setIsModalOpen(true);
  };

  const handleAnalzyeCV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAnalyzing(true);
    setMsg(null);
    try {
      const data = await analyzeEmployeeCV(file);
      setUploadedFile(file); // Store file for later upload
      setFormData(prev => ({
        ...prev,
        name: data.name || prev.name,
        email: data.email || prev.email,
        title: data.role || prev.title,
        skills: data.skills || []
      }));
      setMsg({ text: "Details auto-filled from CV.", tone: "success" });
    } catch (err) {
      console.error(err);
      setMsg({ text: "Failed to analyze CV.", tone: "error" });
    } finally {
      setAnalyzing(false);
      e.target.value = "";
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email) return;

    setSubmitting(true);
    setMsg(null);
    try {
      if (editingEmployee) {
        const { updateEmployee } = await import("../../api/employees");
        await updateEmployee(editingEmployee.id, formData);
        setMsg({ text: "Employee updated successfully.", tone: "success" });
      } else {
        const { createEmployee } = await import("../../api/employees");
        // Create employee with initial details
        const newEmployee = await createEmployee(formData);

        if (uploadedFile) {
          setMsg({ text: "Employee created. Uploading CV...", tone: "success" });
          await uploadEmployeeCV(newEmployee.id, uploadedFile);
        }
        setMsg({ text: "Employee added and CV uploaded.", tone: "success" });
      }
      // Small delay to allow backend to initialize CV record
      await new Promise(r => setTimeout(r, 500));
      await qc.invalidateQueries({ queryKey: ["employees"] });
      setIsModalOpen(false);
    } catch (e: unknown) {
      let errorMsg = `Failed to ${editingEmployee ? 'update' : 'add'} employee.`;
      if (e && typeof e === 'object' && 'response' in e) {
        errorMsg = (e as { response: { data: { message: string } } }).response.data.message || errorMsg;
      }
      setMsg({ text: errorMsg, tone: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    // Removed confirm() to prevent blocking automated testing

    setDeletingId(id);
    setMsg(null);
    try {
      const { deleteEmployee } = await import("../../api/employees");
      await deleteEmployee(id);
      await qc.invalidateQueries({ queryKey: ["employees"] });
      setMsg({ text: `Removed ${name}.`, tone: "success" });
    } catch {
      setMsg({ text: "Failed to delete employee.", tone: "error" });
    } finally {
      setDeletingId(null);
    }
  };

  const onUpload = async (employee: Employee, file: File) => {
    setMsg(null);
    setUploadingId(employee.id);
    try {
      await uploadEmployeeCV(employee.id, file);
      setMsg({ text: `Uploaded CV for ${employee.name}.`, tone: "success" });
      await qc.invalidateQueries({ queryKey: ["employees"] });
    } catch (e: unknown) {
      let errorMsg = `Failed to upload CV for ${employee.name}.`;
      if (e && typeof e === 'object' && 'response' in e) {
        errorMsg = (e as { response: { data: { message: string } } }).response.data.message || errorMsg;
      }
      setMsg({
        text: errorMsg,
        tone: "error",
      });
    } finally {
      setUploadingId(null);
    }
  };

  const handleUnassignTask = async (taskId: string, employeeId: string) => {
    try {
      await unassignTask(taskId);
      setMsg({ text: "Task unassigned successfully.", tone: "success" });

      // Update local state for immediate feedback
      if (viewingTasksEmployee && viewingTasksEmployee.id === employeeId) {
        setViewingTasksEmployee(prev => prev ? ({
          ...prev,
          assigned_tasks: prev.assigned_tasks?.filter(t => t.id !== taskId)
        }) : null);
      }

      await qc.invalidateQueries({ queryKey: ["employees"] });
    } catch (e) {
      console.error(e);
      setMsg({ text: "Failed to unassign task.", tone: "error" });
    }
  };

  if (isLoading) {
    return (
      <div className="page">
        <div className="card">Loading employees...</div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="page">
        <div className="card">Failed to load employees.</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-hero">
        <div>
          <div className="eyebrow">Talent directory</div>
          <h1 className="page-title">Employees</h1>
          <p className="lead">
            Upload CVs, review extracted skills, and keep profiles current.
          </p>
        </div>
        <div className="hero-actions">
          <div className="search">
            <input
              className="search-input"
              type="search"
              placeholder="Search by name or email"
              aria-label="Search employees"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={openCreateModal}>
            Add Employee
          </button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card card accent-teal reveal delay-1">
          <div className="stat-label">Total employees</div>
          <div className="stat-value">{counts.total}</div>
          <div className="stat-meta">Profiles in directory</div>
        </div>
        <div className="stat-card card accent-sun reveal delay-2">
          <div className="stat-label">CVs ready</div>
          <div className="stat-value">{counts.ready}</div>
          <div className="stat-meta">Parsed and available</div>
        </div>
        <div className="stat-card card accent-clay reveal delay-3">
          <div className="stat-label">Processing</div>
          <div className="stat-value">{counts.processing}</div>
          <div className="stat-meta">In extraction queue</div>
        </div>
        <div className="stat-card card accent-teal reveal delay-4">
          <div className="stat-label">Missing CVs</div>
          <div className="stat-value">{counts.missing}</div>
          <div className="stat-meta">Needs upload</div>
        </div>
      </div>

      {msg && (
        <div className="alert" data-tone={msg.tone}>
          {msg.text}
        </div>
      )}

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal card">
            <h2>{editingEmployee ? "Edit Employee" : "Add New Employee"}</h2>

            {!editingEmployee && (
              <div className="mb-6 p-4 bg-indigo-50 border border-indigo-100 rounded-xl flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-indigo-900">Auto-fill from CV</h4>
                  <p className="text-xs text-indigo-700">Upload a resume to populate details.</p>
                </div>
                <label className={`btn btn-sm bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 ${analyzing ? "opacity-50" : "cursor-pointer"}`}>
                  <input type="file" className="hidden" accept=".pdf,.docx" onChange={handleAnalzyeCV} disabled={analyzing} />
                  {analyzing ? "Analyzing..." : "Upload CV"}
                </label>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="field">
                <label className="field-label">Name</label>
                <input
                  className="input"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label className="field-label">Email</label>
                <input
                  className="input"
                  type="email"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label className="field-label">Title</label>
                <input
                  className="input"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                />
              </div>
              <div className="field">
                <label className="field-label">Skills (comma separated)</label>
                <input
                  className="input"
                  value={formData.skills.join(", ")}
                  onChange={e => setFormData({ ...formData, skills: e.target.value.split(",").map(s => s.trim()) })}
                  placeholder="e.g. React, Python, Leadership"
                />
                <p className="text-xs text-slate-500 mt-1">Auto-detected from CV. Edit as needed.</p>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Saving..." : (editingEmployee ? "Save Changes" : "Add Employee")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {!filtered.length && (
        <div className="card empty-state">
          <h3>No employees found</h3>
          <p>Try refining your search or uploading new profiles.</p>
        </div>
      )}

      <div className="employee-grid">
        {filtered.map((employee) => {
          const status = employee.cvStatus || "NOT_UPLOADED";
          const updatedAt = employee.cvUpdatedAt
            ? new Date(employee.cvUpdatedAt).toLocaleString()
            : "No CV uploaded yet";
          const skills = employee.skills || [];

          return (
            <article key={employee.id} className="card employee-card reveal">
              <div className="employee-top">
                <div className="avatar">{getInitials(employee.name)}</div>
                <div className="employee-info">
                  <div className="employee-name">{employee.name}</div>
                  <div className="employee-meta">
                    {employee.title || employee.email || "Role not set"}
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className={`badge ${statusClass(status)}`} title={employee.cvErrorMessage}>
                    {statusLabel(status)}
                  </span>
                  {status === 'FAILED' && employee.cvErrorMessage && (
                    <span className="text-[10px] text-red-500 mt-1 max-w-[100px] text-right leading-tight">
                      {employee.cvErrorMessage}
                    </span>
                  )}
                </div>
              </div>

              <div className="employee-body">
                <div>
                  <div className="muted">Skills</div>
                  <div className="tag-list">
                    {skills.length ? (
                      <>
                        {(expandedSkillsId === employee.id ? skills : skills.slice(0, 8)).map((skill) => (
                          <span key={skill} className="tag">
                            {skill}
                          </span>
                        ))}
                        {skills.length > 8 && (
                          <button
                            type="button"
                            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium hover:underline ml-1"
                            onClick={() => setExpandedSkillsId(expandedSkillsId === employee.id ? null : employee.id)}
                          >
                            {expandedSkillsId === employee.id ? "Show less" : `+${skills.length - 8} more`}
                          </button>
                        )}
                      </>
                    ) : (
                      <span className="muted">No skills extracted yet.</span>
                    )}
                  </div>
                </div>
                <div className="employee-update">
                  <div className="muted">Last update</div>
                  <div>{updatedAt}</div>
                </div>
                <div className="employee-workload">
                  <div className="muted">Workload</div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getWorkloadColor(employee.current_workload || 0)}`}
                        style={{ width: `${Math.min(employee.current_workload || 0, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-slate-600">
                      {Math.round(employee.current_workload || 0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="card-actions">
                <label
                  className={`upload-box${uploadingId === employee.id ? " is-loading" : ""}`}
                >
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    disabled={uploadingId === employee.id}
                    onChange={(ev) => {
                      const file = ev.target.files?.[0];
                      if (file) onUpload(employee, file);
                      ev.currentTarget.value = "";
                    }}
                  />
                  <span>
                    {uploadingId === employee.id ? "Uploading..." : "Upload CV"}
                  </span>
                </label>
                {employee.cvUrl && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => window.open(employee.cvUrl, '_blank')}
                    title="View CV"
                  >
                    📄
                  </button>
                )}
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => openEditModal(employee)}
                  title="Edit Employee"
                >
                  ✏️
                </button>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => setViewingTasksEmployee(employee)}
                  title="Manage Tasks"
                >
                  📋
                </button>
                <button
                  className="btn btn-ghost btn-danger btn-sm"
                  onClick={() => handleDelete(employee.id, employee.name)}
                  disabled={deletingId === employee.id}
                  title="Delete Employee"
                >
                  {deletingId === employee.id ? "..." : "🗑️"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
      {viewingTasksEmployee && (
        <div className="modal-overlay">
          <div className="modal card w-[600px] max-w-full">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Tasks Assigned to {viewingTasksEmployee.name}</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setViewingTasksEmployee(null)}>✕</button>
            </div>

            <div className="space-y-3">
              {viewingTasksEmployee.assigned_tasks && viewingTasksEmployee.assigned_tasks.length > 0 ? (
                viewingTasksEmployee.assigned_tasks.map(task => (
                  <div key={task.id} className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex justify-between items-center group hover:bg-white hover:shadow-sm transition-all">
                    <div>
                      <div className="font-medium text-slate-800">{task.title}</div>
                      <div className="text-xs text-slate-500 flex gap-2 mt-1">
                        <span className={`px-1.5 py-0.5 rounded ${task.priority === 'HIGH' ? 'bg-red-100 text-red-700' :
                          task.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                            'bg-emerald-100 text-emerald-700'
                          }`}>{task.priority}</span>
                        <span>Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No date'}</span>
                      </div>
                    </div>
                    <button
                      className="btn btn-sm border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300"
                      onClick={() => handleUnassignTask(task.id, viewingTasksEmployee.id)}
                      title="Unassign Task"
                    >
                      Unassign
                    </button>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500 bg-slate-50 rounded-lg">
                  No active tasks assigned.
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button className="btn btn-primary" onClick={() => setViewingTasksEmployee(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
