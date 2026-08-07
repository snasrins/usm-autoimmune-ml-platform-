import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  Brain,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  Cpu,
  BarChart3,
  Eye,
  Pause,
  Play,
  Square,
  RefreshCw,
  Calendar,
  Timer,
  FileText,
  Plus,
  ChevronRight,
  ArrowDown,
  Lock,
  Unlock,
  Layers,
  GitBranch,
  Sparkles,
  Settings,
  Database,
  Activity,
  XCircle,
  PlayCircle
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function TrainingJobsPage() {
  const navigate = useNavigate();
  
  // Two-stage ensemble training architecture
  const [ensembleRun, setEnsembleRun] = useState({
    id: 'ensemble-2024-04-03',
    name: 'Ensemble Training Run',
    datasetVersion: 'AAM-SLE-E v2.1',
    startedAt: '2024-04-03 08:15',
    stage1Jobs: [
      {
        id: 'stage1-rf',
        name: 'Random Forest Base',
        algorithm: 'Random Forest',
        role: 'base',
        stage: 1,
        status: 'completed',
        progress: 100,
        accuracy: 87.3,
        precision: 89.1,
        recall: 85.7,
        f1Score: 87.3,
        gpuUsage: 0,
        vramUsage: 0,
        runtime: '1h 23m',
        completedAt: '2024-04-03 09:38',
        hyperparameters: { n_estimators: 100, max_depth: 15 }
      },
      {
        id: 'stage1-xgb',
        name: 'XGBoost Base',
        algorithm: 'XGBoost',
        role: 'base',
        stage: 1,
        status: 'running',
        progress: 78,
        currentEpoch: 78,
        totalEpochs: 100,
        accuracy: 84.7,
        loss: 0.223,
        gpuUsage: 85,
        vramUsage: 14.2,
        runtime: '2h 04m',
        startedAt: '2024-04-03 08:15',
        estimatedCompletion: '28 min',
        hyperparameters: { max_depth: 8, learning_rate: 0.1, n_estimators: 100 }
      },
      {
        id: 'stage1-gb',
        name: 'Gradient Boosting Base',
        algorithm: 'Gradient Boosting',
        role: 'base',
        stage: 1,
        status: 'running',
        progress: 65,
        currentEpoch: 65,
        totalEpochs: 100,
        accuracy: 86.2,
        loss: 0.198,
        gpuUsage: 72,
        vramUsage: 11.8,
        runtime: '1h 42m',
        startedAt: '2024-04-03 08:15',
        estimatedCompletion: '54 min',
        hyperparameters: { n_estimators: 100, learning_rate: 0.05 }
      },
      {
        id: 'stage1-svm',
        name: 'SVM Base',
        algorithm: 'Support Vector Machine',
        role: 'base',
        stage: 1,
        status: 'queued',
        progress: 0,
        gpuUsage: 0,
        vramUsage: 0,
        queuePosition: 1,
        hyperparameters: { kernel: 'rbf', C: 1.0, gamma: 'scale' }
      },
      {
        id: 'stage1-lr',
        name: 'Logistic Regression Base',
        algorithm: 'Logistic Regression',
        role: 'base',
        stage: 1,
        status: 'queued',
        progress: 0,
        gpuUsage: 0,
        vramUsage: 0,
        queuePosition: 2,
        hyperparameters: { penalty: 'l2', C: 1.0, max_iter: 1000 }
      }
    ],
    stage2Job: {
      id: 'stage2-meta',
      name: 'Meta-Learner Stack',
      algorithm: 'Logistic Regression',
      role: 'meta',
      stage: 2,
      status: 'locked',
      progress: 0,
      dependsOn: ['stage1-rf', 'stage1-xgb', 'stage1-gb', 'stage1-svm', 'stage1-lr'],
      gpuUsage: 0,
      vramUsage: 0,
      hyperparameters: { penalty: 'l2', C: 1.5, max_iter: 500 },
      estimatedRuntime: '45 min'
    }
  });

  // GPU Quota Management
  const gpuQuota = {
    total: 4,
    used: 2,
    available: 2,
    totalVRAM: 64, // GB
    usedVRAM: 26.0,
    availableVRAM: 38.0,
    jobs: [
      { name: 'XGBoost Base', gpuId: 0, vram: 14.2 },
      { name: 'Gradient Boosting Base', gpuId: 1, vram: 11.8 }
    ]
  };

  const [filterStatus, setFilterStatus] = useState('all');

  // Calculate pipeline status
  const stage1Jobs = ensembleRun.stage1Jobs;
  const stage2Job = ensembleRun.stage2Job;
  const stage1Complete = stage1Jobs.every(j => j.status === 'completed');
  const stage1Running = stage1Jobs.some(j => j.status === 'running');
  
  const activeJobs = stage1Jobs.filter(j => j.status === 'running').length;
  const completedJobs = stage1Jobs.filter(j => j.status === 'completed').length;
  const totalJobs = stage1Jobs.length + 1; // +1 for meta-learner

  // Filter jobs
  const getFilteredJobs = () => {
    if (filterStatus === 'all') return stage1Jobs;
    return stage1Jobs.filter(job => job.status === filterStatus);
  };
  
  const filteredStage1Jobs = getFilteredJobs();

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white/60 backdrop-blur-sm border-b border-white/20">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-syne text-lg font-bold text-black-text">Training Pipeline</h1>
              <span className="px-2 py-0.5 rounded-md bg-purple-dim text-purple-primary text-[10px] font-semibold">
                Two-Stage DAG
              </span>
              <span className="px-2 py-0.5 rounded-md bg-amber-dim text-amber text-[10px] font-semibold">
                {activeJobs} running
              </span>
            </div>
            <p className="text-xs text-gray-muted mt-0.5">Stage 1: Base Learners → Stage 2: Meta-Learner</p>
          </div>
          <button
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            New Ensemble Run
          </button>
        </div>

        {/* Stats Bar + GPU Quota */}
        <div className="px-6 py-4 bg-white/40 backdrop-blur-sm border-b border-white/20">
          <div className="max-w-7xl mx-auto grid grid-cols-5 gap-4">
            <StatCard
              icon={Layers}
              label="Pipeline Progress"
              value={`${completedJobs}/${totalJobs}`}
              color="purple"
            />
            <StatCard
              icon={CheckCircle}
              label="Stage 1 Complete"
              value={`${completedJobs}/5`}
              color="green"
            />
            <StatCard
              icon={Cpu}
              label="GPUs Used"
              value={`${gpuQuota.used}/${gpuQuota.total}`}
              color="amber"
            />
            <StatCard
              icon={Database}
              label="VRAM Used"
              value={`${gpuQuota.usedVRAM.toFixed(1)}GB`}
              color="blue"
            />
            <StatCard
              icon={Activity}
              label="Avg GPU Load"
              value={`${Math.round((stage1Jobs.filter(j => j.status === 'running').reduce((sum, j) => sum + j.gpuUsage, 0) / activeJobs) || 0)}%`}
              color="purple"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* GPU Quota Panel */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-purple-primary" />
                  <h2 className="font-syne text-base font-bold text-black-text">GPU Resource Allocation</h2>
                </div>
                <div className="text-xs text-gray-muted">
                  {gpuQuota.available} GPU{gpuQuota.available !== 1 ? 's' : ''} available • {gpuQuota.availableVRAM.toFixed(1)}GB VRAM free
                </div>
              </div>
              
              <div className="grid grid-cols-4 gap-3">
                {Array.from({ length: gpuQuota.total }, (_, i) => {
                  const job = gpuQuota.jobs.find(j => j.gpuId === i);
                  return (
                    <div key={i} className={`p-3 rounded-xl border-2 ${
                      job 
                        ? 'bg-purple-dim border-purple-primary/30' 
                        : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="text-[10px] font-bold text-gray-muted mb-1">GPU {i}</div>
                      {job ? (
                        <>
                          <div className="text-xs font-semibold text-purple-primary mb-1 line-clamp-1">
                            {job.name}
                          </div>
                          <div className="text-xs text-gray-muted">
                            {job.vram}GB VRAM
                          </div>
                        </>
                      ) : (
                        <div className="text-xs text-gray-muted">Idle</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Two-Stage DAG Visualization */}
            <div className="bg-gradient-to-br from-purple-primary/5 to-purple-primary/10 border-2 border-purple-primary/20 rounded-2xl p-6">
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2">
                  <GitBranch className="w-5 h-5 text-purple-primary" />
                  <h2 className="font-syne text-lg font-bold text-black-text">Ensemble Training DAG</h2>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-muted">
                  <span className="flex items-center gap-1">
                    <Database className="w-3.5 h-3.5" />
                    Dataset: {ensembleRun.datasetVersion}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    Started: {ensembleRun.startedAt}
                  </span>
                </div>
              </div>

              {/* Stage 1: Base Learners */}
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-500 text-xs font-bold flex items-center gap-1.5">
                    <Layers className="w-4 h-4" />
                    STAGE 1
                  </div>
                  <div className="text-sm font-medium text-gray-muted">
                    Base Learners (Parallel Training)
                  </div>
                  <div className="ml-auto text-xs text-gray-muted">
                    {completedJobs}/5 completed
                  </div>
                </div>
                
                <div className="grid grid-cols-5 gap-3 mb-4">
                  {stage1Jobs.map((job, idx) => (
                    <StageJobCard key={job.id} job={job} jobNumber={idx + 1} />
                  ))}
                </div>
              </div>

              {/* Dependency Arrow */}
              <div className="flex items-center justify-center mb-6">
                <div className="flex flex-col items-center gap-2">
                  <div className="text-xs text-gray-muted">All Stage 1 jobs must complete</div>
                  <ArrowDown className="w-6 h-6 text-purple-primary" />
                  <div className="text-xs text-gray-muted">Out-of-fold predictions → Stage 2</div>
                </div>
              </div>

              {/* Stage 2: Meta-Learner */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="px-3 py-1.5 rounded-lg bg-purple-dim text-purple-primary text-xs font-bold flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    STAGE 2
                  </div>
                  <div className="text-sm font-medium text-gray-muted">
                    Meta-Learner (Combines Base Predictions)
                  </div>
                  {stage2Job.status === 'locked' && (
                    <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-dim text-amber text-xs font-medium">
                      <Lock className="w-3.5 h-3.5" />
                      Locked
                    </div>
                  )}
                </div>
                
                <Stage2JobCard job={stage2Job} locked={!stage1Complete} />
              </div>
            </div>

            {/* Filter & Jobs List */}
            <div>
              <div className="flex items-center gap-3 mb-4">
                <h2 className="font-syne text-base font-bold text-black-text">Stage 1 Job Details</h2>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 rounded-lg border border-white/40 bg-white/80 backdrop-blur-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="running">Running</option>
                  <option value="completed">Completed</option>
                  <option value="queued">Queued</option>
                  <option value="failed">Failed</option>
                </select>
              </div>

              <div className="space-y-3">
                {filteredStage1Jobs.map((job) => (
                  <DetailedJobCard key={job.id} job={job} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    amber: { bg: 'bg-amber-dim', text: 'text-amber' },
    green: { bg: 'bg-green-dim', text: 'text-green' },
    purple: { bg: 'bg-purple-dim', text: 'text-purple-primary' },
    blue: { bg: 'bg-blue-50', text: 'text-blue-500' }
  };
  const c = colorMap[color];

  return (
    <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${c.bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${c.text}`} />
        </div>
        <div>
          <div className="text-xs text-gray-muted">{label}</div>
          <div className="font-syne text-xl font-bold text-black-text">{value}</div>
        </div>
      </div>
    </div>
  );
}

function StageJobCard({ job, jobNumber }) {
  const getStatusConfig = (status) => {
    const configs = {
      running: { color: 'text-amber', bg: 'bg-amber-dim', icon: Zap, label: 'Running' },
      completed: { color: 'text-green', bg: 'bg-green-dim', icon: CheckCircle, label: 'Complete' },
      queued: { color: 'text-blue-500', bg: 'bg-blue-50', icon: Clock, label: 'Queued' },
      failed: { color: 'text-red', bg: 'bg-red-dim', icon: XCircle, label: 'Failed' }
    };
    return configs[status] || configs.queued;
  };

  const statusConfig = getStatusConfig(job.status);
  const StatusIcon = statusConfig.icon;

  return (
    <div className={`bg-white/80 backdrop-blur-sm border-2 rounded-xl p-3 transition-all ${
      job.status === 'running' ? 'border-amber shadow-md' : 
      job.status === 'completed' ? 'border-green/30' : 
      'border-white/40'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-bold text-purple-primary">BASE #{jobNumber}</div>
        <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full ${statusConfig.bg} ${statusConfig.color}`}>
          <StatusIcon className="w-3 h-3" />
        </div>
      </div>
      
      <div className="text-xs font-semibold text-black-text mb-1 line-clamp-1">{job.name}</div>
      <div className="text-[10px] text-gray-muted mb-2">{job.algorithm}</div>
      
      {job.status === 'running' && (
        <>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-amber rounded-full transition-all"
              style={{ width: `${job.progress}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-gray-muted">{job.progress}%</span>
            <span className="text-amber font-medium">{job.accuracy}%</span>
          </div>
        </>
      )}
      
      {job.status === 'completed' && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-muted">Accuracy</span>
          <span className="font-bold text-green">{job.accuracy}%</span>
        </div>
      )}
      
      {job.status === 'queued' && (
        <div className="text-[10px] text-gray-muted">
          Queue position: #{job.queuePosition}
        </div>
      )}
    </div>
  );
}

function Stage2JobCard({ job, locked }) {
  return (
    <div className={`bg-white/80 backdrop-blur-sm border-2 rounded-2xl p-5 ${
      locked ? 'border-amber/30 opacity-70' : 'border-purple-primary/40'
    }`}>
      <div className="flex items-center gap-4">
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
          locked ? 'bg-gray-100' : 'bg-gradient-to-br from-purple-primary to-purple-primary/80'
        }`}>
          {locked ? (
            <Lock className="w-7 h-7 text-gray-muted" />
          ) : (
            <Sparkles className="w-7 h-7 text-white" />
          )}
        </div>
        
        <div className="flex-1">
          <div className="font-syne text-lg font-bold text-black-text mb-1">{job.name}</div>
          <div className="text-sm text-gray-muted mb-2">{job.algorithm}</div>
          
          {locked ? (
            <div className="text-xs text-amber">
              Waiting for {job.dependsOn.length} base learners to complete
            </div>
          ) : (
            <div className="text-xs text-gray-muted">
              Ready to start • Est. runtime: {job.estimatedRuntime}
            </div>
          )}
        </div>
        
        {!locked && (
          <button className="px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium flex items-center gap-2">
            <PlayCircle className="w-4 h-4" />
            Start Training
          </button>
        )}
      </div>
    </div>
  );
}

function DetailedJobCard({ job }) {
  const getStatusConfig = (status) => {
    const configs = {
      running: { color: 'text-amber', bg: 'bg-amber-dim', icon: Zap, label: 'Running' },
      completed: { color: 'text-green', bg: 'bg-green-dim', icon: CheckCircle, label: 'Completed' },
      queued: { color: 'text-blue-500', bg: 'bg-blue-50', icon: Clock, label: 'Queued' },
      failed: { color: 'text-red', bg: 'bg-red-dim', icon: AlertCircle, label: 'Failed' }
    };
    return configs[status] || configs.queued;
  };

  const statusConfig = getStatusConfig(job.status);
  const StatusIcon = statusConfig.icon;

  return (
    <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl p-4 hover:border-purple-primary/30 transition-all">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-purple-dim flex items-center justify-center flex-shrink-0">
          <Brain className="w-5 h-5 text-purple-primary" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="font-syne text-sm font-bold text-black-text mb-0.5">{job.name}</h3>
              <div className="text-xs text-gray-muted">{job.algorithm}</div>
            </div>
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${statusConfig.bg} ${statusConfig.color} flex-shrink-0`}>
              <StatusIcon className="w-3.5 h-3.5" />
              <span className="text-xs font-medium">{statusConfig.label}</span>
            </div>
          </div>
          
          {job.status === 'running' && (
            <>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-gray-muted">Epoch {job.currentEpoch}/{job.totalEpochs}</span>
                <span className="font-semibold text-amber">{job.progress}%</span>
              </div>
              <div className="h-2 bg-gray-50 rounded-full overflow-hidden mb-3">
                <div className="h-full bg-gradient-to-r from-amber to-amber/80 rounded-full" style={{ width: `${job.progress}%` }} />
              </div>
            </>
          )}
          
          <div className="grid grid-cols-4 gap-3 text-xs">
            {job.accuracy && (
              <div>
                <div className="text-gray-muted mb-0.5">Accuracy</div>
                <div className="font-bold text-purple-primary">{job.accuracy}%</div>
              </div>
            )}
            {job.loss && (
              <div>
                <div className="text-gray-muted mb-0.5">Loss</div>
                <div className="font-bold text-black-text">{job.loss}</div>
              </div>
            )}
            <div>
              <div className="text-gray-muted mb-0.5">GPU</div>
              <div className="font-bold text-black-text">{job.gpuUsage}%</div>
            </div>
            <div>
              <div className="text-gray-muted mb-0.5">Runtime</div>
              <div className="font-bold text-black-text">{job.runtime || '-'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
