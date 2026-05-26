import { useState } from "react";
import { useAuth } from "../../auth/hooks";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchMyProfile } from "../../api/profile";
import { uploadEmployeeCV, updateEmployee } from "../../api/employees";
import { updateTaskProgress, type TaskStatus } from "../../api/tasks";



export default function MyProfile() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Edit Profile State
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editTitle, setEditTitle] = useState("");

  // Task Progress State
  const [selectedTask, setSelectedTask] = useState<{ id: string, title: string, status: string, notes?: string } | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus>("IN_PROGRESS");
  const [taskNotes, setTaskNotes] = useState("");

  const { data: profileData, isLoading, error } = useQuery({
    queryKey: ["my-profile"],
    queryFn: fetchMyProfile,
  });

  const handleCVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !profileData?.employee?.id) return;

    setUploading(true);
    setUploadMsg(null);
    try {
      await uploadEmployeeCV(profileData.employee.id, file);
      setUploadMsg({ type: "success", text: "CV uploaded! Skills will update shortly." });
      // Refresh profile to see status change
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    } catch (err) {
      console.error(err);
      setUploadMsg({ type: "error", text: "Failed to upload CV." });
    } finally {
      setUploading(false);
      e.target.value = ""; // Reset input
    }
  };

  const openEditProfile = () => {
    if (profileData?.employee) {
      setEditName(profileData.employee.name);
      setEditTitle(profileData.employee.title || "");
      setIsEditProfileOpen(true);
    }
  };

  const handleUpdateProfile = async () => {
    if (!profileData?.employee?.id) return;
    try {
      await updateEmployee(profileData.employee.id, { name: editName, title: editTitle });
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
      setIsEditProfileOpen(false);
    } catch (err) {
      console.error("Failed to update profile", err);
      alert("Failed to update profile");
    }
  };

  const openTaskUpdate = (task: any) => {
    setSelectedTask(task);
    setTaskStatus(task.status);
    setTaskNotes(task.notes || "");
  };

  const handleUpdateTask = async () => {
    if (!selectedTask) return;
    try {
      await updateTaskProgress(selectedTask.id, taskStatus, taskNotes);
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
      setSelectedTask(null);
    } catch (err) {
      console.error("Failed to update task", err);
      alert("Failed to update task progress");
    }
  };

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
              <div className="profile-role">{profileData?.employee?.title || "Individual Contributor"}</div>
            </div>
            <button className="btn btn-sm btn-outline ml-auto" onClick={openEditProfile}>
              Edit
            </button>
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
                <div key={task.id} className="task-item flex flex-col items-start gap-2 bg-white dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-all hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-800">
                  <div className="flex justify-between items-start w-full mb-1">
                    <div className="task-title text-lg font-bold text-slate-800 dark:text-white leading-tight">
                        {task.title}
                    </div>
                    <span 
                      className={`badge cursor-pointer hover:bg-opacity-80 ml-3 shrink-0 uppercase text-[10px] tracking-wider px-2 py-1 ${task.status === 'COMPLETED' ? 'status-success' : task.status === 'BLOCKED' ? 'status-error' : 'status-processing'}`} 
                      onClick={() => openTaskUpdate(task)}
                    >
                      {task.status.replace("_", " ")}
                    </span>
                  </div>
                  
                  <div className="task-desc text-sm text-slate-600 dark:text-slate-300 w-full mb-2">
                    {task.description || "No description provided."}
                  </div>
                  
                  <div className="task-meta flex items-center gap-2 mt-auto pt-2 w-full border-t border-slate-100 dark:border-slate-700/50 text-xs font-medium text-slate-500 dark:text-slate-400">
                    <svg className="w-4 h-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {task.due_date ? `Due ${new Date(task.due_date).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}` : "No due date"}
                  </div>
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
              <h2 className="card-title">CV & Portfolio</h2>
              <p className="card-subtitle">Upload your CV to auto-extract skills.</p>
            </div>
            {profileData?.employee?.cvStatus && (
              <span className={`badge ${profileData.employee.cvStatus === 'READY' ? 'status-success' :
                profileData.employee.cvStatus === 'FAILED' ? 'status-error' :
                  'status-processing'
                }`}>
                {profileData.employee.cvStatus}
              </span>
            )}
          </div>

          <div className="p-4">
            <label className={`btn btn-outline w-full ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={handleCVUpload}
                disabled={uploading}
              />
              {uploading ? "Uploading..." : "Upload New CV"}
            </label>
            {uploadMsg && (
              <div className={`mt-3 text-sm ${uploadMsg.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {uploadMsg.text}
              </div>
            )}
            {profileData?.employee?.cvUpdatedAt && (
              <div className="mt-2 text-xs text-center text-slate-400 dark:text-slate-500">
                Last updated: {new Date(profileData.employee.cvUpdatedAt).toLocaleDateString()}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Edit Profile Modal */}
      {isEditProfileOpen && (
        <div className="modal-overlay">
          <div className="modal card">
            <h2 className="card-title">Edit Profile</h2>
            <div className="form-section">
              <div className="field">
                <label className="field-label">Name</label>
                <input
                  type="text"
                  className="input"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>
              <div className="field">
                <label className="field-label">Title</label>
                <input
                  type="text"
                  className="input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                />
              </div>
            </div>
            <div className="form-actions" style={{ marginTop: '16px' }}>
              <button className="btn btn-ghost" onClick={() => setIsEditProfileOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUpdateProfile}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Task Update Modal */}
      {selectedTask && (
        <div className="modal-overlay">
          <div className="modal card">
            <h2 className="card-title">Update Progress: {selectedTask.title}</h2>
            <div className="form-section">
              <div className="field">
                <label className="field-label">Status</label>
                <select
                  className="select"
                  value={taskStatus}
                  onChange={(e) => setTaskStatus(e.target.value as any)}
                >
                  <option value="ASSIGNED">Assigned</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="BLOCKED">Blocked</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>
              <div className="field">
                <label className="field-label">Notes</label>
                <textarea
                  className="textarea"
                  placeholder="Add progress notes..."
                  value={taskNotes}
                  onChange={(e) => setTaskNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="form-actions" style={{ marginTop: '16px' }}>
              <button className="btn btn-ghost" onClick={() => setSelectedTask(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUpdateTask}>Update</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
