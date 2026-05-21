import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/hooks";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "../../api/dashboard";
import { fetchTasks as fetchTasksList, type Task, type TaskMatch } from "../../api/tasks";

const insights = [
  "Two tasks waiting on scope clarity from stakeholders.",
  "CV parsing queue shows three profiles in progress.",
  "Weekly allocation review scheduled for Thursday.",
];

const priorityClass = (priority: string) => {
  if (priority === "HIGH") return "priority-high";
  if (priority === "MEDIUM") return "priority-medium";
  return "priority-low";
};

export default function PMDashboard() {
  const { user } = useAuth();

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
  });

  // ✅ FIX: wrap fetchTasksList so it matches React Query's expected queryFn signature
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => fetchTasksList(),
  });

  const stats = statsData
    ? [
      { label: "Active tasks", value: String(statsData.active_tasks ?? 0), meta: "Currently assigned", tone: "accent-teal" },
      { label: "Unassigned", value: String(statsData.unassigned_tasks ?? 0), meta: "Need allocation", tone: "accent-clay" },
      { label: "Employee capacity", value: `${Math.round(statsData.employee_capacity ?? 0)}%`, meta: "Average workload", tone: "accent-sun" },
      { label: "Skills coverage", value: `${Math.round(statsData.skills_coverage ?? 0)}%`, meta: "Task coverage", tone: "accent-teal" },
    ]
    : [
      { label: "Active tasks", value: "0", meta: "Loading...", tone: "accent-teal" },
      { label: "Unassigned", value: "0", meta: "Loading...", tone: "accent-clay" },
      { label: "Employee capacity", value: "0%", meta: "Loading...", tone: "accent-sun" },
      { label: "Skills coverage", value: "0%", meta: "Loading...", tone: "accent-teal" },
    ];

  const tasks = tasksData
    ? tasksData.slice(0, 3).map((task: Task) => ({
      title: task.title,
      priority: task.priority,
      due: task.due_date ? `Due ${new Date(task.due_date).toLocaleDateString()}` : "No due date",
      skills: task.requiredSkills || [],
    }))
    : [];

  const focusAreas = statsData
    ? [
      { label: "Skill coverage", value: `${Math.round(statsData.skills_coverage ?? 0)}%`, meta: "Task coverage", progress: Math.round(statsData.skills_coverage ?? 0) },
      { label: "Capacity balance", value: `${Math.round(statsData.employee_capacity ?? 0)}%`, meta: "Average workload", progress: Math.round(statsData.employee_capacity ?? 0) },
      { label: "On-time risk", value: "21%", meta: "Low risk", progress: 21 },
    ]
    : [
      { label: "Skill coverage", value: "0%", meta: "Loading...", progress: 0 },
      { label: "Capacity balance", value: "0%", meta: "Loading...", progress: 0 },
      { label: "On-time risk", value: "0%", meta: "Loading...", progress: 0 },
    ];

  const matches: TaskMatch[] = []; // Will be populated when tasks have matches

  const getGreeting = () => {
    const hour = new Date().getHours();
    // 6 AM to 12 PM -> Good morning
    // Else (12 PM to 6 AM) -> Good evening
    if (hour >= 6 && hour < 12) return "Good morning";
    return "Good evening";
  };

  if (statsLoading || tasksLoading) {
    return (
      <div className="page">
        <div className="card">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-hero">
        <div>
          <div className="eyebrow">PM Dashboard</div>
          <h1 className="page-title">
            {getGreeting()}{user?.name ? `, ${user.name}` : ""}.
          </h1>
          <p className="lead">
            Track allocation, capacity, and skill coverage across your team.
          </p>
        </div>
        <div className="hero-actions">
          <NavLink to="/pm/tasks/new" className="btn btn-primary">
            Create task
          </NavLink>
          <NavLink to="/pm/employees" className="btn btn-outline">
            Review employees
          </NavLink>
        </div>
      </div>

      <div className="stat-grid">
        {stats.map((stat, index) => (
          <div
            key={stat.label}
            className={`stat-card card ${stat.tone} reveal delay-${index + 1}`}
          >
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-meta">{stat.meta}</div>
          </div>
        ))}
      </div>

      <div className="split-grid">
        <section className="card reveal delay-1">
          <div className="card-header">
            <div>
              <h2 className="card-title">Priority queue</h2>
              <p className="card-subtitle">
                Focus items that need assignments this week.
              </p>
            </div>
            <span className="badge">This week</span>
          </div>
          <div className="task-list">
            {tasks.length > 0 ? (
              tasks.map((task) => (
                <div className="task-item" key={task.title}>
                  <div>
                    <div className="task-title">{task.title}</div>
                    <div className="task-meta">{task.due}</div>
                    <div className="tag-list">
                      {task.skills.map((skill) => (
                        <span key={skill} className="tag">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className={`badge ${priorityClass(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
              ))
            ) : (
              <div className="muted">No tasks yet. Create your first task to get started.</div>
            )}
          </div>
        </section>

        <section className="card reveal delay-2">
          <div className="card-header">
            <div>
              <h2 className="card-title">Allocation focus</h2>
              <p className="card-subtitle">
                Balance skills, bandwidth, and delivery confidence.
              </p>
            </div>
          </div>
          <div className="focus-list">
            {focusAreas.map((area) => (
              <div key={area.label} className="focus-item">
                <div className="focus-top">
                  <div>
                    <div className="focus-label">{area.label}</div>
                    <div className="focus-meta">{area.meta}</div>
                  </div>
                  <div className="focus-value">{area.value}</div>
                </div>
                <div className="progress">
                  <div className="progress-bar" style={{ width: `${area.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid-2">
        <section className="card reveal delay-1">
          <div className="card-header">
            <div>
              <h2 className="card-title">Recommended matches</h2>
              <p className="card-subtitle">
                High-fit employees based on required skills.
              </p>
            </div>
            <span className="badge status-ready">Live</span>
          </div>
          <div className="match-list">
            {matches.length > 0 ? (
              matches.map((match) => (
                <div key={match.employee_id} className="match-item">
                  <div>
                    <div className="match-name">{match.employee_name}</div>
                    <div className="match-meta">
                      {match.employee_title} - {Math.round(match.suitability_score)}%
                    </div>
                  </div>
                  <div className="tag-list">
                    {match.matching_skills.map((skill) => (
                      <span key={skill} className="tag">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="muted">No matches available. Create tasks to see recommendations.</div>
            )}
          </div>
        </section>

        <section className="card reveal delay-2">
          <div className="card-header">
            <div>
              <h2 className="card-title">Next steps</h2>
              <p className="card-subtitle">
                Quick actions to keep allocations moving.
              </p>
            </div>
          </div>
          <div className="insight-list">
            {insights.map((insight) => (
              <div key={insight} className="insight-item">
                {insight}
              </div>
            ))}
          </div>
          <div className="callout">
            Create a new task or update employee skills to improve matching.
          </div>
        </section>
      </div>
    </div>
  );
}
