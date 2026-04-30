import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { authAPI, dashboardAPI } from '../services/api';
import DashboardLayout from '../components/DashboardLayout';
import {
  ArrowRight,
  Upload,
  Tag,
  Target,
  Settings as SettingsIcon,
  Layers,
  Filter,
  CheckSquare,
  Package,
  Play,
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronRight,
  Zap,
  TrendingUp,
  Activity
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPhase, setCurrentPhase] = useState('data'); // data, training, clinical

  const [stats, setStats] = useState({
    totalDatasets: 0,
    totalRecords: 0,
    labeledPercent: 0,
    trainingJobs: 0,
    modelsDeployed: 0,
    unlabeledRecords: 0
  });

  const [pipelineStatus, setPipelineStatus] = useState({
    upload: { complete: false, count: 0 },
    labeling: { complete: false, progress: 0 },
    preprocessing: { complete: false, lastRun: null },
    training: { active: false, running: 0, queued: 0 }
  });

  const [nextAction, setNextAction] = useState({
    title: 'Upload your first dataset',
    description: 'Start by uploading patient data to begin the ML pipeline',
    action: 'Upload Dataset',
    route: '/data-prep',
    priority: 'high'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      
      const dashboardData = await dashboardAPI.getAllStats({
        includeAdminStats: Boolean(userData?.is_superuser)
      });
      
      // Process stats
      const uploadsData = dashboardData.uploads;
      const labelingData = dashboardData.labeling;
      const trainingData = dashboardData.training;
      const modelsData = dashboardData.models;
      
      const totalDatasets = uploadsData.total || 0;
      const totalRecords = labelingData.total || 0;
      const labeledCount = labelingData.labeled_count || 0;
      const unlabeledCount = labelingData.unlabeled_count || 0;
      const labeledPercent = totalRecords > 0 ? (labeledCount / totalRecords) * 100 : 0;
      
      const runningJobs = trainingData.jobs?.filter(j => j.status === 'running').length || 0;
      const queuedJobs = trainingData.jobs?.filter(j => j.status === 'queued').length || 0;
      
      setStats({
        totalDatasets,
        totalRecords,
        labeledPercent: Math.round(labeledPercent),
        trainingJobs: runningJobs + queuedJobs,
        modelsDeployed: modelsData.total_count || 0,
        unlabeledRecords: unlabeledCount
      });

      // Determine pipeline status
      setPipelineStatus({
        upload: { complete: totalDatasets > 0, count: totalDatasets },
        labeling: { complete: labeledPercent >= 80, progress: labeledPercent },
        preprocessing: { complete: false, lastRun: null }, // TODO: track this
        training: { active: runningJobs > 0, running: runningJobs, queued: queuedJobs }
      });

      // Determine next action (decision-driven!)
      determineNextAction(totalDatasets, labeledPercent, unlabeledCount, runningJobs, modelsData.total_count);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const determineNextAction = (datasets, labeledPct, unlabeled, training, models) => {
    // Decision tree for "what to do next"
    if (datasets === 0) {
      setNextAction({
        title: 'Upload your first dataset',
        description: 'Start by uploading patient data (CSV/Excel) to begin the ML pipeline',
        action: 'Upload Dataset',
        route: '/data-prep',
        priority: 'high',
        icon: Upload
      });
    } else if (labeledPct < 50) {
      setNextAction({
        title: `Label ${unlabeled} unlabeled records`,
        description: `You have ${labeledPct}% labeled. Aim for 80%+ before training`,
        action: 'Start Labeling',
        route: '/data-prep?tab=2',
        priority: 'high',
        icon: Tag
      });
    } else if (labeledPct >= 50 && training === 0 && models === 0) {
      setNextAction({
        title: 'Ready to train your first model',
        description: `${labeledPct}% labeled - good coverage! Start training now`,
        action: 'Start Training',
        route: '/training',
        priority: 'high',
        icon: Play
      });
    } else if (training > 0) {
      setNextAction({
        title: `${training} model(s) training`,
        description: 'Training in progress. Monitor progress or compare completed models',
        action: 'View Training Jobs',
        route: '/training',
        priority: 'medium',
        icon: Activity
      });
    } else if (models > 0) {
      setNextAction({
        title: 'Explore model performance',
        description: `${models} trained models available. Compare metrics or generate predictions`,
        action: 'View Models',
        route: '/models',
        priority: 'medium',
        icon: TrendingUp
      });
    } else {
      setNextAction({
        title: 'Continue your workflow',
        description: 'Review data quality or preprocess your dataset',
        action: 'Data Preparation',
        route: '/data-prep',
        priority: 'low',
        icon: Layers
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-gray-500 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <DashboardLayout>
      {/* Clean, spacious container */}
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50/30 to-gray-50">
        
        {/* Header - Clean and minimal */}
        <div className="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="max-w-[1400px] mx-auto px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-1">
                  {getGreeting()}, {user?.username || 'Researcher'}
                </h1>
                <p className="text-sm text-gray-500">
                  {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                </p>
              </div>

              {/* Phase Switcher */}
              <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                {['data', 'training', 'clinical'].map(phase => (
                  <button
                    key={phase}
                    onClick={() => setCurrentPhase(phase)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      currentPhase === phase
                        ? 'bg-white text-purple-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {phase.charAt(0).toUpperCase() + phase.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Spacious */}
        <div className="max-w-[1400px] mx-auto px-8 py-8">
          
          {/* ==== PRIMARY FOCUS: What to Do Next ==== */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <NextActionCard {...nextAction} />
          </motion.div>

          {/* ==== SECONDARY: Quick Status Overview ==== */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            <StatusCard
              label="Datasets"
              value={stats.totalDatasets}
              subtitle={`${stats.totalRecords.toLocaleString()} records`}
              status={stats.totalDatasets > 0 ? 'good' : 'neutral'}
              onClick={() => navigate('/data-prep')}
            />
            <StatusCard
              label="Labeled"
              value={`${stats.labeledPercent}%`}
              subtitle={`${stats.unlabeledRecords} need labeling`}
              status={stats.labeledPercent >= 80 ? 'good' : stats.labeledPercent >= 50 ? 'warning' : 'neutral'}
              onClick={() => navigate('/data-prep?tab=2')}
            />
            <StatusCard
              label="Training"
              value={stats.trainingJobs}
              subtitle={stats.trainingJobs > 0 ? 'jobs active' : 'no active jobs'}
              status={stats.trainingJobs > 0 ? 'active' : 'neutral'}
              onClick={() => navigate('/training')}
            />
            <StatusCard
              label="Models"
              value={stats.modelsDeployed}
              subtitle="ready to use"
              status={stats.modelsDeployed > 0 ? 'good' : 'neutral'}
              onClick={() => navigate('/models')}
            />
          </div>

          {/* ==== TERTIARY: Pipeline Progress ==== */}
          <div className="grid grid-cols-[1fr,400px] gap-8">
            
            {/* Left: Pipeline Visualization */}
            <div className="bg-white rounded-xl border border-gray-200 p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">ML Pipeline Progress</h2>
                <span className="text-xs text-gray-500 font-medium">8-Step Workflow</span>
              </div>

              <PipelineSteps pipelineStatus={pipelineStatus} />
            </div>

            {/* Right: Contextual Insights */}
            <div className="space-y-6">
              
              {/* Alerts Card */}
              <AlertsCard 
                alerts={[
                  stats.unlabeledRecords > 100 && {
                    type: 'warning',
                    message: `${stats.unlabeledRecords} records need labeling`,
                    action: () => navigate('/data-prep?tab=2')
                  },
                  stats.totalDatasets === 0 && {
                    type: 'info',
                    message: 'No datasets uploaded yet',
                    action: () => navigate('/data-prep')
                  },
                  stats.trainingJobs > 0 && {
                    type: 'active',
                    message: `${stats.trainingJobs} models training`,
                    action: () => navigate('/training')
                  }
                ].filter(Boolean)}
              />

              {/* Recent Activity */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  <ActivityItem 
                    icon={Upload}
                    text="Dataset uploaded"
                    time="2 hours ago"
                    status="success"
                  />
                  <ActivityItem 
                    icon={Tag}
                    text="Labeling completed"
                    time="Yesterday"
                    status="success"
                  />
                  <ActivityItem 
                    icon={Play}
                    text="Training started"
                    time="2 days ago"
                    status="info"
                  />
                </div>
                <button className="w-full mt-4 text-sm text-purple-600 hover:text-purple-700 font-medium">
                  View all activity
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// ==== COMPONENTS ====

function NextActionCard({ title, description, action, route, priority, icon: Icon }) {
  const navigate = useNavigate();
  
  const priorityStyles = {
    high: 'from-purple-600 to-purple-700',
    medium: 'from-purple-500 to-purple-600',
    low: 'from-gray-600 to-gray-700'
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="relative overflow-hidden"
    >
      <div className={`bg-gradient-to-br ${priorityStyles[priority]} rounded-2xl p-8 text-white shadow-lg`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {Icon && <Icon className="w-6 h-6" />}
              <span className="text-xs font-semibold uppercase tracking-wider opacity-90">
                Next Action
              </span>
            </div>
            <h2 className="text-3xl font-bold mb-3">{title}</h2>
            <p className="text-purple-100 text-base mb-6 max-w-2xl">
              {description}
            </p>
            <button
              onClick={() => navigate(route)}
              className="inline-flex items-center gap-2 bg-white text-purple-700 px-6 py-3 rounded-lg font-semibold hover:bg-purple-50 transition-colors"
            >
              {action}
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
          
          {/* Decorative element */}
          <div className="opacity-10">
            <Zap className="w-32 h-32" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StatusCard({ label, value, subtitle, status, onClick }) {
  const statusStyles = {
    good: 'border-green-200 bg-green-50/50',
    warning: 'border-amber-200 bg-amber-50/50',
    active: 'border-purple-200 bg-purple-50/50',
    neutral: 'border-gray-200 bg-white'
  };

  const statusIndicators = {
    good: <div className="w-2 h-2 rounded-full bg-green-500" />,
    warning: <div className="w-2 h-2 rounded-full bg-amber-500" />,
    active: <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />,
    neutral: null
  };

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02, y: -2 }}
      className={`${statusStyles[status]} border rounded-xl p-6 text-left transition-all hover:shadow-md`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {label}
        </span>
        {statusIndicators[status]}
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">
        {value}
      </div>
      <div className="text-sm text-gray-600">
        {subtitle}
      </div>
    </motion.button>
  );
}

function PipelineSteps({ pipelineStatus }) {
  const steps = [
    { id: 1, label: 'Upload', icon: Upload, status: pipelineStatus.upload.complete ? 'complete' : 'pending' },
    { id: 2, label: 'Labeling', icon: Tag, status: pipelineStatus.labeling.complete ? 'complete' : pipelineStatus.upload.complete ? 'active' : 'pending' },
    { id: 3, label: 'Target', icon: Target, status: 'pending' },
    { id: 4, label: 'Preprocess', icon: SettingsIcon, status: 'pending' },
    { id: 5, label: 'Features', icon: Layers, status: 'pending' },
    { id: 6, label: 'Selection', icon: Filter, status: 'pending' },
    { id: 7, label: 'Validation', icon: CheckSquare, status: 'pending' },
    { id: 8, label: 'Train', icon: Package, status: pipelineStatus.training.active ? 'active' : 'pending' }
  ];

  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center gap-4">
          {/* Step indicator */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 ${
            step.status === 'complete' 
              ? 'bg-green-100 border-green-500'
              : step.status === 'active'
              ? 'bg-purple-100 border-purple-500'
              : 'bg-gray-100 border-gray-300'
          }`}>
            {step.status === 'complete' ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : step.status === 'active' ? (
              <step.icon className="w-5 h-5 text-purple-600" />
            ) : (
              <step.icon className="w-5 h-5 text-gray-400" />
            )}
          </div>

          {/* Step info */}
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${
                step.status === 'complete' || step.status === 'active'
                  ? 'text-gray-900'
                  : 'text-gray-400'
              }`}>
                {step.label}
              </span>
              {step.status === 'active' && (
                <span className="text-xs text-purple-600 font-medium">In Progress</span>
              )}
              {step.status === 'complete' && (
                <span className="text-xs text-green-600 font-medium">Done</span>
              )}
            </div>
            
            {/* Progress bar for active step */}
            {step.status === 'active' && step.id === 2 && (
              <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-600 transition-all duration-500"
                  style={{ width: `${pipelineStatus.labeling.progress}%` }}
                />
              </div>
            )}
          </div>

          {/* Connector line */}
          {index < steps.length - 1 && (
            <div className={`absolute left-[1.25rem] mt-14 w-0.5 h-6 ${
              step.status === 'complete' ? 'bg-green-300' : 'bg-gray-200'
            }`} style={{ marginLeft: '0rem' }} />
          )}
        </div>
      ))}
    </div>
  );
}

function AlertsCard({ alerts }) {
  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 text-green-600">
          <CheckCircle className="w-5 h-5" />
          <span className="text-sm font-medium">All systems operational</span>
        </div>
      </div>
    );
  }

  const typeStyles = {
    warning: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: AlertCircle },
    info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: AlertCircle },
    active: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', icon: Activity }
  };

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => {
        const style = typeStyles[alert.type];
        const Icon = style.icon;
        
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`${style.bg} ${style.border} border rounded-lg p-4 cursor-pointer hover:shadow-sm transition-all`}
            onClick={alert.action}
          >
            <div className="flex items-start gap-3">
              <Icon className={`w-5 h-5 ${style.text} flex-shrink-0 mt-0.5`} />
              <div className="flex-1">
                <p className={`text-sm font-medium ${style.text}`}>
                  {alert.message}
                </p>
              </div>
              <ChevronRight className={`w-4 h-4 ${style.text}`} />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

function ActivityItem({ icon: Icon, text, time, status }) {
  const statusColors = {
    success: 'text-green-600 bg-green-100',
    info: 'text-purple-600 bg-purple-100',
    warning: 'text-amber-600 bg-amber-100'
  };

  return (
    <div className="flex items-center gap-3">
      <div className={`w-8 h-8 rounded-full ${statusColors[status]} flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{text}</p>
        <p className="text-xs text-gray-500">{time}</p>
      </div>
    </div>
  );
}
