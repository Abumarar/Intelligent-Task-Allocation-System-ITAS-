import { useAuth } from "../../auth/hooks";
import { useQuery } from "@tanstack/react-query";
import { fetchMyProfile } from "../../api/profile";

const growthGoals = [
  "Lead a cross-team discovery sprint",
  "Mentor a junior analyst",
  "Complete cloud fundamentals certification",
];

export default function MyProfile() {
  const { user } = useAuth();
  const { data: profileData, isLoading, error } = useQuery({
    queryKey: ["my-profile"],
    queryFn: fetchMyProfile,
  });

  const skills = profileData?.employee?.skills || [];
  const tasks = profileData?.tasks || [];
  const workload = profileData?.workload || 0;

  if (isLoading) {
    return (
      <div className="page">
        <div className="card">Loading profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="card">Failed to load profile.</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-hero">
        <div>
          <div className="eyebrow">Employee space</div>
          <h1 className="page-title">My profile</h1>
          <p className="lead">
            Track your workload, skills, and growth focus in one place.
          </p>
        </div>
      </div>

      <div className="profile-grid">
        <section className="card profile-card">
          <div className="profile-header">
            <div className="avatar">{user?.name ? user.name.slice(0, 2).toUpperCase() : "ME"}</div>
            <div>
              <div className="profile-name">{user?.name || "Employee"}</div>
              <div className="profile-role">Individual Contributor</div>
            </div>
          </div>
          <div className="profile-meta">
            <div>
              <div className="muted">Team</div>
              <div>Customer Experience</div>
            </div>
            <div>
              <div className="muted">Location</div>
              <div>Remote</div>
            </div>
            <div>
              <div className="muted">Availability</div>
              <div>{Math.round(workload)}% capacity</div>
            </div>
          </div>
          <div className="progress">
            <div className="progress-bar" style={{ width: `${workload}%` }} />
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Core skills</h2>
              <p className="card-subtitle">Skills highlighted in recent tasks.</p>
            </div>
            <span className="badge">Updated today</span>
          </div>
          <div className="tag-list">
            {skills.length > 0 ? (
              skills.map((skill) => (
                <span key={skill} className="tag">
                  {skill}
                </span>
              ))
            ) : (
              <span className="muted">No skills extracted yet. Upload a CV to extract skills.</span>
            )}
          </div>
        </section>
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Active tasks</h2>
              <p className="card-subtitle">Assignments on your radar.</p>
            </div>
          </div>
          <div className="task-list">
            {tasks.length > 0 ? (
              tasks.map((task) => (
                <div key={task.id} className="task-item">
                  <div>
                    <div className="task-title">{task.title}</div>
                    <div className="task-meta">
                      {task.due_date ? `Due ${new Date(task.due_date).toLocaleDateString()}` : "No due date"}
                    </div>
                  </div>
                  <span className="badge status-processing">{task.status}</span>
                </div>
              ))
            ) : (
              <div className="muted">No active tasks assigned yet.</div>
            )}
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Growth focus</h2>
              <p className="card-subtitle">Personal development goals.</p>
            </div>
          </div>
          <div className="checklist">
            {growthGoals.map((goal) => (
              <div key={goal} className="check-item">
                {goal}
              </div>
            ))}
          </div>
          <div className="callout">
            Add or update goals during your next 1:1 sync.
          </div>
        </section>
      </div>
    </div>
  );
}
