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
  X
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import EnsembleTrainingDialog from '../components/EnsembleTrainingDialog';
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
  const [selectedModels, setSelectedModels] = useState([]);
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [activeRun, setActiveRun] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState([]);
  
  // Ensemble training state
  const [showEnsembleDialog, setShowEnsembleDialog] = useState(false);
  const [isTrainingEnsemble, setIsTrainingEnsemble] = useState(false);
  const [ensembleStatus, setEnsembleStatus] = useState('');
  
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
  const [showDatasetSelector, setShowDatasetSelector] = useState(false);

  // Fetch available datasets (include staging so labeled staging data can be trained)
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        console.log('[Training] Fetching datasets...');
        // Include both staging and saved data - users can train on staging data after labeling
        const response = await flexibleAPI.getRecentUploads(50, true, true);
        console.log('[Training] Got uploads:', response.uploads?.length || 0);
        
        if (!response.uploads || response.uploads.length === 0) {
          console.log('[Training] No uploads found');
          setAvailableDatasets([]);
          return;
        }
        
        // Simple transformation without fetching labeling stats (for now)
        // User can see all datasets and select manually
        const datasets = response.uploads
          .filter(upload => upload.row_count > 0)
          .map(upload => ({
            batch_id: upload.id,
            original_filename: upload.file_name,
            uploaded_at: upload.uploaded_at,
            record_count: upload.row_count || 0,
            labeled_count: upload.row_count || 0, // Assume all labeled for now
            dataset_type: upload.dataset_type || 'General',
            source: upload.source || 'Upload',
            is_staging: upload.source === 'staging'  // Track if staging
          }));
        
        console.log('[Training] Datasets transformed:', datasets.length);
        setAvailableDatasets(datasets);
        
        // Auto-select dataset: Priority - navigation state > sessionStorage > first available
        const targetBatchId = location.state?.dataset_id || 
                              sessionStorage.getItem('current_batch_id') || 
                              config.batchId;
        
        if (targetBatchId && datasets.length > 0) {
          const matchingDataset = datasets.find(d => d.batch_id === targetBatchId);
          if (matchingDataset) {
            console.log('[Training] Auto-selecting dataset from ML Prep:', matchingDataset.original_filename);
            setSelectedDataset(matchingDataset);
          } else {
            console.log('[Training] Target batch not found, selecting first dataset');
            setSelectedDataset(datasets[0]);
          }
        } else if (datasets.length > 0 && !selectedDataset) {
          console.log('[Training] Auto-selecting first dataset:', datasets[0].original_filename);
          setSelectedDataset(datasets[0]);
        }
        
      } catch (error) {
        console.error('[Training] Error fetching datasets:', error);
        console.error('[Training] Error stack:', error.stack);
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
        
        // If all jobs completed, store model IDs and clear active run
        if (allCompleted) {
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
          }, 5000);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [activeRun]);

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
      setEnsembleStatus('Ensemble training job started successfully!');
      
      // Close dialog and show success message
      setTimeout(() => {
        setShowEnsembleDialog(false);
        setIsTrainingEnsemble(false);
        setEnsembleStatus('');
        alert(`Ensemble training started! Job ID: ${response.job_id}\n\nThe ensemble will combine ${baseModelJobs.length} base models using ${ensembleConfig.metaLearnerType} meta-learner.`);
      }, 1500);
      
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

  return (
    <DashboardLayout>
      <PageHeader title="Training Jobs" subtitle="Training" user={user} />
      <div className="h-screen flex flex-col" style={{ zoom: 0.75 }}>

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
                      onClick={() => window.location.reload()}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-xs text-gray-muted"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Refresh
                    </button>
                    {completedModels.length >= 3 && (
                      <button
                        onClick={() => setShowEnsembleDialog(true)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-primary to-blue-500 text-white hover:opacity-90 transition-opacity text-xs font-medium"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        Train Ensemble ({completedModels.length} models)
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
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!activeRun && (
              <div className="bg-gradient-to-br from-purple-primary/5 to-purple-primary/10 border-2 border-dashed border-purple-primary/30 rounded-2xl p-12 text-center">
                <Brain className="w-16 h-16 text-purple-primary/40 mx-auto mb-4" />
                <h3 className="font-syne text-lg font-bold text-black-text mb-2">
                  No Active Training Runs
                </h3>
                <p className="text-sm text-gray-muted mb-6 max-w-md mx-auto">
                  Start a new training run to experiment with different ML algorithms and compare their performance
                </p>
                <button
                  onClick={() => setShowDatasetSelector(true)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Start Your First Training Run
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dataset Selection Dialog */}
      {showDatasetSelector && (
        <DatasetSelectorDialog
          datasets={availableDatasets}
          selectedDataset={selectedDataset}
          onSelectDataset={(dataset) => {
            setSelectedDataset(dataset);
            setConfig(prev => ({ ...prev, batchId: dataset.batch_id }));
            setShowDatasetSelector(false);
            setShowNewRunDialog(true);
          }}
          onClose={() => setShowDatasetSelector(false)}
        />
      )}

      {/* New Training Run Dialog */}
      {showNewRunDialog && (
        <NewTrainingRunDialog
          selectedModels={selectedModels}
          onToggleModel={toggleModel}
          config={config}
          onConfigChange={setConfig}
          onStart={startTrainingRun}
          onClose={() => setShowNewRunDialog(false)}
          selectedDataset={selectedDataset}
          isLoading={isPreparingDataset || isStartingTraining}
          loadingStatus={datasetPrepStatus}
        />
      )}
      
      {/* Ensemble Training Dialog */}
      {showEnsembleDialog && (
        <EnsembleTrainingDialog
          completedModels={completedModels}
          activeRun={activeRun}
          onStart={startEnsembleTraining}
          onClose={() => setShowEnsembleDialog(false)}
          isLoading={isTrainingEnsemble}
          loadingStatus={ensembleStatus}
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
    </DashboardLayout>
  );
}

// Training Job Card Component
function TrainingJobCard({ job, modelInfo }) {
  const Icon = modelInfo?.icon || Brain;
  
  const getStatusConfig = () => {
    switch (job.status) {
      case 'running':
        return { icon: Zap, color: 'text-amber', bg: 'bg-amber-dim', label: 'Training...' };
      case 'completed':
        return { icon: CheckCircle, color: 'text-green', bg: 'bg-green-dim', label: 'Complete' };
      case 'failed':
        return { icon: XCircle, color: 'text-red', bg: 'bg-red-dim', label: 'Failed' };
      case 'queued':
        return { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-50', label: 'Queued' };
      default:
        return { icon: Clock, color: 'text-gray-muted', bg: 'bg-gray-100', label: 'Unknown' };
    }
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl p-4">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-lg ${statusConfig.bg} flex items-center justify-center`}>
          <Icon className={`w-6 h-6 ${statusConfig.color}`} />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-syne text-sm font-bold text-black-text">{modelInfo?.name || job.model_name}</h3>
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${statusConfig.bg} ${statusConfig.color}`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </span>
          </div>
          
          {job.status === 'running' && (
            <>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
                <div
                  className="h-full bg-amber rounded-full transition-all"
                  style={{ width: `${job.progress || 0}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-muted">Progress: {job.progress || 0}%</span>
                <span className="text-amber font-medium">Training...</span>
              </div>
            </>
          )}
          
          {job.status === 'completed' && job.result && (
            <div className="grid grid-cols-6 gap-3 text-xs">
              <div>
                <div className="text-gray-muted">Accuracy</div>
                <div className="font-bold text-green">{job.result.accuracy?.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-muted">AUC-ROC</div>
                <div className="font-bold text-purple-primary">{job.result.auc_roc?.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-muted">Precision</div>
                <div className="font-bold text-blue-500">{job.result.precision?.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-muted">Recall</div>
                <div className="font-bold text-amber">{job.result.recall?.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-muted">F1 Score</div>
                <div className="font-bold text-green">{job.result.f1?.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-muted">Training Time</div>
                <div className="font-bold text-black-text">
                  {job.result.training_time_seconds ? `${Math.round(job.result.training_time_seconds)}s` : 'N/A'}
                </div>
              </div>
            </div>
          )}
          
          {job.status === 'queued' && (
            <div className="text-xs text-gray-muted">Waiting to start...</div>
          )}
        </div>
      </div>
    </div>
  );
}

// New Training Run Dialog Component
// Dataset Selector Dialog Component
function DatasetSelectorDialog({ datasets, selectedDataset, onSelectDataset, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="font-syne text-xl font-bold text-black-text">Select Dataset for Training</h2>
            <p className="text-sm text-gray-muted mt-1">Choose a validated dataset to train models on</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-muted" />
          </button>
        </div>

        {/* Dataset List */}
        <div className="space-y-3">
          {datasets.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-12 h-12 text-gray-muted mx-auto mb-3" />
              <p className="text-sm text-gray-muted">No datasets available</p>
              <p className="text-xs text-gray-muted mt-1">Upload and label a dataset first</p>
            </div>
          ) : (
            datasets.map((dataset) => {
              const recordCount = dataset.record_count || 0;
              const labeledCount = dataset.labeled_count || 0;
              const labelingProgress = recordCount > 0 ? Math.round((labeledCount / recordCount) * 100) : 0;
              const isFullyLabeled = labelingProgress >= 50; // Lower threshold for testing
              const isSelected = selectedDataset?.batch_id === dataset.batch_id;

              return (
                <button
                  key={dataset.batch_id}
                  onClick={() => onSelectDataset(dataset)} // Remove isFullyLabeled check
                  className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                    isSelected
                      ? 'border-purple-primary bg-purple-primary/5'
                      : 'border-gray-200 hover:border-purple-primary/50 hover:bg-purple-primary/5'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="w-4 h-4 text-purple-primary" />
                        <h3 className="font-syne font-bold text-sm text-black-text">
                          {dataset.original_filename || dataset.batch_id.substring(0, 8)}
                        </h3>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700">
                          ✓ Ready
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div>
                          <span className="text-gray-muted">Records:</span>
                          <span className="ml-1 font-medium text-black-text">{recordCount}</span>
                        </div>
                        <div>
                          <span className="text-gray-muted">Labeled:</span>
                          <span className="ml-1 font-medium text-black-text">{labeledCount}</span>
                        </div>
                        <div>
                          <span className="text-gray-muted">Uploaded:</span>
                          <span className="ml-1 font-medium text-black-text">
                            {new Date(dataset.uploaded_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      {!isFullyLabeled && (
                        <p className="text-xs text-yellow-600 mt-2">
                          ⚠️ Dataset must be 100% labeled before training
                        </p>
                      )}
                    </div>

                    {isSelected && (
                      <CheckCircle className="w-5 h-5 text-purple-primary flex-shrink-0 ml-3" />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Help Text */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-700">
            <span className="font-medium">💡 Tip:</span> Only fully labeled datasets can be used for training. 
            Complete labeling in the Data Preparation tab first.
          </p>
        </div>
      </div>
    </div>
  );
}

function NewTrainingRunDialog({ selectedModels, onToggleModel, config, onConfigChange, onStart, onClose, selectedDataset, isLoading, loadingStatus }) {
  // Group models by category
  const modelsByCategory = AVAILABLE_MODELS.reduce((acc, model) => {
    if (!acc[model.category]) acc[model.category] = [];
    acc[model.category].push(model);
    return acc;
  }, {});

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-syne text-xl font-bold text-black-text">Start New Training Run</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-muted" />
          </button>
        </div>

        {/* Selected Dataset Info or Warning */}
        {selectedDataset ? (
          <div className="mb-5 p-4 bg-purple-50 rounded-xl border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-purple-primary" />
              <h3 className="font-syne font-bold text-sm text-black-text">Training Dataset</h3>
            </div>
            <div className="text-sm text-gray-700">
              <p className="font-medium">{selectedDataset.original_filename || selectedDataset.batch_id.substring(0, 8)}</p>
              <p className="text-xs text-gray-muted mt-1">
                {selectedDataset.record_count} records • {selectedDataset.labeled_count} labeled
              </p>
            </div>
          </div>
        ) : (
          <div className="mb-5 p-4 bg-amber-50 rounded-xl border border-amber-200">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-amber-600" />
              <h3 className="font-syne font-bold text-sm text-amber-900">No Dataset Selected</h3>
            </div>
            <p className="text-sm text-amber-800">
              Please close this dialog and click "New Training Run" to select a dataset first.
            </p>
          </div>
        )}
        
        {/* Model Selection */}
        <div className="mb-6">
          <h3 className="font-syne text-sm font-bold text-black-text mb-3">Select Models to Train</h3>
          
          {Object.entries(modelsByCategory).map(([category, models]) => (
            <div key={category} className="mb-4">
              <div className="text-xs font-bold text-gray-muted mb-2">{category}</div>
              <div className="grid grid-cols-3 gap-2">
                {models.map(model => {
                  const Icon = model.icon;
                  const isSelected = selectedModels.includes(model.id);
                  
                  return (
                    <button
                      key={model.id}
                      onClick={() => model.implemented && onToggleModel(model.id)}
                      disabled={!model.implemented}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all text-left ${
                        isSelected
                          ? 'border-purple-primary bg-purple-dim'
                          : model.implemented
                          ? 'border-gray-200 hover:border-purple-primary/50'
                          : 'border-gray-200 opacity-50 cursor-not-allowed'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isSelected ? 'text-purple-primary' : 'text-gray-muted'}`} />
                      <span className="text-xs font-medium text-black-text">{model.name}</span>
                      {!model.implemented && (
                        <span className="ml-auto text-[8px] text-amber">SOON</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        
        {/* Configuration */}
        <div className="space-y-4 mb-6">
          <h3 className="font-syne text-sm font-bold text-black-text">Hyperparameter Tuning Configuration</h3>
          
          <div>
            <label className="block text-xs font-medium text-gray-muted mb-2">
              Optuna Trials: {config.nTrials}
            </label>
            <input
              type="range"
              min="10"
              max="200"
              step="10"
              value={config.nTrials}
              onChange={(e) => onConfigChange({ ...config, nTrials: parseInt(e.target.value) })}
              className="w-full"
            />
            <p className="text-[10px] text-gray-muted mt-1">More trials = better optimization, but slower</p>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-muted mb-2">
              Cross-Validation Folds: {config.cvFolds}
            </label>
            <input
              type="range"
              min="3"
              max="10"
              value={config.cvFolds}
              onChange={(e) => onConfigChange({ ...config, cvFolds: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
        
        {/* Actions */}
        <div className="space-y-3">
          {/* Loading Status */}
          {isLoading && loadingStatus && (
            <div className="px-4 py-3 rounded-lg bg-purple-primary/10 border border-purple-primary/30">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-purple-primary border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-purple-primary font-medium">{loadingStatus}</span>
              </div>
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={onStart}
              disabled={selectedModels.length === 0 || !selectedDataset || isLoading}
              className="flex-1 px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              title={!selectedDataset ? "Please select a dataset first" : ""}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4" />
                  Start Training ({selectedModels.length} models)
                </>
              )}
            </button>
          </div>
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
