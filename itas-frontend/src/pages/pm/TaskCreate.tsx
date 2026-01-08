import { useState, type FormEvent } from "react";
import TagInput from "../../components/common/TagInput";
import { api } from "../../api/client";
import { useQueryClient } from "@tanstack/react-query";

export default function TaskCreate() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [priority, setPriority] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");
  const [skills, setSkills] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
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
