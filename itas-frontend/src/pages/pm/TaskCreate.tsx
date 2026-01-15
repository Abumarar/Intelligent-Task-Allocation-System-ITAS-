import { useState, type FormEvent } from "react";
import TagInput from "../../components/common/TagInput";
import { api } from "../../api/client";
import { uploadTaskDocument, assignTask } from "../../api/tasks";
import { fetchProjects, type Project } from "../../api/projects";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

type Match = {
  employee_id: string;
  employee_name: string;
  employee_title: string;
  suitability_score: number;
  matching_skills: string[];
  current_workload: number;
};

export default function TaskCreate() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const initialProjectId = location.state?.projectId || "";

  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [priority, setPriority] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");
  const [projectId, setProjectId] = useState(initialProjectId);
  const [startDate, setStartDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [skills, setSkills] = useState<string[]>([]);

  // Fetch projects for dropdown
  const { data: projectsData } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects
  });

  const projects = projectsData || [];
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [msg, setMsg] = useState<{ text: string; tone: "success" | "error" } | null>(null);

  // New state for matches
  const [createdTaskId, setCreatedTaskId] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);

  const clearForm = () => {
    setTitle("");
    setDesc("");
    setPriority("MEDIUM");
    setStartDate("");
    setDueDate("");
    setSkills([]);
    setCreatedTaskId(null);
    setMatches([]);
    setShowSuccess(false);
  };

  const reset = () => {
    clearForm();
    setMsg(null);
  };

  const handleDocumentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAnalyzing(true);
    setMsg(null);
    try {
      const data = await uploadTaskDocument(file);
      if (data.title) setTitle(data.title);
      if (data.description) setDesc(data.description);
      if (data.priority) setPriority(data.priority as "LOW" | "MEDIUM" | "HIGH");
      if (data.dueDate) setDueDate(new Date(data.dueDate).toISOString().split('T')[0]);
      if (data.requiredSkills && data.requiredSkills.length > 0) {
        // Merge with existing skill tags
        const newSkills = Array.from(new Set([...skills, ...data.requiredSkills]));
        setSkills(newSkills);
      }
      setMsg({ text: "Task details auto-filled from document.", tone: "success" });
    } catch (err) {
      console.error(err);
      setMsg({ text: "Failed to analyze document.", tone: "error" });
    } finally {
      setAnalyzing(false);
      // Reset input
      e.target.value = "";
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setMsg(null);
    try {
      const res = await api.post("/tasks/", {
        title,
        description: desc,
        priority,
        requiredSkills: skills,
        start_date: startDate || undefined,
        due_date: dueDate || undefined,
        project_id: projectId || undefined,
      });

      // Capture matches if returned
      const newMatches = res.data.matches || [];
      const newTaskId = res.data.id;

      // Invalidate queries to refresh dashboard
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });

      if (newMatches.length > 0) {
        setMatches(newMatches);
        setCreatedTaskId(newTaskId);
        setShowSuccess(true);
        setMsg({ text: "Task created! Review recommendations below.", tone: "success" });
      } else {
        clearForm();
        setMsg({ text: "Task created successfully.", tone: "success" });
      }

    } catch (err: unknown) {
      let errorMsg = "Failed to create task.";
      if (err && typeof err === 'object' && 'response' in err) {
        errorMsg = (err as { response: { data: { message: string } } }).response.data.message || errorMsg;
      }
      setMsg({ text: errorMsg, tone: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleAssign = async (employeeId: string) => {
    if (!createdTaskId) return;
    try {
      await assignTask(createdTaskId, employeeId);
      setMsg({ text: "Employee assigned successfully!", tone: "success" });
      // Remove assigned match or show status
      setMatches(prev => prev.filter(m => m.employee_id !== employeeId));
      // Provide feedback
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });

      // If no matches left or user wants to proceed
      setTimeout(() => {
        clearForm(); // Reset after assignment
      }, 1500);

    } catch (err) {
      setMsg({ text: "Failed to assign task.", tone: "error" });
    }
  };

  if (showSuccess) {
    return (
      <div className="page">
        <div className="max-w-3xl mx-auto w-full">
          <div className="mb-8 text-center">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold mb-2">Task Created Successfully</h1>
            <p className="text-slate-500">We found the best matches for this task based on skills and workload.</p>
          </div>

          <div className="card">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center">
              <h2 className="font-semibold text-lg">Recommended Employees</h2>
              <button onClick={clearForm} className="text-sm text-slate-500 hover:text-indigo-600 font-medium">
                Skip & Create Another
              </button>
            </div>
            <div className="divide-y divide-slate-100">
              {matches.map(match => (
                <div key={match.employee_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center">
                      {match.employee_name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900">{match.employee_name}</h3>
                        <span className="text-xs text-slate-400">{match.employee_title}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-100">
                          {Math.round(match.suitability_score)}% Match
                        </div>
                        <div className="text-xs text-slate-400">
                          {100 - Math.round(match.current_workload)}% Available
                        </div>
                      </div>
                      {match.matching_skills.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {match.matching_skills.slice(0, 3).map(skill => (
                            <span key={skill} className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded border border-slate-200">
                              {skill}
                            </span>
                          ))}
                          {match.matching_skills.length > 3 && (
                            <span className="text-[10px] text-slate-400 self-center">+{match.matching_skills.length - 3}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleAssign(match.employee_id)}
                    className="btn btn-sm btn-outline hover:bg-indigo-600 hover:text-white hover:border-indigo-600 transition-colors"
                  >
                    Assign
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-hero">
        <div>
          <div className="eyebrow">New assignment</div>
          <h1 className="page-title">Create task</h1>
          <p className="lead">
            Define the task, clarify requirements, and tag the skills you need.
          </p>
        </div>

        <div className="card px-4 py-3 bg-indigo-50 border border-indigo-100 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-indigo-900">Have a job description?</h3>
              <p className="text-xs text-indigo-700">Upload a PDF to auto-fill details.</p>
            </div>
          </div>
          <label className={`btn btn-sm bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 shadow-sm ${analyzing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
            <input
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={handleDocumentUpload}
              disabled={analyzing}
            />
            {analyzing ? "Analyzing..." : "Upload & Fill"}
          </label>
        </div>
      </div>

      <div className="form-layout">
        <form className="form-column" onSubmit={submit}>
          <section className="card form-section">
            <div className="section-header">
              <h2 className="section-title">Task details</h2>
              <p className="section-desc">
                Give the team a clear brief and expected outcomes.
              </p>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="title">
                Title
              </label>
              <input
                id="title"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Customer onboarding workflow update"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="description">
                Description
              </label>
              <textarea
                id="description"
                className="textarea"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Include scope, dependencies, and desired deliverables."
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="project">
                Project
              </label>
              <select
                id="project"
                className="select"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              >
                <option value="">No Project (Uncategorized)</option>
                {projects.map((p: Project) => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            </div>
          </section>

          <section className="card form-section">
            <div className="section-header">
              <h2 className="section-title">Timeline</h2>
              <p className="section-desc">Set the schedule for this task.</p>
            </div>
            <div className="flex gap-4">
              <div className="field flex-1">
                <label className="field-label" htmlFor="startDate">Start Date</label>
                <input
                  id="startDate"
                  type="date"
                  className="input"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div className="field flex-1">
                <label className="field-label" htmlFor="dueDate">Due Date</label>
                <input
                  id="dueDate"
                  type="date"
                  className="input"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
            </div>
          </section>

          <section className="card form-section">
            <div className="section-header">
              <h2 className="section-title">Skill requirements</h2>
              <p className="section-desc">
                Add the skills ITAS should prioritize for matching.
              </p>
            </div>
            <TagInput value={skills} onChange={setSkills} />
          </section>

          {msg && (
            <div className="alert" data-tone={msg.tone}>
              {msg.text}
            </div>
          )}

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving || !title.trim()}
            >
              {saving ? "Saving..." : "Create task"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={reset}>
              Reset form
            </button>
          </div>
        </form>

        <aside className="form-aside">
          <div className="card form-section">
            <div className="section-header">
              <h2 className="section-title">Priority</h2>
              <p className="section-desc">
                Highlight urgency and communicate expected impact.
              </p>
            </div>
            <div className="field">
              <label className="field-label" htmlFor="priority">
                Task priority
              </label>
              <select
                id="priority"
                className="select"
                value={priority}
                onChange={(e) => setPriority(e.target.value as "LOW" | "MEDIUM" | "HIGH")}
              >
                <option value="LOW">Low priority</option>
                <option value="MEDIUM">Medium priority</option>
                <option value="HIGH">High priority</option>
              </select>
            </div>
            <div className="priority-hint">
              Current selection: <span className={`badge ${priority === "HIGH" ? "priority-high" : priority === "MEDIUM" ? "priority-medium" : "priority-low"}`}>{priority}</span>
            </div>
          </div>

          <div className="card form-section">
            <div className="section-header">
              <h2 className="section-title">Guidelines</h2>
              <p className="section-desc">
                Strong task briefs lead to better recommendations.
              </p>
            </div>
            <div className="checklist">
              <div className="check-item">Clarify deliverables and success criteria.</div>
              <div className="check-item">List dependencies and key stakeholders.</div>
              <div className="check-item">Add skills that are truly required.</div>
              <div className="check-item">Use priority to signal urgency, not complexity.</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
