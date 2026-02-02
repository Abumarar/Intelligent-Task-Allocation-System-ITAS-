import { useQuery } from "@tanstack/react-query";
import { fetchReports } from "../../api/reports";


export default function Reports() {
    // const { user } = useAuth(); // Not used currently
    const { data: reports, isLoading, error } = useQuery({
        queryKey: ["reports"],
        queryFn: fetchReports,
    });

    if (isLoading) return <div className="page"><div className="card">Loading reports...</div></div>;
    if (error) return <div className="page"><div className="card">Failed to load reports.</div></div>;
    if (!reports) return null;

    return (
        <div className="page">
            <div className="page-hero">
                <div>
                    <div className="eyebrow">Insights</div>
                    <h1 className="page-title">System Reports</h1>
                    <p className="lead">Detailed analysis of tasks, workload, and team performance.</p>
                </div>
            </div>

            <div className="grid-2">
                <section className="card">
                    <div className="card-header">
                        <h2 className="card-title">Task Statistics</h2>
                        <span className="badge">Real-time</span>
                    </div>
                    <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                        <div className="stat-card card accent-teal">
                            <div className="stat-label">Total Tasks</div>
                            <div className="stat-value">{reports.task_stats.total}</div>
                        </div>
                        <div className="stat-card card accent-sun">
                            <div className="stat-label">Completed</div>
                            <div className="stat-value">{reports.task_stats.completed}</div>
                        </div>
                        <div className="stat-card card accent-clay">
                            <div className="stat-label">Assigned</div>
                            <div className="stat-value">{reports.task_stats.assigned}</div>
                        </div>
                        <div className="stat-card card accent-indigo">
                            <div className="stat-label">Completion Rate</div>
                            <div className="stat-value">{reports.task_stats.completion_rate}%</div>
                        </div>
                    </div>
                </section>

                <section className="card">
                    <div className="card-header">
                        <h2 className="card-title">Recent Activity</h2>
                    </div>
                    <div className="callout accent-teal">
                        <div className="stat-value">{reports.recent_assignments}</div>
                        <div className="stat-label">Assignments in last 30 days</div>
                    </div>
                </section>
            </div>

            <section className="card mt-6">
                <div className="card-header">
                    <h2 className="card-title">Workload Distribution</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="table w-full">
                        <thead>
                            <tr>
                                <th>Employee</th>
                                <th>Title</th>
                                <th>Current Load</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reports.workload_distribution.map((emp) => (
                                <tr key={emp.name}>
                                    <td>
                                        <div className="font-bold">{emp.name}</div>
                                    </td>
                                    <td>{emp.title || "N/A"}</td>
                                    <td>
                                        <div className="flex items-center gap-2">
                                            <div className="progress" style={{ width: '100px', height: '6px' }}>
                                                <div className="progress-bar" style={{ width: `${Math.min(100, emp.workload)}%` }} />
                                            </div>
                                            {Math.round(emp.workload)}%
                                        </div>
                                    </td>
                                    <td>
                                        {emp.workload > 80 ? (
                                            <span className="badge status-error">Overloaded</span>
                                        ) : emp.workload > 50 ? (
                                            <span className="badge status-processing">Active</span>
                                        ) : (
                                            <span className="badge status-success">Available</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}
