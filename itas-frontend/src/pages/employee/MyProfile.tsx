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
              <div className="profile-role">Individual Contributor</div>
            </div>
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
                <div key={task.id} className="task-item">
                  <div>
                    <div className="task-title">{task.title}</div>
                    <div className="task-meta">
                      {task.due_date ? `Due ${new Date(task.due_date).toLocaleDateString()}` : "No due date"}
                    </div>
                  </div>
                  <span className="badge status-processing cursor-pointer hover:bg-opacity-80" onClick={() => openTaskUpdate(task)}>
                    {task.status}
                  </span>
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
              <div className={`mt-3 text-sm ${uploadMsg.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                {uploadMsg.text}
              </div>
            )}
            {profileData?.employee?.cvUpdatedAt && (
              <div className="mt-2 text-xs text-center text-slate-400">
                Last updated: {new Date(profileData.employee.cvUpdatedAt).toLocaleDateString()}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Edit Profile Modal */}
      {isEditProfileOpen && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Edit Profile</h3>
            <div className="py-4 space-y-4">
              <div className="form-control">
                <label className="label">Name</label>
                <input
                  type="text"
                  className="input input-bordered w-full"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>
              <div className="form-control">
                <label className="label">Title</label>
                <input
                  type="text"
                  className="input input-bordered w-full"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-action">
              <button className="btn" onClick={() => setIsEditProfileOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUpdateProfile}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Task Update Modal */}
      {selectedTask && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Update Progress: {selectedTask.title}</h3>
            <div className="py-4 space-y-4">
              <div className="form-control">
                <label className="label">Status</label>
                <select
                  className="select select-bordered w-full"
                  value={taskStatus}
                  onChange={(e) => setTaskStatus(e.target.value as any)}
                >
                  <option value="ASSIGNED">Assigned</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="BLOCKED">Blocked</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>
              <div className="form-control">
                <label className="label">Notes</label>
                <textarea
                  className="textarea textarea-bordered w-full"
                  placeholder="Add progress notes..."
                  value={taskNotes}
                  onChange={(e) => setTaskNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-action">
              <button className="btn" onClick={() => setSelectedTask(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUpdateTask}>Update</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
