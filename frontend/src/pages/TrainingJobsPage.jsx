/**
 * Training Jobs Page - Enhanced with Model Selection & API Integration
 * Complete ML training workflow: Select models → Configure → Train → Monitor → Results
 */
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
  RefreshCw,
  Calendar,
  Plus,
  ArrowDown,
  Lock,
  Layers,
  GitBranch,
  Sparkles,
  Settings,
  Database,
  Activity,
  XCircle,
  PlayCircle,
  Users,
  X,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  FolderOpen
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import ModelingStepsNav from '../components/ModelingStepsNav';
import PageHeader from '../components/PageHeader';
import { authAPI } from '../services/api';
import { mlPreparationAPI, trainingAPI } from '../services/api-complete';
import { flexibleAPI } from '../services/api';

// Available ML Algorithms - ALL 13 MODELS FROM RESEARCH FRAMEWORK
const AVAILABLE_MODELS = [
  { id: 'xgboost', name: 'XGBoost', icon: Zap, category: 'Gradient Boosting', implemented: true, speed: 'Fast', interpretability: 'Medium' },
  { id: 'lightgbm', name: 'LightGBM', icon: Cpu, category: 'Gradient Boosting', implemented: true, speed: 'Very Fast', interpretability: 'Medium' },
  { id: 'catboost', name: 'CatBoost', icon: Database, category: 'Gradient Boosting', implemented: true, speed: 'Moderate', interpretability: 'High' },
  { id: 'gradient_boosting', name: 'Gradient Boosting', icon: TrendingUp, category: 'Gradient Boosting', implemented: true, speed: 'Moderate', interpretability: 'Medium' },
  { id: 'random_forest', name: 'Random Forest', icon: GitBranch, category: 'Ensemble', implemented: true, speed: 'Moderate', interpretability: 'Medium' },
  { id: 'adaboost', name: 'AdaBoost', icon: Activity, category: 'Ensemble', implemented: true, speed: 'Fast', interpretability: 'Medium' },
  { id: 'decision_tree', name: 'Decision Tree', icon: GitBranch, category: 'Trees', implemented: true, speed: 'Very Fast', interpretability: 'Very High' },
  { id: 'svm', name: 'SVM', icon: Layers, category: 'Linear & Distance', implemented: true, speed: 'Slow', interpretability: 'Low' },
  { id: 'knn', name: 'K-Nearest Neighbors', icon: Users, category: 'Linear & Distance', implemented: true, speed: 'Fast', interpretability: 'High' },
  { id: 'logistic_regression', name: 'Logistic Regression', icon: BarChart3, category: 'Linear & Distance', implemented: true, speed: 'Very Fast', interpretability: 'Very High' },
  { id: 'ridge_classifier', name: 'Ridge Classifier', icon: BarChart3, category: 'Linear & Distance', implemented: true, speed: 'Very Fast', interpretability: 'Very High' },
  { id: 'linear_discriminant', name: 'Linear Discriminant Analysis', icon: Layers, category: 'Linear & Distance', implemented: true, speed: 'Very Fast', interpretability: 'Very High' },
  { id: 'mlp', name: 'ANN (MLP)', icon: Brain, category: 'Neural Network', implemented: true, speed: 'Moderate', interpretability: 'Low' }
];

