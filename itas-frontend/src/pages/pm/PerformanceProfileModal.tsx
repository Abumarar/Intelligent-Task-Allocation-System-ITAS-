import { useQuery } from '@tanstack/react-query';
import { getPerformanceProfile } from '../../api/employees';

export default function PerformanceProfileModal({ employeeId, onClose }: { employeeId: string, onClose: () => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['performance-profile', employeeId],
    queryFn: () => getPerformanceProfile(employeeId),
  });

  if (isLoading) {
    return (
      <div className="modal-overlay">
        <div className="modal card w-[800px] max-w-full p-8 text-center">
          Loading performance profile...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="modal-overlay">
        <div className="modal card w-[800px] max-w-full p-8 text-center text-red-500">
          Failed to load performance profile.
          <br/>
          <button className="btn btn-primary mt-4" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  const { metrics, task_history, employee_name } = data;

  const timelineData = [...task_history].reverse().map(task => ({
    name: (task.task_title || "Unknown Task").substring(0, 15) + "...",
    rating: task.performance_rating || 0,
  }));

  return (
    <div className="modal-overlay overflow-y-auto py-10 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm" style={{ zIndex: 1000 }}>
      <div className="modal card w-[1200px] max-w-[95%] xl:max-w-[90%] min-h-[85vh] p-8 md:p-10 relative bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/50 dark:border-slate-700/50 flex flex-col">
        <button className="absolute top-4 right-4 text-slate-500 hover:text-slate-800" onClick={onClose}>✕</button>
        
        <h2 className="text-2xl font-bold mb-6 pr-8">{employee_name}'s Performance Profile</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg flex flex-col justify-center">
            <div className="text-[10px] md:text-xs text-indigo-600 dark:text-indigo-400 font-semibold uppercase tracking-wider mb-1">Reliability Index</div>
            <div className="text-2xl font-bold text-indigo-900 dark:text-indigo-100 truncate">{metrics.reliability_index}%</div>
          </div>
          <div className="p-4 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg flex flex-col justify-center">
            <div className="text-[10px] md:text-xs text-emerald-600 dark:text-emerald-400 font-semibold uppercase tracking-wider mb-1">Consistency</div>
            <div className="text-2xl font-bold text-emerald-900 dark:text-emerald-100 truncate">{metrics.consistency_score}%</div>
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex flex-col justify-center">
            <div className="text-[10px] md:text-xs text-blue-600 dark:text-blue-400 font-semibold uppercase tracking-wider mb-1">Tasks Completed</div>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100 truncate">{metrics.total_completed_tasks}</div>
          </div>
          <div className="p-4 bg-amber-50 dark:bg-amber-900/30 rounded-lg flex flex-col justify-center">
            <div className="text-[10px] md:text-xs text-amber-600 dark:text-amber-400 font-semibold uppercase tracking-wider mb-1">Rated Tasks</div>
            <div className="text-2xl font-bold text-amber-900 dark:text-amber-100 truncate">{metrics.rated_tasks_count}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-4 flex flex-col h-80">
            <h3 className="text-lg font-semibold mb-4 shrink-0">Rated Skills & Usage History</h3>
            {metrics.skill_analytics && metrics.skill_analytics.length > 0 ? (
              <div className="overflow-y-auto overflow-x-hidden pr-2 space-y-3 flex-grow custom-scrollbar">
                {metrics.skill_analytics.map((skill: any, idx: number) => (
                  <div key={idx} className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-100 dark:border-slate-700">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-bold text-slate-800 dark:text-slate-200">{skill.skill_name}</span>
                      <span className="text-xs font-semibold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-400 px-2 py-0.5 rounded">
                        {skill.score}/5 Rating
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span>Used in {skill.tasks_used} task{skill.tasks_used !== 1 ? 's' : ''}</span>
                      <div className="w-1/2 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 mt-1 relative">
                        <div 
                          className={`absolute top-0 left-0 h-1.5 rounded-full ${skill.tasks_used > 0 ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-500'}`}
                          style={{ width: `${(skill.score / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-grow flex items-center justify-center text-slate-500">No skill data available</div>
            )}
          </div>

          <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-4 flex flex-col h-80">
            <h3 className="text-lg font-semibold mb-4 shrink-0">Performance Evolution</h3>
            {timelineData.length > 0 ? (
              <div className="flex-grow min-h-0 flex items-end gap-2 pb-6 pt-4 px-2 relative ml-6">
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-6 pt-4 px-2">
                  {[5, 4, 3, 2, 1, 0].map(val => (
                    <div key={val} className="w-full flex items-center border-b border-slate-300 dark:border-slate-700 opacity-20 relative h-0">
                      <span className="absolute -left-6 text-[10px] text-slate-500">{val}</span>
                    </div>
                  ))}
                </div>
                {timelineData.map((d, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center justify-end h-full relative group">
                    <div 
                      className="w-full max-w-[24px] bg-emerald-500 rounded-t-sm transition-all hover:bg-emerald-400 cursor-pointer"
                      style={{ height: `${(d.rating / 5) * 100}%` }}
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs py-1 px-2 rounded whitespace-nowrap z-10 transition-opacity">
                        {d.rating} Rating
                      </div>
                    </div>
                    <div className="absolute -bottom-6 text-[10px] text-slate-500 truncate w-full text-center" title={d.name}>
                      {d.name.substring(0, 8)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-grow flex items-center justify-center text-slate-500">No historical tasks</div>
            )}
          </div>
        </div>

        <h3 className="text-xl font-bold border-b border-slate-200 dark:border-slate-700 pb-2 mb-4">Task History</h3>
        
        <div className="space-y-6">
          {task_history.length === 0 && (
             <div className="text-slate-500 py-4 text-center bg-slate-50 dark:bg-slate-800/50 rounded-lg">No tasks completed yet.</div>
          )}
          {task_history.map((task: any) => (
            <div key={task.assignment_id} className="border border-slate-200 dark:border-slate-700 rounded-xl p-5 bg-white dark:bg-slate-800 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white">{task.task_title}</h4>
                  <div className="text-sm text-slate-500 dark:text-slate-400 mt-1 flex flex-wrap gap-3">
                    <span>{task.project_name || 'No Project'}</span>
                    <span>•</span>
                    <span>{task.end_date ? new Date(task.end_date).toLocaleDateString() : 'Completed'}</span>
                    {task.task_type && (
                      <>
                        <span>•</span>
                        <span className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-xs">{task.task_type}</span>
                      </>
                    )}
                    {task.complexity_level && (
                      <>
                        <span>•</span>
                        <span className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-xs">{task.complexity_level}</span>
                      </>
                    )}
                  </div>
                </div>
                {task.performance_rating && (
                  <div className="bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full font-bold">
                    ★ {task.performance_rating}/5
                  </div>
                )}
              </div>
              
              {task.pm_comments && (
                <div className="mb-4 bg-slate-50 dark:bg-slate-900/50 p-3 rounded text-sm italic border-l-4 border-indigo-500">
                  "{task.pm_comments}"
                </div>
              )}
              
              {task.skill_evaluations && task.skill_evaluations.length > 0 && (
                <div className="mt-4">
                  <div className="text-xs font-semibold uppercase text-slate-500 tracking-wider mb-2">Skill Breakdown</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {task.skill_evaluations.map((evalItem: any, idx: number) => (
                      <div key={idx} className="bg-slate-50 dark:bg-slate-700/30 p-2 rounded flex justify-between items-center text-sm">
                        <span className="font-medium">{evalItem.skill_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400 text-xs">Req: {evalItem.required_level}</span>
                          <span className={`font-bold ${evalItem.achieved_level >= evalItem.required_level ? 'text-emerald-500' : 'text-amber-500'}`}>
                            Achieved: {evalItem.achieved_level}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
