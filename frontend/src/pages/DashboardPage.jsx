import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as Tooltip from '@radix-ui/react-tooltip';
import { authAPI, dashboardAPI, mlAPI } from '../services/api';
import { explainabilityAPI } from '../services/api-complete';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import MissionControlModal from '../components/MissionControlModal';

// Phase 3 Dashboard Components
import { DatasetStatusCard, DataQualityCard, GPUStatusCard, TrainedModelsCard } from '../components/dashboard/StatusCards';
import { DataQualityOverviewPanel } from '../components/dashboard/DataQualityOverviewPanel';
import { ModelPerformancePanel } from '../components/dashboard/ModelPerformancePanel';
import { FeatureImportancePanel } from '../components/dashboard/FeatureImportancePanel';
import { SystemInsightsPanel } from '../components/dashboard/SystemInsightsPanel';

import {
  Cpu,
  ChevronRight,
  AlertCircle,
  Database,
  List,
  Play,
  Upload,
  Brain,
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showMissionControl, setShowMissionControl] = useState(
    () => sessionStorage.getItem('mc_dismissed') !== '1'
  );

  // Real data from API
  const [stats, setStats] = useState({
    totalDatasets: 0,
    totalRecords: 0,
    modelsDeployed: 0,
    trainingJobs: 0,
    gpuUsagePercent: 0,      // Dynamic GPU percentage
    gpuMemoryUsed: 0,        // Dynamic GPU memory used (GB)
    gpuMemoryTotal: 24,      // Dynamic GPU memory total (GB)
    experimentsRunning: 0,
    pipelinesActive: 0,
    labeledRecords: 0,
    unlabeledRecords: 0,
    totalUsers: 0,
    totalPatients: 0,
    dataQualityIssues: 0,    // Dynamic data quality issues count
    dataQualityMissingPct: 0 // Dynamic missing values percentage
  });

  const [alerts, setAlerts] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  
  // Dashboard panel data
  const [modelPerformance, setModelPerformance] = useState({
    accuracy: 0,
    rocAuc: 0,
    precision: 0,
    f1Score: 0,
    runs: []
  });
  const [featureImportance, setFeatureImportance] = useState([]);
  const [dataQuality, setDataQuality] = useState({
    missingPercent: 0,
    classImbalance: { hospital_a: 50, hospital_b: 50 },
    outliers: 0,
    dataSources: { count: 0, distribution: '0%' }
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load user data
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      
      // Load dashboard statistics
      const dashboardData = await dashboardAPI.getAllStats({
        includeAdminStats: Boolean(userData?.is_superuser)
      });
      
      // Filter data by current user (unless superuser)
      const currentUserId = userData?.id;
      const isSuperuser = userData?.is_superuser;
      
      // Process uploads data (filter by user unless superuser)
      const uploadsData = dashboardData.uploads;
      const userUploads = isSuperuser ? uploadsData.uploads : (uploadsData.uploads || []).filter(u => u.user_id === currentUserId || u.uploaded_by_id === currentUserId);
      const totalDatasets = userUploads.length;
      const totalRecordsFromUploads = userUploads.reduce((sum, upload) => {
        return sum + (upload.row_count || 0);
      }, 0) || 0;
      
      // Process labeling data
      const labelingData = dashboardData.labeling;
      const labeledCount = labelingData.labeled_count || 0;
      const unlabeledCount = labelingData.unlabeled_count || 0;
      const totalRecords = labelingData.total || totalRecordsFromUploads;
      
      // Process platform data
      const platformData = dashboardData.platform;
      const totalUsers = platformData.users?.total || 0;
      const totalPatients = platformData.patients?.total || 0;
      
      // Process ML models data (filter by user unless superuser)
      const modelsData = dashboardData.models;
      const userModels = isSuperuser ? modelsData.models : (modelsData.models || []).filter(m => m.user_id === currentUserId);
      const totalModels = userModels.length;
      
      // Process training data (filter by user unless superuser)
      const trainingData = dashboardData.training;
      const userJobs = isSuperuser ? trainingData.jobs : (trainingData.jobs || []).filter(j => j.user_id === currentUserId);
      const runningJobs = userJobs.filter(job => 
        job.status === 'running' || job.status === 'queued'
      ).length || 0;
      
      // Update stats
      setStats(prev => ({
        ...prev,
        totalDatasets,
        totalRecords,
        labeledRecords: labeledCount,
        unlabeledRecords: unlabeledCount,
        totalUsers,
        totalPatients,
        modelsDeployed: totalModels,
        trainingJobs: runningJobs,
        experimentsRunning: Math.floor(totalDatasets * 0.2), // Estimate
        pipelinesActive: Math.floor(totalDatasets * 0.3)     // Estimate
      }));
      
      // Generate alerts from data
      const newAlerts = [];
      const progressPct = labelingData.progress_percentage || 0;
      
      if (progressPct < 50) {
        newAlerts.push({
          type: 'warning',
          message: `Only ${progressPct.toFixed(1)}% of records labeled`,
          time: 'now'
        });
      }
      
      if (unlabeledCount > 1000) {
        newAlerts.push({
          type: 'info',
          message: `${unlabeledCount.toLocaleString()} records need labeling`,
          time: 'now'
        });
      }
      
      if (totalDatasets === 0) {
        newAlerts.push({
          type: 'info',
          message: 'No datasets uploaded yet. Upload your first dataset to get started.',
          time: 'now'
        });
      }
      
      setAlerts(newAlerts);
      
      // ========================================
      // FETCH MODEL PERFORMANCE DATA
      // ========================================
      try {
        // Get latest completed training jobs for performance metrics (user-filtered)
        const completedJobs = userJobs.filter(job => 
          job.status === 'completed' && job.oof_auc
        ) || [];
        
        if (completedJobs.length > 0) {
          // Sort by completion date, most recent first
          completedJobs.sort((a, b) => 
            new Date(b.completed_at) - new Date(a.completed_at)
          );
          
          const latestJob = completedJobs[0];
          const latestMetrics = latestJob.metrics || {};
          
          setModelPerformance({
            accuracy: parseFloat(((latestMetrics.accuracy || latestJob.oof_auc || 0) * 100).toFixed(2)),
            rocAuc: latestJob.oof_auc || 0,
            precision: parseFloat(((latestMetrics.precision || 0) * 100).toFixed(2)),
            f1Score: parseFloat(((latestMetrics.f1_score || 0) * 100).toFixed(2)),
            runs: completedJobs.slice(0, 3).map((job, idx) => ({
              id: `#${job.id || idx + 101}`,
              model: job.model_name || job.job_type?.replace('_', ' ') || 'Model',
              accuracy: ((job.oof_auc || 0) * 100).toFixed(1),
              status: job.status === 'completed' ? 'Ready' : 'Failed'
            }))
          });
        }
      } catch (err) {
        console.error('Error loading model performance:', err);
      }
      
      // ========================================
      // FETCH FEATURE IMPORTANCE
      // ========================================
      try {
        // Get latest model for feature importance (use filtered userModels)
        if (userModels && userModels.length > 0) {
          const latestModel = userModels[0];
          const importanceData = await explainabilityAPI.getGlobalFeatureImportance(latestModel.id);
          
          if (importanceData.feature_importance) {
            const topFeatures = importanceData.feature_importance
              .slice(0, 4)
              .map(f => ({
                name: f.feature || f.name,
                score: f.importance >= 0 ? `+${f.importance.toFixed(2)}` : f.importance.toFixed(2)
              }));
            setFeatureImportance(topFeatures);
          }
        }
      } catch (err) {
        console.error('Error loading feature importance:', err);
        // Set default features if backend fails
        setFeatureImportance([
          { name: 'ANA Level', score: '+0.00' },
          { name: 'Age', score: '+0.00' },
          { name: 'ESR', score: '+0.00' },
          { name: 'Gender', score: '+0.00' }
        ]);
      }
      
      // ========================================
      // CALCULATE DATA QUALITY METRICS
      // ========================================
      try {
        const totalRecordCount = totalRecords || 0;
        const missingCount = unlabeledCount || 0;
        const missingPct = totalRecordCount > 0 && missingCount > 0 ? (missingCount / totalRecordCount) * 100 : 0;
        
        // Calculate data quality issues count (missing + estimated outliers)
        const estimatedOutliers = Math.floor(totalRecordCount * 0.05); // Estimate 5% outliers
        const qualityIssuesCount = missingCount + estimatedOutliers;
        
        // Calculate class imbalance from labeling data
        const labeledPct = totalRecordCount > 0 ? (labeledCount / totalRecordCount) * 100 : 50;
        const unlabeledPct = 100 - labeledPct;
        
        // Update stats with data quality metrics
        setStats(prev => ({
          ...prev,
          dataQualityIssues: qualityIssuesCount,
          dataQualityMissingPct: missingPct
        }));
        
        setDataQuality({
          missingPercent: missingPct,
          classImbalance: { 
            hospital_a: Math.round(labeledPct), 
            hospital_b: Math.round(unlabeledPct) 
          },
          outliers: estimatedOutliers,
          dataSources: { 
            count: uploadsData.uploads?.length || 0, 
            distribution: `${Math.round(labeledPct)}%` 
          }
        });
      } catch (err) {
        console.error('Error calculating data quality:', err);
      }
      
      // ========================================
      // FETCH GPU USAGE DATA
      // ========================================
      try {
        const systemInfoResponse = await fetch('/api/admin/system-info', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (systemInfoResponse.ok) {
          const systemInfo = await systemInfoResponse.json();
          
          if (systemInfo.gpu && systemInfo.gpu.gpu_available) {
            const gpuMemUsed = systemInfo.gpu.gpu_memory_allocated_gb || 0;
            const gpuMemTotal = systemInfo.gpu.gpu_memory_total_gb || 24;
            const gpuUsagePct = Math.round((gpuMemUsed / gpuMemTotal) * 100);
            
            setStats(prev => ({
              ...prev,
              gpuUsagePercent: gpuUsagePct,
              gpuMemoryUsed: gpuMemUsed,
              gpuMemoryTotal: gpuMemTotal
            }));
          }
        }
      } catch (err) {
        console.error('Error fetching GPU info:', err);
        // Keep default values on error
      }
      
      // ========================================
      // UNIFIED ACTIVITY FEED - USER-SPECIFIC
      // ========================================
      const allActivities = [];
      
      // 1. Upload activities (use filtered userUploads)
      userUploads.forEach(upload => {
        const fileName = upload.file_name || upload.dataset_name || 'Unnamed dataset';
        const rowCount = upload.row_count || 0;
        
        allActivities.push({
          timestamp: new Date(upload.uploaded_at || upload.created_at),
          user: upload.uploaded_by || 'System',
          activity: `Uploaded ${fileName} (${rowCount.toLocaleString()} rows)`,
          status: upload.is_deleted ? 'error' : 'success',
          type: 'upload'
        });
      });
      
      // 2. Training job activities (use filtered userJobs)
      userJobs.forEach(job => {
        const userName = job.user_full_name || job.username || 'Unknown User';
        const modelName = job.model_name || job.job_type?.replace('_', ' ');
        
        // Job started
        if (job.created_at) {
          allActivities.push({
            timestamp: new Date(job.created_at),
            user: userName,
            activity: `Started training: ${modelName}`,
            status: 'info',
            type: 'training_start'
          });
        }
        
        // Job completed/failed
        if (job.completed_at) {
          const isSuccess = job.status === 'completed';
          const aucText = job.oof_auc ? ` (AUC: ${job.oof_auc.toFixed(3)})` : '';
          allActivities.push({
            timestamp: new Date(job.completed_at),
            user: userName,
            activity: isSuccess 
              ? `Completed training: ${modelName}${aucText}`
              : `Training failed: ${modelName}`,
            status: isSuccess ? 'success' : 'error',
            type: isSuccess ? 'training_complete' : 'training_failed'
          });
        }
      });
      
      // 3. Model deployment activities (use filtered userModels)
      userModels.forEach(model => {
        if (model.trained_at) {
          allActivities.push({
            timestamp: new Date(model.trained_at),
            user: 'System', // Models don't have user info yet
            activity: `Model deployed: ${model.model_name} (${model.model_type})`,
            status: 'info',
            type: 'model_deploy'
          });
        }
      });
      
      // Sort by timestamp (most recent first) and take top 20
      allActivities.sort((a, b) => b.timestamp - a.timestamp);
      
      // Format for display
      const formattedActivities = allActivities.slice(0, 20).map((activity, idx) => ({
        no: idx + 1,
        user: activity.user,
        time: formatTimeAgo(activity.timestamp),
        activity: activity.activity,
        status: activity.status,
        type: activity.type
      }));
      
      setRecentActivity(formattedActivities);
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      if (error.response?.status === 401) {
        navigate('/login');
      } else {
        // Show error alert
        setAlerts([{
          type: 'error',
          message: 'Failed to load dashboard data. Showing partial information.',
          time: 'now'
        }]);
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Helper function to format time ago
  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return 'yesterday';
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch (e) {
      return 'Unknown'
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-purple-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-gray-muted">Loading platform...</p>
        </div>
      </div>
    );
  }

  // Get current time greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Format current date
  const getCurrentDate = () => {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date().toLocaleDateString('en-US', options);
  };

  const handleMissionControlClose = () => {
    sessionStorage.setItem('mc_dismissed', '1');
    setShowMissionControl(false);
  };

  return (
    <DashboardLayout>
      <MissionControlModal
        isOpen={showMissionControl}
        onClose={handleMissionControlClose}
      />
      
      {/* ═══ PAGE HEADER ═══ */}
      <PageHeader title="Dashboard" user={user} />

      {/* ═══ CONTENT ═══ */}
      <main className="flex-1 overflow-y-auto p-6 transition-colors relative" style={{ 
        zoom: 0.78,
        background: '#FAFBFC'
      }}>
        {/* ── Ambient glow orbs ── */}
        <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden" style={{ zIndex: 0 }}>
          {/* Top-right: large soft violet orb */}
          <div style={{
            position: 'absolute', top: '-120px', right: '-100px',
            width: '520px', height: '520px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%, rgba(139,92,246,0.03) 45%, transparent 70%)',
            filter: 'blur(40px)',
          }} />
          {/* Bottom-left: indigo orb */}
          <div style={{
            position: 'absolute', bottom: '80px', left: '-80px',
            width: '420px', height: '420px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.055) 0%, rgba(99,102,241,0.02) 50%, transparent 70%)',
            filter: 'blur(50px)',
          }} />
          {/* Centre-right: warm rose accent */}
          <div style={{
            position: 'absolute', top: '38%', right: '8%',
            width: '280px', height: '280px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(236,72,153,0.035) 0%, transparent 65%)',
            filter: 'blur(35px)',
          }} />
          {/* Mid-left: sky accent */}
          <div style={{
            position: 'absolute', top: '20%', left: '14%',
            width: '200px', height: '200px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(14,165,233,0.04) 0%, transparent 65%)',
            filter: 'blur(30px)',
          }} />
          {/* Subtle noise-like grid overlay for depth */}
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: `
              linear-gradient(rgba(15,23,42,0.012) 1px, transparent 1px),
              linear-gradient(90deg, rgba(15,23,42,0.012) 1px, transparent 1px)
            `,
            backgroundSize: '48px 48px',
          }} />
        </div>

        {/* All content sits above orbs */}
        <div className="relative" style={{ zIndex: 1 }}>
        {/* Hero Header - Premium Executive Style */}
        <motion.div 
          className="mb-5 relative"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="relative py-5">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-syne text-[28px] font-semibold leading-tight mb-1.5 text-[#0A0118] tracking-tight">
                  Welcome back, {user?.full_name?.split(' ')[0] || 'Nasrin'}
                </h1>
                <div className="space-y-0.5">
                  <p className="text-[13px] text-[#1A0633] font-semibold tracking-wide">
                    Autoimmune Intelligence Platform
                  </p>
                  <div className="flex items-center gap-4 text-[11px] text-[#64748B]">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                      System status: <span className="font-semibold text-green-600">Operational</span>
                    </span>
                    <span className="text-[#94A3B8]">•</span>
                    <span>
                      Last sync: <span className="font-medium">Today at {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => navigate('/data-preparation')}
                className="flex items-center gap-2 px-5 py-2.5 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all hover:scale-105"
                style={{ background: 'linear-gradient(135deg, #0A0118 0%, #1A0633 100%)' }}
              >
                <Upload className="w-4 h-4" />
                <span>Upload File Now</span>
              </button>
            </div>
          </div>
        </motion.div>

        {/* Greeting Card - OPTION 1: Darker Card (COMMENTED - uncomment to use) */}
        {/*
        <motion.div 
          className="mb-5 relative"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          whileHover={{ scale: 1.01 }}
        >
          <div className="relative bg-gradient-to-br from-purple-900 via-indigo-900 to-purple-950 dark:from-purple-950/80 dark:via-indigo-950/80 dark:to-purple-950/80 rounded-2xl border-2 border-purple-500/60 dark:border-purple-400/40 p-5 shadow-[0_20px_60px_rgba(168,85,247,0.5)] dark:shadow-[0_20px_60px_rgba(168,85,247,0.3)] backdrop-blur-sm relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 via-fuchsia-600/20 to-purple-600/20 animate-gradient" style={{ backgroundSize: '200% 200%' }}></div>
            <div className="flex items-center justify-between relative z-10">
              <div>
                <h1 className="font-syne text-[22px] font-bold text-white drop-shadow-lg leading-tight mb-1.5">
                  {getGreeting()}, <span className="text-purple-200 dark:text-purple-300">{user?.username || 's.nasrin'}</span>
                </h1>
                <p className="text-[13px] text-purple-100/90 dark:text-purple-200/70">
                  {getCurrentDate()} · Last Updated: Today
                </p>
              </div>
            </div>
          </div>
        </motion.div>
        */}

        {/* Phase 3: Status Cards Row - 4 Cards */}
        <motion.div 
          className="grid grid-cols-4 gap-4 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <motion.div whileHover={{ scale: 1.02, y: -3 }} transition={{ type: "spring", stiffness: 300 }}>
            <DatasetStatusCard 
              count={stats.totalDatasets}
            />
          </motion.div>
          <motion.div whileHover={{ scale: 1.02, y: -3 }} transition={{ type: "spring", stiffness: 300 }}>
            <DataQualityCard 
              issues={stats.dataQualityIssues}
              missingPercent={stats.dataQualityMissingPct}
            />
          </motion.div>
          <motion.div whileHover={{ scale: 1.02, y: -3 }} transition={{ type: "spring", stiffness: 300 }}>
            <GPUStatusCard 
              percentage={stats.gpuUsagePercent}
              used={stats.gpuMemoryUsed.toFixed(1)}
              total={stats.gpuMemoryTotal.toFixed(0)}
            />
          </motion.div>
          <motion.div whileHover={{ scale: 1.02, y: -3 }} transition={{ type: "spring", stiffness: 300 }}>
            <TrainedModelsCard 
              count={stats.modelsDeployed}
              training={stats.trainingJobs}
            />
          </motion.div>
        </motion.div>

        {/* Recent Predictions Panel */}
        <RecentPredictionsPanel navigate={navigate} />

        {/* Phase 3: Main Dashboard Layout */}
        <div className="grid grid-cols-[minmax(0,1fr),380px] gap-4 mb-4">
          <div className="flex flex-col gap-4">
            <ModelPerformancePanel 
              performance={modelPerformance}
            />

            <DataQualityOverviewPanel 
              compact
              data={dataQuality}
            />
          </div>

          <FeatureImportancePanel 
            compact
            features={featureImportance}
          />
        </div>
        </div>{/* end z-index wrapper */}
      </main>
    </DashboardLayout>
  );
}

// ═══ COMPONENTS ═══

function MetricCard({ label, value, subtitle, icon, color }) {
  return (
    <motion.div 
      className="relative group"
      whileHover={{ scale: 1.02, y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      {/* Subtle glow on hover */}
      <div className="absolute -inset-0.5 rounded-xl blur opacity-0 group-hover:opacity-30 transition-opacity duration-500" 
           style={{ background: `linear-gradient(135deg, ${color}40, ${color}20)` }}>
      </div>
      
      <div className="relative bg-white rounded-xl border border-gray-200/60 shadow-sm group-hover:shadow-lg transition-all overflow-hidden">
        {/* TOP ACCENT BAR */}
        <div className="h-[3px]" style={{ backgroundColor: color }} />

        <div className="p-4 flex items-center gap-4">
          {/* Icon */}
          <div className="flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
            <div style={{ color: color }}>
              {icon}
            </div>
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Label */}
            <div className="text-[11px] font-medium text-[#888] uppercase tracking-wider mb-1">
              {label}
            </div>
            
            {/* Value */}
            <div className="text-[32px] font-semibold text-[#111] leading-none mb-1">
              {value}
            </div>
            
            {/* Subtitle */}
            <div className="text-[12px] text-[#888]">
              {subtitle}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StatCardClean({ value, label, status, trend }) {
  const getStatusBadge = () => {
    if (trend) return <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded bg-[rgba(22,163,74,0.09)] text-[#16A34A]">{trend}</span>;
    if (status === 'running') return <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded bg-[rgba(123,92,240,0.10)] text-[#7B5CF0]">2 running</span>;
    if (status === 'active') return <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded bg-[rgba(123,92,240,0.10)] text-[#7B5CF0]">Active</span>;
    if (status === 'live') return <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded bg-[rgba(123,92,240,0.10)] text-[#7B5CF0]">Live</span>;
    return null;
  };

  return (
    <div 
      className="bg-white rounded-xl border border-gray-200 border-t-[3px] border-t-[#5d0696] px-4 py-3.5 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all"
      style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 0 20px 0 rgba(123, 92, 240, 0.08)' }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="w-8 h-8 rounded-lg bg-[rgba(123,92,240,0.10)] flex items-center justify-center">
          <Database className="w-3.5 h-3.5 text-[#7B5CF0]" />
        </div>
        {getStatusBadge()}
      </div>
      <div className="font-syne text-[24px] font-bold text-[#0F0F11] leading-none">{value}</div>
      <div className="text-[10.5px] text-[#8585A0] font-medium mt-2">{label}</div>
    </div>
  );
}

function ActivityRow({ no, user, time, activity, status }) {
  // Generate profile image with first letter of username
  const getInitials = (username) => {
    return username.charAt(0).toUpperCase();
  };

  // Color variations for profile avatars
  const colorMap = {
    'testp22026': 'bg-[#7B5CF0]',
    'researcher_a': 'bg-[#10B981]',
    'researcher_b': 'bg-[#3B82F6]',
    'dr_ahmad': 'bg-[#F59E0B]',
    'dr_lim': 'bg-[#EF4444]'
  };

  const renderStatusIcon = () => {
    switch(status) {
      case 'success':
        return (
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#10B981" fillOpacity="0.15"/>
            <path d="M5 8l2 2 4-4" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#EF4444" fillOpacity="0.15"/>
            <path d="M10 6L6 10M6 6l4 4" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
            <path d="M8 1L1 14h14L8 1z" fill="#F59E0B" fillOpacity="0.15"/>
            <path d="M8 6v3M8 11h.01" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      case 'info':
        return (
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#7B5CF0" fillOpacity="0.15"/>
            <path d="M8 7v4M8 5h.01" stroke="#7B5CF0" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <tr className="hover:bg-white/50 transition-colors border-b border-gray-200 last:border-0">
      <td className="px-3 py-2.5 text-[#8585A0]">{no}</td>
      <td className="px-3 py-2.5">
        <div className="flex items-center gap-2">
          <div className={`w-6 h-6 rounded-full ${colorMap[user] || 'bg-gray-400'} flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0`}>
            {getInitials(user)}
          </div>
          <span className="text-[#0F0F11] font-medium">{user}</span>
        </div>
      </td>
      <td className="px-3 py-2.5 text-[#8585A0]">{time}</td>
      <td className="px-3 py-2.5 text-[#0F0F11]">{activity}</td>
      <td className="px-3 py-2.5 text-center">
        <div className="flex justify-center">
          {renderStatusIcon()}
        </div>
      </td>
    </tr>
  );
}

function LogEntry({ time, type, msg }) {
  const renderIcon = () => {
    switch(type) {
      case 'success':
        return (
          <svg className="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#10B981" fillOpacity="0.15"/>
            <path d="M5 8l2 2 4-4" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        );
      case 'error':
        return (
          <svg className="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#EF4444" fillOpacity="0.15"/>
            <path d="M10 6L6 10M6 6l4 4" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 16 16" fill="none">
            <path d="M8 1L1 14h14L8 1z" fill="#F59E0B" fillOpacity="0.15"/>
            <path d="M8 6v3M8 11h.01" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      case 'info':
        return (
          <svg className="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="#7B5CF0" fillOpacity="0.15"/>
            <path d="M8 7v4M8 5h.01" stroke="#7B5CF0" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        );
      default:
        return null;
    }
  };
  
  return (
    <div className="flex gap-3 text-[12px] hover:bg-white/40 px-2 py-1.5 rounded-lg transition-colors font-mono">
      <span className="text-[#8585A0] flex-shrink-0">{time}</span>
      {renderIcon()}
      <span className="text-[#0F0F11]">{msg}</span>
    </div>
  );
}

// Recent Predictions Panel Component
function RecentPredictionsPanel({ navigate }) {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const { predictionHistoryAPI } = await import('../services/api-complete');
        const response = await predictionHistoryAPI.getHistory(5); // Get last 5 predictions
        setPredictions(response.predictions || []);
      } catch (error) {
        console.error('[Dashboard] Error loading predictions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  if (loading) {
    return (
      <motion.div
        className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm mb-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <div className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-4 border-purple-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      </motion.div>
    );
  }

  if (predictions.length === 0) {
    return null; // Don't show panel if no predictions
  }

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  return (
    <motion.div
      className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm mb-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Recent Predictions</h3>
        <button 
          className="text-xs text-purple-600 hover:text-purple-700 font-medium"
          onClick={() => navigate('/predictions-history')}
        >
          View All →
        </button>
      </div>
      
      <div className="grid grid-cols-5 gap-3">
        {predictions.slice(0, 5).map((prediction, idx) => {
          const colorClasses = [
            { bg: 'bg-purple-50', icon: 'text-purple-600', iconBg: 'bg-purple-100' },
            { bg: 'bg-blue-50', icon: 'text-blue-600', iconBg: 'bg-blue-100' },
            { bg: 'bg-green-50', icon: 'text-green-600', iconBg: 'bg-green-100' },
            { bg: 'bg-orange-50', icon: 'text-orange-600', iconBg: 'bg-orange-100' },
            { bg: 'bg-pink-50', icon: 'text-pink-600', iconBg: 'bg-pink-100' }
          ];
          const colors = colorClasses[idx % 5];
          
          return (
            <div 
              key={prediction.batch_id}
              onClick={() => navigate('/predictions-history')}
              className={`flex items-start gap-3 p-3 ${colors.bg} rounded-lg hover:shadow-sm transition-all cursor-pointer`}
            >
              <div className={`w-8 h-8 rounded-lg ${colors.iconBg} flex items-center justify-center flex-shrink-0`}>
                <Brain className={`w-4 h-4 ${colors.icon}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-gray-900 truncate">{prediction.model_name}</div>
                <div className="text-xs text-gray-600 truncate">{prediction.total_predictions} predictions</div>
                <div className="text-xs text-gray-400 mt-1">{formatDate(prediction.predicted_at)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