export default function TrainingJobsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  
  // Load user data
  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
      }
    };
    loadUser();
  }, []);
  
  // State management
  const [showNewRunDialog, setShowNewRunDialog] = useState(false);
  const [expandedActiveJobs, setExpandedActiveJobs] = useState(new Set());
  const [expandedHistoryJobs, setExpandedHistoryJobs] = useState(new Set());
  const [selectedModels, setSelectedModels] = useState([]);
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [activeRun, setActiveRun] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState([]);
  
  // Ensemble training state
  const [showEnsembleDialog, setShowEnsembleDialog] = useState(false);
  const [isTrainingEnsemble, setIsTrainingEnsemble] = useState(false);
  const [ensembleStatus, setEnsembleStatus] = useState('');

  // Training history state
  const [trainingHistory, setTrainingHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [expandedSessions, setExpandedSessions] = useState(new Set(['session-0']));  // open newest by default
  const [historyPage, setHistoryPage] = useState(1);
  const SESSIONS_PER_PAGE = 5;
  const [historySearch, setHistorySearch] = useState('');
  // History ensemble state
  const [historyEnsembleSession, setHistoryEnsembleSession] = useState(null);
  const [historyEnsembleLoading, setHistoryEnsembleLoading] = useState(false);
  const [historyEnsembleJobs, setHistoryEnsembleJobs] = useState({});
  
  // Loading states for better UX
  const [isPreparingDataset, setIsPreparingDataset] = useState(false);
  const [datasetPrepStatus, setDatasetPrepStatus] = useState('');
  const [isStartingTraining, setIsStartingTraining] = useState(false);
  
  // Training configuration
  const [config, setConfig] = useState({
    batchId: null,  // Selected dataset batch ID
    targetColumn: 'labels_disease_classification',  // Disease classification for autoimmune dataset
    testSize: 0.35,  // Research framework: 65% train / 35% test (n=67 train, n=37 test)
    nTrials: 30,    // Optuna trials for hyperparameter optimization
    cvFolds: 5,     // 5-fold cross-validation (research standard)
    randomState: 42
  });

  // Load batch_id and target_column from navigation state or sessionStorage (from ML Prep workflow)
  useEffect(() => {
    // Priority 1: Navigation state (passed from DataPreparationPage)
    if (location.state?.dataset_id || location.state?.target_column) {
      console.log('[Training] Loaded from navigation state:', location.state);
      setConfig(prev => ({
        ...prev,
        batchId: location.state.dataset_id || prev.batchId,
        targetColumn: location.state.target_column || prev.targetColumn
      }));
      
      // Also update sessionStorage for persistence
      if (location.state.dataset_id) {
        sessionStorage.setItem('current_batch_id', location.state.dataset_id);
      }
      if (location.state.target_column) {
        sessionStorage.setItem('current_target_column', location.state.target_column);
      }
      // Auto-open the wizard when navigated from ML Queue
      setShowNewRunDialog(true);
      return; // Skip sessionStorage check if we have navigation state
    }
    
    // Priority 2: sessionStorage (from previous session or direct navigation)
    const savedBatchId = sessionStorage.getItem('current_batch_id');
    const savedTargetColumn = sessionStorage.getItem('current_target_column');
    
    if (savedBatchId || savedTargetColumn) {
      console.log('[Training] Loaded from session - batch:', savedBatchId, 'target:', savedTargetColumn);
      setConfig(prev => ({ 
        ...prev, 
        batchId: savedBatchId || prev.batchId,
        targetColumn: savedTargetColumn || prev.targetColumn
      }));
    }
    
    // Load active training run from sessionStorage (for persistence across pages)
    const savedActiveRun = sessionStorage.getItem('active_training_run');
    if (savedActiveRun) {
      try {
        const run = JSON.parse(savedActiveRun);
        console.log('[Training] Restored active training run from session:', run);
        setActiveRun(run);
      } catch (error) {
        console.error('[Training] Failed to parse saved training run:', error);
        sessionStorage.removeItem('active_training_run');
      }
    }
  }, [location.state]);

  // Dataset selection
  const [availableDatasets, setAvailableDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [datasetPage, setDatasetPage] = useState(1);  // for "load more"
  const DATASET_PAGE_SIZE = 10;

  // Fetch available datasets — default to 10 most recent
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        console.log('[Training] Fetching datasets...');
        const response = await flexibleAPI.getRecentUploads(50, true, true);
        console.log('[Training] Got uploads:', response.uploads?.length || 0);
        
        if (!response.uploads || response.uploads.length === 0) {
          setAvailableDatasets([]);
          return;
        }
        
        const datasets = response.uploads
          .filter(upload => upload.row_count > 0)
          // sort newest first
          .sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at))
          .map(upload => ({
            batch_id: upload.id,
            original_filename: upload.file_name,
            uploaded_at: upload.uploaded_at,
            record_count: upload.row_count || 0,
            labeled_count: upload.row_count || 0,
            dataset_type: upload.dataset_type || 'General',
            source: upload.source || 'Upload',
            is_staging: upload.source === 'staging',
            isToday: new Date(upload.uploaded_at).toDateString() === new Date().toDateString(),
          }));
        
        console.log('[Training] Datasets transformed:', datasets.length);
        setAvailableDatasets(datasets);
        
        // Auto-select: navigation state > sessionStorage > newest (first in sorted list)
        const targetBatchId = location.state?.dataset_id || 
                              sessionStorage.getItem('current_batch_id') || 
                              config.batchId;
        
        if (targetBatchId && datasets.length > 0) {
          const match = datasets.find(d => d.batch_id === targetBatchId);
          setSelectedDataset(match || datasets[0]);
        } else if (datasets.length > 0 && !selectedDataset) {
          setSelectedDataset(datasets[0]);  // always default to newest
        }
        
      } catch (error) {
        console.error('[Training] Error fetching datasets:', error);
        setAvailableDatasets([]);
      }
    };
    
    fetchDatasets();
  }, [location.state, config.batchId]);

  // Sync config.batchId with selectedDataset
  useEffect(() => {
    if (selectedDataset && selectedDataset.batch_id !== config.batchId) {
      console.log('[Training] Syncing config.batchId with selectedDataset:', selectedDataset.batch_id);
      setConfig(prev => ({ ...prev, batchId: selectedDataset.batch_id }));
    }
  }, [selectedDataset]);

  // Poll active training run (every 3 seconds)
  useEffect(() => {
    if (!activeRun) return;
    
    const interval = setInterval(async () => {
      try {
        let allCompleted = true;
        const updatedJobs = { ...activeRun.jobs };
        
        // Poll each job in the active run
        for (const [modelId, job] of Object.entries(activeRun.jobs)) {
          if (job.status !== 'completed' && job.status !== 'failed') {
            allCompleted = false;
            const statusData = await trainingAPI.getJobStatus(job.job_id);
            
            updatedJobs[modelId] = {
              ...job,
              status: statusData.status,
              progress: statusData.progress?.percentage || 0,
              result: statusData.result
            };
          }
        }
        
        const updatedRun = {
          ...activeRun,
          jobs: updatedJobs
        };
        
        setActiveRun(updatedRun);
        
        // Save to sessionStorage for persistence
        sessionStorage.setItem('active_training_run', JSON.stringify(updatedRun));
        
        // Check if all non-ensemble jobs done, AND if ensemble exists it's also terminal
        const hasEnsemble = !!updatedJobs['ensemble'];
        const ensembleTerminal = !hasEnsemble || ['completed', 'failed'].includes(updatedJobs['ensemble']?.status);
        if (allCompleted && ensembleTerminal) {
          const completedModelIds = Object.entries(updatedJobs)
            .filter(([_, job]) => job.status === 'completed' && job.result?.model_id)
            .map(([_, job]) => job.result.model_id);
          
          if (completedModelIds.length > 0) {
            sessionStorage.setItem('trained_model_ids', JSON.stringify(completedModelIds));
            sessionStorage.setItem('workflow_stage', 'model_comparison');
            console.log('[Training] All models complete. Model IDs:', completedModelIds);
          }
          
          // Clear active run after brief delay to show completion
          setTimeout(() => {
            sessionStorage.removeItem('active_training_run');
            setActiveRun(null);
            refreshHistory(); // auto-refresh history list after run finishes
          }, 5000);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [activeRun]);

  // Fetch training history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      setLoadingHistory(true);
      try {
        const data = await trainingAPI.getTrainingHistory(100);
        const jobs = (data.jobs || []).filter(j => j.job_type === 'base_model' || j.job_type === 'base_model_training');
        setTrainingHistory(jobs);
      } catch (error) {
        console.error('[Training] Failed to fetch history:', error);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, []);

  const refreshHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await trainingAPI.getTrainingHistory(100);
      const jobs = (data.jobs || []).filter(j => j.job_type === 'base_model' || j.job_type === 'base_model_training');
      setTrainingHistory(jobs);
    } catch (error) {
      console.error('[Training] Failed to refresh history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Toggle model selection
  const toggleModel = (modelId) => {
    setSelectedModels(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  // Start new training run
  const startTrainingRun = async () => {
    try {
      // Validate dataset selection
      if (!config.batchId) {
        alert('Please select a dataset first');
        return;
      }

      console.log('[Training] ========== STARTING TRAINING ==========');
      console.log('[Training] Batch ID:', config.batchId);
      console.log('[Training] Target Column:', config.targetColumn);
      console.log('[Training] Selected Dataset:', selectedDataset);
      console.log('[Training] Full Config:', config);
      
      setIsPreparingDataset(true);
      setDatasetPrepStatus('Initializing dataset preparation...');

      // Step 1: Prepare dataset using mlPreparationAPI
      console.log('[Training] Preparing dataset with config:', config);
      const datasetResponse = await mlPreparationAPI.prepareDataset(config.batchId, {
        targetColumn: config.targetColumn,
        testSize: config.testSize,
        randomState: config.randomState
      });
      
      const datasetJobId = datasetResponse.job_id;  // Backend returns job_id, not dataset_id
      console.log('[Training] Dataset preparation job started:', datasetJobId);
      
      // Step 1.5: Wait for dataset preparation to complete (poll status)
      setDatasetPrepStatus('Preparing dataset (splitting train/test, scaling features)...');
      let datasetReady = false;
      let attempts = 0;
      const maxAttempts = 60; // 60 attempts * 2s = 2 minutes max wait
      
      while (!datasetReady && attempts < maxAttempts) {
        try {
          const statusResponse = await trainingAPI.getJobStatus(datasetJobId);
          console.log(`[Training] Dataset job status (attempt ${attempts + 1}):`, statusResponse.status, statusResponse);
          
          setDatasetPrepStatus(`Preparing dataset... (${attempts + 1}/${maxAttempts}) - Status: ${statusResponse.status}`);
          
          if (statusResponse.status === 'completed') {
            datasetReady = true;
            setDatasetPrepStatus('Dataset ready! Starting model training...');
            console.log('[Training] Dataset preparation completed!');
          } else if (statusResponse.status === 'failed') {
            // Backend returns error_message, not error
            throw new Error('Dataset preparation failed: ' + (statusResponse.error_message || statusResponse.error || 'Unknown error'));
          }
          
          if (!datasetReady) {
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
            attempts++;
          }
        } catch (error) {
          console.error('[Training] Error checking dataset status:', error);
          throw new Error('Failed to prepare dataset: ' + error.message);
        }
      }
      
      if (!datasetReady) {
        throw new Error('Dataset preparation timed out after 2 minutes');
      }
      
      setIsPreparingDataset(false);
      setIsStartingTraining(true);
      
      // Step 2: Start training selected models
      const jobs = {};
      for (const modelId of selectedModels) {
        console.log('[Training] Starting training for:', modelId);
        setDatasetPrepStatus(`Queueing ${modelId} for training...`);
        
        const response = await trainingAPI.trainBaseModel({
          model_name: modelId,
          dataset_id: datasetJobId,  // Use the job_id from dataset preparation
          n_trials: config.nTrials || 100,
          cv_folds: config.cvFolds || 5,
          use_selected_features: true
        });
        
        jobs[modelId] = {
          job_id: response.job_id,
          model_name: modelId,
          status: 'queued',
          progress: 0
        };
      }
      
      // Create active run
      const newRun = {
        id: `run-${Date.now()}`,
        name: `${selectedModels.length}-Model Training Run`,
        datasetId: datasetJobId,
        startedAt: new Date().toISOString(),
        jobs
      };
      
      console.log('[Training] Training run created:', newRun);
      setActiveRun(newRun);
      
      // Save to sessionStorage for persistence across pages
      sessionStorage.setItem('active_training_run', JSON.stringify(newRun));
      
      setShowNewRunDialog(false);
      setIsStartingTraining(false);
      setDatasetPrepStatus('');
      
    } catch (error) {
      console.error('Error starting training run:', error);
      alert('Failed to start training run: ' + error.message);
      setIsPreparingDataset(false);
      setIsStartingTraining(false);
      setDatasetPrepStatus('');
    }
  };

  // Calculate stats
  const activeJobs = activeRun ? Object.values(activeRun.jobs).filter(j => j.status === 'running').length : 0;
  const completedJobs = activeRun ? Object.values(activeRun.jobs).filter(j => j.status === 'completed').length : 0;
  const totalJobs = activeRun ? Object.keys(activeRun.jobs).length : 0;
  
  // Get completed models for comparison
  const completedModels = activeRun ? Object.entries(activeRun.jobs)
    .filter(([_, job]) => job.status === 'completed' && job.result)
    .map(([modelId, job]) => ({
      modelId,
      modelName: AVAILABLE_MODELS.find(m => m.id === modelId)?.name || modelId,
      jobId: job.job_id,  // Include the job ID for ensemble training
      ...job.result
    })) : [];
  
  // Toggle model for comparison
  const toggleComparison = (modelId) => {
    setSelectedForComparison(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };
  
  // Show comparison view
  const handleShowComparison = () => {
    if (completedModels.length >= 2) {
      setSelectedForComparison(completedModels.slice(0, 3).map(m => m.modelId));
      setShowComparison(true);
    }
  };

  // Start ensemble training
  const startEnsembleTraining = async (ensembleConfig) => {
    try {
      setIsTrainingEnsemble(true);
      setEnsembleStatus('Starting ensemble training...');
      
      console.log('[Ensemble] Starting ensemble training with config:', ensembleConfig);
      
      // Get all completed base model job IDs
      const baseModelJobs = completedModels.map(m => m.jobId);
      
      console.log('[Ensemble] Dataset ID:', activeRun.datasetId);
      console.log('[Ensemble] Base model jobs:', baseModelJobs);
      
      // Train ensemble
      const response = await trainingAPI.trainEnsemble({
        datasetId: activeRun.datasetId,  // Fixed: Use datasetId, not datasetJobId
        baseModelJobs: baseModelJobs,
        metaLearnerType: ensembleConfig.metaLearnerType || 'logistic_regression',
        targetColumn: config.targetColumn,
        batchId: config.batchId
      });
      
      console.log('[Ensemble] Ensemble training started:', response.job_id);
      
      // Add ensemble job to activeRun so the polling loop tracks it
      const ensembleJob = {
        job_id: response.job_id,
        model_name: 'ensemble',
        status: 'queued',
        progress: 0,
        result: null
      };
      const updatedRun = {
        ...activeRun,
        jobs: { ...activeRun.jobs, ensemble: ensembleJob }
      };
      setActiveRun(updatedRun);
      sessionStorage.setItem('active_training_run', JSON.stringify(updatedRun));
      
      setShowEnsembleDialog(false);
      setIsTrainingEnsemble(false);
      setEnsembleStatus('');
      
    } catch (error) {
      console.error('[Ensemble] Failed to start ensemble training:', error);
      console.error('[Ensemble] Error details:', error.response?.data);
      setEnsembleStatus('');
      setIsTrainingEnsemble(false);
      
      // Show detailed error message
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`Failed to start ensemble training:\n\n${errorMsg}\n\nDataset ID: ${activeRun?.datasetId}\nBase Models: ${completedModels.map(m => m.jobId).join(', ')}`);
    }
  };

  // Start ensemble training from a history session (not an active run)
  const startHistoryEnsemble = async (session, ensembleConfig) => {
    setHistoryEnsembleLoading(true);
    try {
      const baseModelJobIds = session.jobs
        .filter(j => j.job_type === 'base_model' && j.status === 'completed')
        .map(j => j.job_id);
      const response = await trainingAPI.trainEnsemble({
        datasetId: session.datasetId,
        baseModelJobs: baseModelJobIds,
        metaLearnerType: ensembleConfig.metaLearnerType || 'logistic_regression',
        batchId: session.datasetId,
      });
      setHistoryEnsembleJobs(prev => ({
        ...prev,
        [session.key]: { jobId: response.job_id, status: 'running' }
      }));
      setHistoryEnsembleSession(null);
      // Refresh history at intervals to catch completion
      setTimeout(() => refreshHistory(), 8000);
      setTimeout(() => refreshHistory(), 30000);
      setTimeout(() => refreshHistory(), 90000);
    } catch (error) {
      const msg = error.response?.data?.detail || error.message;
      alert(`Failed to start ensemble: ${msg}`);
    } finally {
      setHistoryEnsembleLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 flex flex-col" style={{ background: '#FFFFFF' }}>
      <PageHeader title="Training Jobs" subtitle="Training" user={user} />
      <ModelingStepsNav />
      <div className="h-screen flex flex-col" style={{ zoom: 0.75, background: '#FFFFFF' }}>

        {/* Stats Bar */}
        {activeRun && (
          <div className="px-6 py-4 bg-white/40 backdrop-blur-sm border-b border-white/20">
            <div className="max-w-7xl mx-auto grid grid-cols-4 gap-4">
              <StatCard icon={Layers} label="Selected Models" value={totalJobs} color="purple" />
              <StatCard icon={Zap} label="Currently Training" value={activeJobs} color="amber" />
              <StatCard icon={CheckCircle} label="Completed" value={completedJobs} color="green" />
              <StatCard icon={BarChart3} label="Progress" value={`${Math.round((completedJobs / totalJobs) * 100)}%`} color="blue" />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Active Training Run */}
            {activeRun && (
              <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className="font-syne text-base font-bold text-black-text">{activeRun.name}</h2>
                    <p className="text-xs text-gray-muted mt-1">
                      Started: {new Date(activeRun.startedAt).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        setActiveRun(null);
                        sessionStorage.removeItem('active_training_run');
                        setShowNewRunDialog(true);
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-primary text-purple-primary hover:bg-purple-dim transition-colors text-xs font-medium"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      New Run
                    </button>
                    <button
                      onClick={() => window.location.reload()}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-xs text-gray-muted"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Refresh
                    </button>
                    {completedModels.length >= 3 && !activeRun.jobs['ensemble'] && (
                      <button
                        onClick={() => {
                          // Scroll down to the inline EnsembleSection
                          document.querySelector('[data-ensemble-section]')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-primary to-blue-500 text-white hover:opacity-90 transition-opacity text-xs font-medium"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        Train Ensemble ({completedModels.length} models) ↓
                      </button>
                    )}
                    {completedModels.length >= 1 && (
                      <button
                        onClick={() => navigate('/model-comparison')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-xs font-medium"
                      >
                        <BarChart3 className="w-3.5 h-3.5" />
                        Go to Model Comparison ({completedModels.length})
                      </button>
                    )}
                  </div>
                </div>
                
                <div className="space-y-3">
                  {Object.entries(activeRun.jobs).map(([modelId, job]) => (
                    <TrainingJobCard
                      key={modelId}
                      job={job}
                      modelInfo={AVAILABLE_MODELS.find(m => m.id === modelId)}
                      isExpanded={expandedActiveJobs.has(modelId)}
                      onToggle={() => setExpandedActiveJobs(prev => {
                        const next = new Set(prev);
                        next.has(modelId) ? next.delete(modelId) : next.add(modelId);
                        return next;
                      })}
                    />
                  ))}

                  {/* Inline Ensemble Section — appears once ≥2 base models complete */}
                  {completedModels.length >= 2 && !activeRun.jobs['ensemble'] && (
                    <div data-ensemble-section>
                    <EnsembleSection
                      completedModels={completedModels}
                      activeRun={activeRun}
                      onStart={startEnsembleTraining}
                      isLoading={isTrainingEnsemble}
                    />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* No Active Run Banner */}
            {!activeRun && (
              <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-purple-dim flex items-center justify-center">
                      <Brain className="w-5 h-5 text-purple-primary" />
                    </div>
                    <div>
                      <h3 className="font-syne text-sm font-bold text-black-text">No Active Training Run</h3>
                      <p className="text-xs text-gray-muted mt-0.5">Select a dataset and models to start a new run</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowNewRunDialog(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium"
                  >
                    <Plus className="w-4 h-4" />
                    New Training Run
                  </button>
                </div>
              </div>
            )}

            {/* Training History — always visible */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h2 className="font-syne text-base font-bold text-black-text">Training History</h2>
                  <p className="text-xs text-gray-muted mt-1">
                    {loadingHistory ? 'Loading...' : `${trainingHistory.length} model run${trainingHistory.length !== 1 ? 's' : ''} completed`}
                  </p>
                </div>
                <button
                  onClick={refreshHistory}
                  disabled={loadingHistory}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-xs text-gray-muted disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
              {/* Search bar */}
              <div className="relative mb-4">
                <input
                  type="text"
                  placeholder="Search runs by model name, dataset ID, or status…"
                  value={historySearch}
                  onChange={e => { setHistorySearch(e.target.value); setHistoryPage(1); }}
                  className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-primary/30 focus:border-purple-primary"
                />
                <Eye className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
              </div>

              {loadingHistory ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-6 h-6 border-2 border-purple-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : trainingHistory.length === 0 ? (
                <div className="text-center py-10">
                  <BarChart3 className="w-10 h-10 text-purple-primary/30 mx-auto mb-3" />
                  <p className="text-sm text-gray-muted">No training runs recorded yet</p>
                  <p className="text-xs text-gray-muted mt-1">Results will appear here after your first run completes</p>
                </div>
              ) : (() => {
                // ── Group jobs into sessions by dataset_id ──
                const sessionsMap = new Map();
                trainingHistory.forEach(job => {
                  const key = job.dataset_id || `no-dataset-${new Date(job.created_at).toDateString()}`;
                  if (!sessionsMap.has(key)) sessionsMap.set(key, []);
                  sessionsMap.get(key).push(job);
                });
                // Sort sessions newest-first
                let sessions = Array.from(sessionsMap.entries())
                  .map(([key, jobs]) => ({
                    key,
                    jobs: jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
                    latestDate: jobs.reduce((d, j) => new Date(j.created_at) > new Date(d) ? j.created_at : d, jobs[0].created_at),
                    bestAuc: Math.max(...jobs.map(j => j.test_auc || j.oof_auc || 0).filter(Boolean)),
                    datasetId: jobs[0].dataset_id,
                  }))
                  .sort((a, b) => new Date(b.latestDate) - new Date(a.latestDate));

                // Apply search filter
                if (historySearch.trim()) {
                  const q = historySearch.toLowerCase();
                  sessions = sessions.filter(s =>
                    s.jobs.some(j =>
                      (j.model_name || '').toLowerCase().includes(q) ||
                      (j.job_id || '').toLowerCase().includes(q) ||
                      (j.dataset_id || '').toLowerCase().includes(q) ||
                      (j.status || '').toLowerCase().includes(q) ||
                      (j.job_type || '').toLowerCase().includes(q)
                    ) || (s.datasetId || '').toLowerCase().includes(q)
                  );
                }

                const pagedSessions = sessions.slice(0, historyPage * SESSIONS_PER_PAGE);
                const hasMore = sessions.length > historyPage * SESSIONS_PER_PAGE;

                const toggleSession = (key) => setExpandedSessions(prev => {
                  const next = new Set(prev);
                  next.has(key) ? next.delete(key) : next.add(key);
                  return next;
                });

                return (
                  <div className="space-y-3">
                    {sessions.length === 0 && historySearch && (
                      <p className="text-center py-6 text-xs text-gray-400">No runs match "{historySearch}"</p>
                    )}
                    {pagedSessions.map((session, si) => {
                      const isOpen = expandedSessions.has(session.key) || (si === 0 && expandedSessions.has('session-0'));
                      const completedJobs = session.jobs.filter(j => j.status === 'completed');
                      const modelJobIds = completedJobs.map(j => j.job_id);
                      const sessionDate = new Date(session.latestDate);
                      const isToday = sessionDate.toDateString() === new Date().toDateString();
                      const dateLabel = isToday ? 'Today' : sessionDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
                      const baseCount = session.jobs.filter(j => j.job_type === 'base_model').length;
                      const ensembleCount = session.jobs.filter(j => j.job_type === 'ensemble').length;

                      return (
                        <div key={session.key} className={`border rounded-xl overflow-hidden transition-all ${isToday ? 'border-purple-200 bg-purple-50/20' : 'border-gray-150 bg-white/60'}`}>
                          {/* Session Header */}
                          <button
                            onClick={() => toggleSession(si === 0 ? 'session-0' : session.key)}
                            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-black/5 transition-colors text-left"
                          >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isToday ? 'bg-purple-dim' : 'bg-gray-100'}`}>
                              <FolderOpen className={`w-4 h-4 ${isToday ? 'text-purple-primary' : 'text-gray-400'}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-syne text-sm font-bold text-black-text">{dateLabel}</span>
                                {isToday && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-purple-primary text-white">Today</span>}
                                <span className="text-[10px] text-gray-400">{baseCount} base{ensembleCount ? `, ${ensembleCount} ensemble` : ''}</span>
                              </div>
                              <div className="text-[10px] text-gray-400 mt-0.5 font-mono truncate">
                                {session.datasetId ? `dataset: ${session.datasetId.slice(0, 8)}…` : 'no dataset ref'}
                              </div>
                              {/* Submitted by */}
                              {session.jobs[0]?.user_full_name && (
                                <div className="flex items-center gap-1 mt-0.5">
                                  <Users className="w-3 h-3 text-gray-400 flex-shrink-0" />
                                  <span className="text-[10px] text-gray-600 font-medium">{session.jobs[0].user_full_name}</span>
                                  {session.jobs[0].user_full_name !== user?.full_name && (
                                    <span className="text-[10px] text-gray-400">(Other Team Member)</span>
                                  )}
                                </div>
                              )}
                            </div>
                            {session.bestAuc > 0 && (
                              <div className="text-right flex-shrink-0 mr-2">
                                <div className="text-[10px] text-gray-400">Best AUC</div>
                                <div className="font-bold text-sm text-purple-primary">{session.bestAuc.toFixed(3)}</div>
                              </div>
                            )}
                            {completedJobs.length >= 1 && (
                              <button
                                onClick={e => { e.stopPropagation(); navigate('/models', { state: { highlightIds: modelJobIds } }); }}
                                className="flex-shrink-0 flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-lg bg-purple-dim text-purple-primary hover:bg-purple-primary hover:text-white transition-colors mr-1"
                                title="View these models in Registry"
                              >
                                <Layers className="w-3 h-3" /> Registry →
                              </button>
                            )}
                            <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
                          </button>

                          {/* Session Jobs */}
                          {isOpen && (
                            <div className="px-4 pb-4 border-t border-gray-100 space-y-2 pt-3">
                              {session.jobs.map(job => (
                                <HistoryJobCard
                                  key={job.job_id}
                                  job={job}
                                  isExpanded={expandedHistoryJobs.has(job.job_id)}
                                  onToggle={() => setExpandedHistoryJobs(prev => {
                                    const next = new Set(prev);
                                    next.has(job.job_id) ? next.delete(job.job_id) : next.add(job.job_id);
                                    return next;
                                  })}
                                />
                              ))}
                              {/* Add Ensemble within session — functional inline form */}
                              {completedJobs.filter(j => j.job_type === 'base_model').length >= 2 &&
                               !session.jobs.some(j => j.job_type === 'ensemble') && (
                                historyEnsembleSession === session.key ? (
                                  <HistoryEnsembleSection
                                    session={session}
                                    onStart={(cfg) => startHistoryEnsemble(session, cfg)}
                                    onCancel={() => setHistoryEnsembleSession(null)}
                                    isLoading={historyEnsembleLoading}
                                  />
                                ) : historyEnsembleJobs[session.key] ? (
                                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-blue-200 bg-blue-50 text-xs text-blue-700 font-medium">
                                    <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                                    Ensemble training in progress — history will refresh automatically
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => {
                                      setHistoryEnsembleSession(session.key);
                                      // auto-expand the session
                                      setExpandedSessions(prev => new Set([...prev, session.key, 'session-0']));
                                    }}
                                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-purple-300 text-purple-primary hover:bg-purple-dim text-xs font-medium transition-colors"
                                  >
                                    <Layers className="w-3.5 h-3.5" />
                                    Add Ensemble on these base models →
                                  </button>
                                )
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {hasMore && (
                      <button
                        onClick={() => setHistoryPage(p => p + 1)}
                        className="w-full py-2.5 rounded-xl border border-gray-200 text-xs text-gray-muted hover:bg-gray-50 transition-colors"
                      >
                        Load older sessions ({sessions.length - pagedSessions.length} more)
                      </button>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Training Wizard Dialog */}
      {showNewRunDialog && (
        <NewTrainingRunDialog
          availableDatasets={availableDatasets}
          selectedModels={selectedModels}
          onToggleModel={toggleModel}
          onSetModels={setSelectedModels}
          config={config}
          onConfigChange={setConfig}
          onStart={startTrainingRun}
          onClose={() => setShowNewRunDialog(false)}
          selectedDataset={selectedDataset}
          onSelectDataset={(dataset) => {
            setSelectedDataset(dataset);
            setConfig(prev => ({ ...prev, batchId: dataset.batch_id }));
          }}
          isLoading={isPreparingDataset || isStartingTraining}
          loadingStatus={datasetPrepStatus}
        />
      )}
      
      {/* Model Comparison Dialog */}
      {showComparison && (
        <ModelComparisonDialog
          models={completedModels}
          selectedModels={selectedForComparison}
          onToggleModel={toggleComparison}
          onClose={() => setShowComparison(false)}
        />
      )}
      </div>
    </DashboardLayout>
  );
}

// Inline Ensemble Section — shown below base models when ≥2 are complete
function EnsembleSection({ completedModels, activeRun, onStart, isLoading }) {
  const [expanded, setExpanded] = useState(false);
  const [metaLearner, setMetaLearner] = useState('logistic_regression');

  const META_LEARNERS = [
    { id: 'logistic_regression', label: 'Logistic Regression', desc: 'Fast, interpretable, good baseline' },
    { id: 'gradient_boosting',   label: 'Gradient Boosting',   desc: 'Powerful, handles non-linearity' },
    { id: 'neural_network',      label: 'Neural Network',       desc: 'Deep stacking, highest capacity' },
  ];

  const handleStart = () => {
    onStart({ metaLearnerType: metaLearner, baseModels: completedModels });
  };

  return (
    <div className="border-2 border-dashed border-purple-200 rounded-xl overflow-hidden">
      <button onClick={() => setExpanded(v => !v)} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-purple-50/50 transition-colors text-left">
        <div className="w-8 h-8 rounded-lg bg-purple-dim flex items-center justify-center flex-shrink-0">
          <Layers className="w-4 h-4 text-purple-primary" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-syne text-sm font-bold text-purple-primary">Train Stacking Ensemble</span>
            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-dim text-purple-primary">
              {completedModels.length} base models ready
            </span>
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5">Combine your trained models into a meta-learner</p>
        </div>
        <ChevronDown className={`w-4 h-4 text-purple-300 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-purple-100 bg-purple-50/30">
          <p className="text-xs text-gray-500 mt-3 mb-2">Select meta-learner algorithm:</p>
          <div className="space-y-2 mb-4">
            {META_LEARNERS.map(ml => (
              <label key={ml.id} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${metaLearner === ml.id ? 'border-purple-primary bg-purple-dim' : 'border-gray-200 hover:border-purple-200'}`}>
                <input type="radio" name="metaLearner" value={ml.id} checked={metaLearner === ml.id} onChange={() => setMetaLearner(ml.id)} className="mt-0.5 accent-purple-600" />
                <div>
                  <div className="text-xs font-semibold text-black-text">{ml.label}</div>
                  <div className="text-[10px] text-gray-400">{ml.desc}</div>
                </div>
              </label>
            ))}
          </div>
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-purple-primary text-white text-sm font-medium hover:bg-purple-primary/90 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Starting...</>
            ) : (
              <><Layers className="w-4 h-4" /> Start Ensemble Training</>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

// Inline Ensemble Section for History sessions
function HistoryEnsembleSection({ session, onStart, onCancel, isLoading }) {
  const [metaLearner, setMetaLearner] = useState('logistic_regression');
  const baseCount = session.jobs.filter(j => j.job_type === 'base_model' && j.status === 'completed').length;

  const META_LEARNERS = [
    { id: 'logistic_regression', label: 'Logistic Regression', desc: 'Fast, interpretable, good baseline' },
    { id: 'gradient_boosting',   label: 'Gradient Boosting',   desc: 'Powerful, handles non-linearity' },
    { id: 'neural_network',      label: 'Neural Network',       desc: 'Deep stacking, highest capacity' },
  ];

  return (
    <div className="border-2 border-purple-200 rounded-xl overflow-hidden bg-purple-50/30">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-purple-100">
        <Layers className="w-4 h-4 text-purple-primary flex-shrink-0" />
        <span className="font-syne text-xs font-bold text-purple-primary flex-1">
          Stack {baseCount} base models into an ensemble
        </span>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 text-xs px-2 py-1 rounded transition-colors">Cancel</button>
      </div>
      <div className="px-4 pb-4 pt-3">
        <p className="text-[10px] text-gray-500 mb-2">Select meta-learner:</p>
        <div className="space-y-1.5 mb-3">
          {META_LEARNERS.map(ml => (
            <label key={ml.id} className={`flex items-start gap-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${metaLearner === ml.id ? 'border-purple-primary bg-white' : 'border-gray-200 hover:border-purple-200'}`}>
              <input type="radio" name={`histMeta-${session.key}`} value={ml.id} checked={metaLearner === ml.id} onChange={() => setMetaLearner(ml.id)} className="mt-0.5 accent-purple-600" />
              <div>
                <div className="text-[11px] font-semibold text-black-text">{ml.label}</div>
                <div className="text-[10px] text-gray-400">{ml.desc}</div>
              </div>
            </label>
          ))}
        </div>
        <button
          onClick={() => onStart({ metaLearnerType: metaLearner })}
          disabled={isLoading}
          className="w-full py-2 rounded-lg bg-purple-primary text-white text-xs font-medium hover:bg-purple-primary/90 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <><div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> Starting…</>
          ) : (
            <><Layers className="w-3.5 h-3.5" /> Start Ensemble Training</>
          )}
        </button>
      </div>
    </div>
  );
}

// Training Job Card Component (expandable row)
function TrainingJobCard({ job, modelInfo, isExpanded, onToggle }) {
  const isEnsemble = job.model_name === 'ensemble' || !modelInfo;
  const Icon = isEnsemble ? Layers : (modelInfo?.icon || Brain);

  const statusConfig = {
    running:   { icon: Zap,         color: 'text-amber',     bg: 'bg-amber-dim',  label: 'Training...' },
    completed: { icon: CheckCircle, color: 'text-green',     bg: 'bg-green-dim',  label: 'Complete' },
    failed:    { icon: XCircle,     color: 'text-red-500',   bg: 'bg-red-50',     label: 'Failed' },
    queued:    { icon: Clock,       color: 'text-blue-500',  bg: 'bg-blue-50',    label: 'Queued' },
  }[job.status] || { icon: Clock, color: 'text-gray-muted', bg: 'bg-gray-100', label: 'Unknown' };
  const StatusIcon = statusConfig.icon;
  const displayName = isEnsemble ? 'Stacking Ensemble' : (modelInfo?.name || job.model_name);

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${isEnsemble ? 'border-purple-200 bg-purple-50/30' : 'border-gray-100 bg-white/50'}`}>
      <button onClick={onToggle} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-black/5 transition-colors text-left">
        <div className={`w-8 h-8 rounded-lg ${statusConfig.bg} flex items-center justify-center flex-shrink-0`}>
          {job.status === 'running'
            ? <Icon className={`w-4 h-4 ${statusConfig.color} animate-pulse`} />
            : <Icon className={`w-4 h-4 ${statusConfig.color}`} />
          }
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-syne text-sm font-bold text-black-text truncate">{displayName}</span>
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusConfig.bg} ${statusConfig.color} flex-shrink-0`}>
              <StatusIcon className="w-2.5 h-2.5" />
              {statusConfig.label}
            </span>
          </div>
          {job.status === 'running' && (
            <div className="flex items-center gap-2 mt-1">
              <div className="h-1 flex-1 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-amber rounded-full transition-all" style={{ width: `${job.progress || 15}%` }} />
              </div>
              <span className="text-[10px] text-amber font-medium">{job.progress || 0}%</span>
            </div>
          )}
        </div>

        {job.status === 'completed' && job.result && (
          <div className="flex items-center gap-4 text-xs flex-shrink-0 mr-2">
            <div className="text-right">
              <div className="text-[10px] text-gray-400">AUC</div>
              <div className="font-bold text-purple-primary">
                {(job.result.test_auc ?? job.result.ensemble_test_auc ?? job.result.oof_auc)?.toFixed(3) || '—'}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-gray-400">F1</div>
              <div className="font-bold text-green">
                {(job.result.test_f1 ?? job.result.ensemble_test_f1 ?? job.result.f1)?.toFixed(3) || '—'}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-gray-400">Time</div>
              <div className="font-bold text-black-text">
                {job.result.training_time_seconds ? `${Math.round(job.result.training_time_seconds)}s` : '—'}
              </div>
            </div>
          </div>
        )}
        {job.status === 'queued' && <span className="text-xs text-blue-400 flex-shrink-0 mr-2">Waiting...</span>}

        <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50">
          {job.status === 'queued' && (
            <div className="flex items-center gap-2 text-xs text-blue-500 py-1">
              <Clock className="w-3.5 h-3.5" /> Waiting for resources to become available...
            </div>
          )}
          {job.status === 'running' && (
            <div className="space-y-2">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-amber rounded-full transition-all" style={{ width: `${job.progress || 15}%` }} />
              </div>
              <p className="text-xs text-gray-500">Training in progress — {job.progress || 0}% complete</p>
            </div>
          )}
          {job.status === 'completed' && job.result && (
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'AUC-ROC (Test)', value: (job.result.test_auc ?? job.result.ensemble_test_auc)?.toFixed(3), color: 'text-purple-primary' },
                { label: 'CV AUC (OOF)',   value: (job.result.oof_auc ?? job.result.ensemble_oof_auc)?.toFixed(3),  color: 'text-purple-primary/70' },
                { label: 'Precision',      value: (job.result.test_precision ?? job.result.ensemble_test_precision)?.toFixed(3), color: 'text-blue-500' },
                { label: 'Recall',         value: (job.result.test_recall ?? job.result.ensemble_test_recall)?.toFixed(3), color: 'text-amber' },
                { label: 'F1 Score',       value: (job.result.test_f1 ?? job.result.ensemble_test_f1)?.toFixed(3), color: 'text-green' },
                { label: 'Training Time',  value: job.result.training_time_seconds ? `${Math.round(job.result.training_time_seconds)}s` : null, color: 'text-black-text' },
              ].filter(m => m.value != null).map(({ label, value, color }) => (
                <div key={label} className="bg-white rounded-lg px-3 py-2 border border-gray-100">
                  <div className="text-[10px] text-gray-400 mb-0.5">{label}</div>
                  <div className={`text-sm font-bold ${color}`}>{value}</div>
                </div>
              ))}
            </div>
          )}
          {job.status === 'failed' && (
            <div className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
              Error: {job.error_message || 'Training failed'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// 3-Step Training Wizard
function NewTrainingRunDialog({ availableDatasets, selectedModels, onToggleModel, onSetModels, config, onConfigChange, onStart, onClose, selectedDataset, onSelectDataset, isLoading, loadingStatus }) {
  const [step, setStep] = useState(selectedDataset ? 2 : 1);
  const [datasetSearch, setDatasetSearch] = useState('');
  const [showAllDatasets, setShowAllDatasets] = useState(false);
  const DATASET_VISIBLE = 10;

  const getCleanName = (dataset) => {
    const raw = dataset.original_filename || dataset.file_name || '';
    const cleaned = raw
      .replace(/^Preprocessed Session\s+/i, '')
      .replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '')
      .replace(/\.csv\s*$/i, '')
      .trim();
    if (cleaned) return cleaned;
    // Build a descriptive fallback from metadata
    const count = dataset.record_count || dataset.row_count;
    const date = dataset.uploaded_at ? new Date(dataset.uploaded_at) : null;
    const dateStr = date ? `${date.toLocaleString('en-US', { month: 'short' })} ${date.getDate()}` : '';
    const countStr = count ? ` · ${count} rows` : '';
    return dateStr ? `Upload ${dateStr}${countStr}` : `Dataset${countStr}`;
  };

  const modelsByCategory = AVAILABLE_MODELS.reduce((acc, model) => {
    if (!acc[model.category]) acc[model.category] = [];
    acc[model.category].push(model);
    return acc;
  }, {});

  const canNext1 = !!selectedDataset;
  const canStart = selectedModels.length > 0 && !!selectedDataset;

  const STEPS = [{ num: 1, label: 'Dataset' }, { num: 2, label: 'Models' }];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[92vh] flex flex-col shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <div>
            <h2 className="font-syne text-lg font-bold text-black-text">New Training Run</h2>
            <p className="text-xs text-gray-muted mt-0.5">Select a dataset and the algorithms to run</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5 text-gray-muted" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center px-6 py-3 border-b border-gray-100 gap-1">
          {STEPS.map((s, i) => (
            <div key={s.num} className="flex items-center">
              <button
                onClick={() => { if (s.num < step || (s.num === 2 && canNext1)) setStep(s.num); }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                  step === s.num ? 'bg-purple-dim text-purple-primary' : s.num < step ? 'text-purple-primary hover:bg-purple-dim/50 cursor-pointer' : 'text-gray-400 cursor-default'
                }`}
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  s.num < step ? 'bg-green-100 text-green-700' : step === s.num ? 'bg-purple-primary text-white' : 'bg-gray-100 text-gray-400'
                }`}>
                  {s.num < step ? '✓' : s.num}
                </span>
                {s.label}
              </button>
              {i < 1 && <ChevronRight className="w-3 h-3 text-gray-300 mx-1" />}
            </div>
          ))}
          {selectedModels.length > 0 && (
            <span className="ml-auto text-xs text-purple-primary font-medium">{selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''} selected</span>
          )}
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">

          {/* ─── STEP 1: Dataset ─── */}
          {step === 1 && (
            <div className="space-y-3">
              <p className="text-xs text-gray-muted">Select the dataset to train on. Newest first — defaults to the latest upload.</p>

              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search datasets…"
                  value={datasetSearch}
                  onChange={e => setDatasetSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-purple-primary/50"
                />
                <svg className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 111 11a6 6 0 0116 0z" /></svg>
              </div>

              {availableDatasets.length === 0 ? (
                <div className="text-center py-10">
                  <Database className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-muted">No datasets available</p>
                  <p className="text-xs text-gray-muted mt-1">Upload and label a dataset in Data Preparation first</p>
                </div>
              ) : (() => {
                const filtered = availableDatasets.filter(d =>
                  !datasetSearch || getCleanName(d).toLowerCase().includes(datasetSearch.toLowerCase())
                );
                const visible = showAllDatasets || datasetSearch ? filtered : filtered.slice(0, DATASET_VISIBLE);
                const hiddenCount = filtered.length - visible.length;

                return (
                  <div className="space-y-2">
                    {visible.map(dataset => {
                      const isSel = selectedDataset?.batch_id === dataset.batch_id;
                      return (
                        <button
                          key={dataset.batch_id}
                          onClick={() => onSelectDataset(dataset)}
                          className={`w-full p-3.5 rounded-xl border-2 text-left transition-all ${
                            isSel ? 'border-purple-primary bg-purple-primary/5' : 'border-gray-100 hover:border-purple-primary/30 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${isSel ? 'bg-purple-dim' : 'bg-gray-100'}`}>
                              <Database className={`w-4 h-4 ${isSel ? 'text-purple-primary' : 'text-gray-400'}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-syne font-bold text-sm text-black-text truncate">{getCleanName(dataset)}</span>
                                {dataset.isToday && (
                                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 flex-shrink-0">New</span>
                                )}
                              </div>
                              <div className="text-xs text-gray-muted mt-0.5">{dataset.record_count.toLocaleString()} records · {new Date(dataset.uploaded_at).toLocaleDateString()}</div>
                            </div>
                            {isSel && <CheckCircle className="w-5 h-5 text-purple-primary flex-shrink-0" />}
                          </div>
                        </button>
                      );
                    })}
                    {hiddenCount > 0 && (
                      <button onClick={() => setShowAllDatasets(true)} className="w-full py-2 text-xs text-purple-primary hover:underline text-center">
                        Show {hiddenCount} older dataset{hiddenCount !== 1 ? 's' : ''} →
                      </button>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {/* ─── STEP 2: Model Selection ─── */}
          {step === 2 && (
            <div className="space-y-4">
              {/* Dataset summary */}
              {selectedDataset && (
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl text-xs">
                  <Database className="w-3.5 h-3.5 text-purple-primary flex-shrink-0" />
                  <span className="font-medium text-black-text truncate">{getCleanName(selectedDataset)}</span>
                  <span className="text-gray-400 flex-shrink-0">{selectedDataset.record_count} records</span>
                  <button onClick={() => setStep(1)} className="text-purple-primary hover:underline ml-auto flex-shrink-0 text-xs">Change</button>
                </div>
              )}

              {/* Preset shortcuts */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 mr-1">Quick select:</span>
                <button onClick={() => onSetModels(['logistic_regression','decision_tree','random_forest','xgboost','lightgbm'])}
                  className="text-xs px-2.5 py-1 rounded-full border border-gray-200 hover:border-purple-primary/40 hover:bg-purple-dim transition-colors text-gray-600 hover:text-purple-primary">
                  5 core models
                </button>
                <button onClick={() => onSetModels(AVAILABLE_MODELS.map(m => m.id))}
                  className="text-xs px-2.5 py-1 rounded-full border border-gray-200 hover:border-purple-primary/40 hover:bg-purple-dim transition-colors text-gray-600 hover:text-purple-primary">
                  All 13
                </button>
                <button onClick={() => onSetModels([])}
                  className="text-xs px-2.5 py-1 rounded-full border border-gray-200 hover:border-gray-300 transition-colors text-gray-400 hover:text-gray-600">
                  Clear
                </button>
              </div>

              {/* Model grid */}
              {Object.entries(modelsByCategory).map(([category, models]) => (
                <div key={category}>
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">{category}</div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {models.map(model => {
                      const Icon = model.icon;
                      const isSel = selectedModels.includes(model.id);
                      return (
                        <button
                          key={model.id}
                          onClick={() => onToggleModel(model.id)}
                          className={`flex items-center gap-2 px-2.5 py-2 rounded-lg border text-left text-xs transition-all ${
                            isSel ? 'border-purple-primary bg-purple-dim' : 'border-gray-100 hover:border-purple-primary/30 hover:bg-gray-50'
                          }`}
                        >
                          <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isSel ? 'text-purple-primary' : 'text-gray-400'}`} />
                          <span className={`font-medium truncate ${isSel ? 'text-purple-primary' : 'text-black-text'}`}>{model.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* Loading status */}
              {isLoading && loadingStatus && (
                <div className="px-4 py-3 rounded-lg bg-purple-primary/10 border border-purple-primary/20">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-purple-primary border-t-transparent rounded-full animate-spin flex-shrink-0" />
                    <span className="text-sm text-purple-primary font-medium">{loadingStatus}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-3 px-6 py-4 border-t border-gray-100">
          {step > 1 ? (
            <button onClick={() => setStep(s => s - 1)} disabled={isLoading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-sm font-medium transition-colors disabled:opacity-50">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
          ) : (
            <button onClick={onClose}
              className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-sm font-medium transition-colors">
              Cancel
            </button>
          )}
          <div className="flex-1" />
          {step === 1 ? (
            <button onClick={() => setStep(2)} disabled={!canNext1}
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              Next <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={onStart} disabled={!canStart || isLoading}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              {isLoading ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Processing...</>
              ) : (
                <><PlayCircle className="w-4 h-4" /> Start Training ({selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''})</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}


// Stat Card Component
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

// Model Comparison Dialog Component
function ModelComparisonDialog({ models, selectedModels, onToggleModel, onClose }) {
  // Get selected model data
  const comparisonData = models.filter(m => selectedModels.includes(m.modelId));
  
  // Metrics to compare
  const metrics = [
    { key: 'accuracy', label: 'Accuracy', format: (v) => v?.toFixed(3) || 'N/A', color: 'text-green' },
    { key: 'auc_roc', label: 'AUC-ROC', format: (v) => v?.toFixed(3) || 'N/A', color: 'text-purple-primary' },
    { key: 'precision', label: 'Precision', format: (v) => v?.toFixed(3) || 'N/A', color: 'text-blue-500' },
    { key: 'recall', label: 'Recall', format: (v) => v?.toFixed(3) || 'N/A', color: 'text-amber' },
    { key: 'f1', label: 'F1 Score', format: (v) => v?.toFixed(3) || 'N/A', color: 'text-green' },
    { key: 'training_time_seconds', label: 'Training Time', format: (v) => v ? `${Math.round(v)}s` : 'N/A', color: 'text-gray-700' }
  ];
  
  // Find best model per metric
  const getBestValue = (metricKey) => {
    if (metricKey === 'training_time_seconds') {
      return Math.min(...comparisonData.map(m => m[metricKey] || Infinity));
    }
    return Math.max(...comparisonData.map(m => m[metricKey] || 0));
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="font-syne text-xl font-bold text-black-text">Model Performance Comparison</h2>
            <p className="text-xs text-gray-muted mt-1">LAYER 7: ML Training + LAYER 8: Evaluation Metrics</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-muted" />
          </button>
        </div>
        
        {/* Model Selector */}
        <div className="mb-6 p-4 bg-purple-50 rounded-lg">
          <div className="text-xs font-bold text-gray-muted mb-2">Select Models to Compare (up to 4)</div>
          <div className="flex flex-wrap gap-2">
            {models.map(model => {
              const isSelected = selectedModels.includes(model.modelId);
              const modelInfo = AVAILABLE_MODELS.find(m => m.id === model.modelId);
              const Icon = modelInfo?.icon || Brain;
              
              return (
                <button
                  key={model.modelId}
                  onClick={() => selectedModels.length < 4 || isSelected ? onToggleModel(model.modelId) : null}
                  disabled={!isSelected && selectedModels.length >= 4}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-purple-primary bg-purple-dim'
                      : 'border-gray-200 hover:border-purple-primary/50'
                  } ${!isSelected && selectedModels.length >= 4 ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-purple-primary' : 'text-gray-muted'}`} />
                  <span className="text-xs font-medium text-black-text">{model.modelName}</span>
                </button>
              );
            })}
          </div>
        </div>
        
        {comparisonData.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">Select at least 2 models to compare</p>
          </div>
        )}
        
        {comparisonData.length > 0 && (
          <>
            {/* Side-by-Side Comparison Table */}
            <div className="mb-6">
              <h3 className="font-syne text-sm font-bold text-black-text mb-3">Performance Metrics (Side-by-Side)</h3>
              <div className="bg-gray-50 rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-4 py-3 text-left font-bold text-gray-700 bg-white">Metric</th>
                      {comparisonData.map(model => (
                        <th key={model.modelId} className="px-4 py-3 text-center font-bold text-gray-700 bg-white">
                          {model.modelName}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.map((metric, idx) => {
                      const bestValue = getBestValue(metric.key);
                      
                      return (
                        <tr key={metric.key} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-4 py-3 font-medium text-gray-700">{metric.label}</td>
                          {comparisonData.map(model => {
                            const value = model[metric.key];
                            const isBest = value === bestValue;
                            
                            return (
                              <td key={model.modelId} className={`px-4 py-3 text-center font-bold ${isBest ? `${metric.color} bg-green-50` : 'text-gray-700'}`}>
                                {metric.format(value)}
                                {isBest && <span className="ml-1 text-green text-[10px]">★ BEST</span>}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* Confusion Matrix Section */}
            {comparisonData.length > 0 && comparisonData[0].confusion_matrix && (
              <div className="mb-6">
                <h3 className="font-syne text-sm font-bold text-black-text mb-3">Confusion Matrices</h3>
                <div className="grid grid-cols-2 gap-4">
                  {comparisonData.slice(0, 4).map(model => (
                    <ConfusionMatrixCard key={model.modelId} model={model} />
                  ))}
                </div>
              </div>
            )}
            
            {/* Performance Radar Chart Placeholder */}
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-6 text-center">
              <Activity className="w-12 h-12 text-purple-primary/40 mx-auto mb-3" />
              <h3 className="font-syne text-sm font-bold text-gray-900 mb-2">Visual Comparison Chart</h3>
              <p className="text-xs text-gray-600">
                Radar chart visualization showing {comparisonData.length} models across {metrics.length} metrics
              </p>
              <div className="mt-4 text-[10px] text-gray-500">
                📊 Chart implementation: Use Chart.js or Recharts for visualization
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// History Job Card Component
function HistoryJobCard({ job, isExpanded, onToggle }) {
  const modelInfo = AVAILABLE_MODELS.find(m => m.id === job.model_name);
  const Icon = modelInfo?.icon || Brain;

  const statusMap = {
    completed: { color: 'text-green',     bg: 'bg-green-dim', label: 'Completed', icon: CheckCircle },
    failed:    { color: 'text-red-500',   bg: 'bg-red-50',    label: 'Failed',    icon: XCircle },
    running:   { color: 'text-amber',     bg: 'bg-amber-dim', label: 'Running',   icon: Zap },
    queued:    { color: 'text-blue-500',  bg: 'bg-blue-50',   label: 'Queued',    icon: Clock },
  };
  const statusConfig = statusMap[job.status] || statusMap.queued;
  const StatusIcon = statusConfig.icon;

  const formatDate = (dt) => {
    if (!dt) return 'N/A';
    return new Date(dt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  };
  const formatDuration = (s) => {
    if (s == null) return null;
    return s < 60 ? `${Math.round(s)}s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
  };

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">
      <button onClick={onToggle} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left">
        <div className={`w-8 h-8 rounded-lg ${statusConfig.bg} flex items-center justify-center flex-shrink-0`}>
          <Icon className={`w-4 h-4 ${statusConfig.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-syne text-sm font-bold text-black-text truncate">
              {modelInfo?.name || job.model_name || 'Unknown Model'}
            </span>
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusConfig.bg} ${statusConfig.color} flex-shrink-0`}>
              <StatusIcon className="w-2.5 h-2.5" />
              {statusConfig.label}
            </span>
          </div>
          <div className="text-[10px] text-gray-400 mt-0.5">{formatDate(job.created_at)}</div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0 text-xs mr-2">
          {job.oof_auc != null && (
            <div className="text-right">
              <div className="text-[10px] text-gray-400">CV AUC</div>
              <div className="font-bold text-purple-primary">{job.oof_auc.toFixed(3)}</div>
            </div>
          )}
          {formatDuration(job.training_time_seconds) && (
            <div className="text-right">
              <div className="text-[10px] text-gray-400">Duration</div>
              <div className="font-bold text-black-text">{formatDuration(job.training_time_seconds)}</div>
            </div>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="bg-white rounded-lg px-3 py-2 border border-gray-100">
              <div className="text-[10px] text-gray-400 mb-0.5">Job ID</div>
              <div className="font-mono text-gray-500 text-[10px]">{job.job_id?.slice(0, 8)}…</div>
            </div>
            <div className="bg-white rounded-lg px-3 py-2 border border-gray-100">
              <div className="text-[10px] text-gray-400 mb-0.5">Completed</div>
              <div className="text-gray-700">{formatDate(job.completed_at)}</div>
            </div>
            <div className="bg-white rounded-lg px-3 py-2 border border-gray-100">
              <div className="text-[10px] text-gray-400 mb-0.5">CV AUC (OOF)</div>
              <div className="font-bold text-purple-primary">{job.oof_auc?.toFixed(4) || '—'}</div>
            </div>
            <div className="bg-white rounded-lg px-3 py-2 border border-gray-100">
              <div className="text-[10px] text-gray-400 mb-0.5">Duration</div>
              <div className="font-bold text-black-text">{formatDuration(job.training_time_seconds) || '—'}</div>
            </div>
            {job.user_full_name && (
              <div className="bg-white rounded-lg px-3 py-2 border border-gray-100 col-span-2">
                <div className="text-[10px] text-gray-400 mb-0.5">Trained by</div>
                <div className="text-gray-700">{job.user_full_name}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Confusion Matrix Card Component
function ConfusionMatrixCard({ model }) {
  const cm = model.confusion_matrix || [[0, 0], [0, 0]];
  const total = cm.flat().reduce((a, b) => a + b, 0);
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="font-syne text-sm font-bold text-gray-900">{model.modelName}</div>
        <div className="ml-auto text-xs text-gray-500">Total: {total}</div>
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-green-100 border border-green-200 rounded p-3 text-center">
          <div className="text-xs text-gray-600 mb-1">True Negative</div>
          <div className="font-bold text-lg text-green-700">{cm[0]?.[0] || 0}</div>
          <div className="text-[10px] text-gray-500 mt-1">
            {total > 0 ? `${((cm[0]?.[0] || 0) / total * 100).toFixed(1)}%` : '0%'}
          </div>
        </div>
        
        <div className="bg-red-100 border border-red-200 rounded p-3 text-center">
          <div className="text-xs text-gray-600 mb-1">False Positive</div>
          <div className="font-bold text-lg text-red-700">{cm[0]?.[1] || 0}</div>
          <div className="text-[10px] text-gray-500 mt-1">
            {total > 0 ? `${((cm[0]?.[1] || 0) / total * 100).toFixed(1)}%` : '0%'}
          </div>
        </div>
        
        <div className="bg-red-100 border border-red-200 rounded p-3 text-center">
          <div className="text-xs text-gray-600 mb-1">False Negative</div>
          <div className="font-bold text-lg text-red-700">{cm[1]?.[0] || 0}</div>
          <div className="text-[10px] text-gray-500 mt-1">
            {total > 0 ? `${((cm[1]?.[0] || 0) / total * 100).toFixed(1)}%` : '0%'}
          </div>
        </div>
        
        <div className="bg-green-100 border border-green-200 rounded p-3 text-center">
          <div className="text-xs text-gray-600 mb-1">True Positive</div>
          <div className="font-bold text-lg text-green-700">{cm[1]?.[1] || 0}</div>
          <div className="text-[10px] text-gray-500 mt-1">
            {total > 0 ? `${((cm[1]?.[1] || 0) / total * 100).toFixed(1)}%` : '0%'}
          </div>
        </div>
      </div>
    </div>
  );
}
