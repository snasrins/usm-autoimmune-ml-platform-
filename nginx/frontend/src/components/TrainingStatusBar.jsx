import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, CheckCircle, Loader2, X, ChevronDown, ChevronUp, BarChart3 } from 'lucide-react';
import { trainingAPI } from '../services/api-complete';

export default function TrainingStatusBar() {
  const navigate = useNavigate();
  const [activeRun, setActiveRun] = useState(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isVisible, setIsVisible] = useState(true);

  // Load active run from sessionStorage
  useEffect(() => {
    const loadActiveRun = () => {
      const savedRun = sessionStorage.getItem('active_training_run');
      if (savedRun) {
        try {
          const run = JSON.parse(savedRun);
          setActiveRun(run);
        } catch (error) {
          console.error('[TrainingStatusBar] Failed to parse active run:', error);
          sessionStorage.removeItem('active_training_run');
        }
      } else {
        setActiveRun(null);
      }
    };

    loadActiveRun();

    // Poll every 3 seconds for updates
    const interval = setInterval(loadActiveRun, 3000);

    return () => clearInterval(interval);
  }, []);

  // Poll job statuses
  useEffect(() => {
    if (!activeRun) return;

    const pollJobs = async () => {
      try {
        let hasUpdates = false;
        const updatedJobs = { ...activeRun.jobs };

        for (const [modelId, job] of Object.entries(activeRun.jobs)) {
          if (job.status !== 'completed' && job.status !== 'failed') {
            const statusData = await trainingAPI.getJobStatus(job.job_id);
            
            if (statusData.status !== job.status) {
              hasUpdates = true;
              updatedJobs[modelId] = {
                ...job,
                status: statusData.status,
                progress: statusData.progress?.percentage || 0,
                result: statusData.result
              };
            }
          }
        }

        if (hasUpdates) {
          const updatedRun = { ...activeRun, jobs: updatedJobs };
          setActiveRun(updatedRun);
          sessionStorage.setItem('active_training_run', JSON.stringify(updatedRun));
        }
      } catch (error) {
        console.error('[TrainingStatusBar] Error polling jobs:', error);
      }
    };

    const interval = setInterval(pollJobs, 3000);
    return () => clearInterval(interval);
  }, [activeRun]);

  if (!activeRun || !isVisible) return null;

  const jobs = Object.values(activeRun.jobs);
  const activeJobs = jobs.filter(j => j.status === 'running').length;
  const queuedJobs = jobs.filter(j => j.status === 'queued').length;
  const completedJobs = jobs.filter(j => j.status === 'completed').length;
  const failedJobs = jobs.filter(j => j.status === 'failed').length;
  const totalJobs = jobs.length;
  const progress = Math.round((completedJobs / totalJobs) * 100);

  return (
    <div className="bg-purple-primary/10 border-b border-purple-primary/20 transition-all duration-300">
      {/* Compact Header (always visible) */}
      <div className="flex items-center gap-4 px-6 py-3">
        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-amber rounded-full animate-pulse"></div>
          <span className="text-sm font-medium text-purple-primary">
            Training in Progress
          </span>
        </div>

        {/* Progress Summary */}
        <div className="flex items-center gap-4 text-xs text-gray-700">
          {activeJobs > 0 && (
            <div className="flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber" />
              <span>{activeJobs} running</span>
            </div>
          )}
          {queuedJobs > 0 && (
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-gray-muted" />
              <span>{queuedJobs} queued</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-green" />
            <span>{completedJobs}/{totalJobs} completed</span>
          </div>
          {failedJobs > 0 && (
            <div className="flex items-center gap-1.5">
              <X className="w-3.5 h-3.5 text-red-500" />
              <span>{failedJobs} failed</span>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="flex-1 max-w-xs">
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-primary to-purple-light transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 ml-auto">
          {completedJobs > 0 && (
            <button
              onClick={() => navigate('/model-comparison')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-xs font-medium"
            >
              <BarChart3 className="w-3.5 h-3.5" />
              View Results
            </button>
          )}
          <button
            onClick={() => navigate('/training')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-primary/30 hover:bg-purple-primary/10 transition-colors text-xs font-medium text-purple-primary"
          >
            View Details
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg hover:bg-purple-primary/10 transition-colors"
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-purple-primary" />
            ) : (
              <ChevronDown className="w-4 h-4 text-purple-primary" />
            )}
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="p-1.5 rounded-lg hover:bg-purple-primary/10 transition-colors"
            title="Hide"
          >
            <X className="w-4 h-4 text-gray-muted" />
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-6 pb-3 pt-1">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {jobs.map((job, index) => {
              const statusColors = {
                queued: 'bg-gray-100 text-gray-700 border-gray-300',
                running: 'bg-amber-dim text-amber border-amber',
                completed: 'bg-green-dim text-green border-green',
                failed: 'bg-red-100 text-red-600 border-red-300'
              };

              return (
                <div
                  key={index}
                  className={`px-3 py-2 rounded-lg border ${statusColors[job.status]} text-xs font-medium flex items-center justify-between`}
                >
                  <span>{job.model_name}</span>
                  {job.status === 'running' && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  )}
                  {job.status === 'completed' && (
                    <CheckCircle className="w-3.5 h-3.5" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
