import { useState, type FormEvent } from "react";
import TagInput from "../../components/common/TagInput";
import { api } from "../../api/client";
import { uploadTaskDocument } from "../../api/tasks";
import { useQueryClient } from "@tanstack/react-query";

export default function TaskCreate() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [priority, setPriority] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");
  const [skills, setSkills] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [msg, setMsg] = useState<{ text: string; tone: "success" | "error" } | null>(null);

  const clearForm = () => {
    setTitle("");
    setDesc("");
    setPriority("MEDIUM");
    setSkills([]);
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
      await api.post("/tasks/", {
        title,
        description: desc,
        priority,
        requiredSkills: skills,
      });
      // Invalidate queries to refresh dashboard immediately
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      clearForm();
      setMsg({ text: "Task created successfully.", tone: "success" });
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
              accept=".pdf"
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
