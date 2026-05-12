import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tooltip from '@radix-ui/react-tooltip';
import {
  Layers,
  Brain,
  Zap,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Eye,
  BarChart3,
  Sparkles,
  Search,
  Filter,
  ArrowDown,
  Beaker,
  GitBranch,
  X,
  HelpCircle,
  Loader2
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { mlAPI, authAPI } from '../services/api';
import { trainingAPI } from '../services/api-complete';

export default function ModelRegistryPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(null);
  
  // Training progress state
  const [activeTrainingRun, setActiveTrainingRun] = useState(null);
  
  // Ensemble builder state
  const [showEnsembleBuilder, setShowEnsembleBuilder] = useState(false);
  const [selectedBaseModels, setSelectedBaseModels] = useState([]);
  const [datasetId, setDatasetId] = useState('');
  const [ensembleTraining, setEnsembleTraining] = useState(false);
  const [ensembleError, setEnsembleError] = useState(null);

  // Fetch models from API and load user
  useEffect(() => {
    fetchModels();
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
  
  // Load active training run from sessionStorage
  useEffect(() => {
    const loadActiveTrainingRun = () => {
      const savedRun = sessionStorage.getItem('active_training_run');
      if (savedRun) {
        try {
          const run = JSON.parse(savedRun);
          setActiveTrainingRun(run);
        } catch (error) {
          console.error('[ModelRegistry] Failed to parse active training run:', error);
        }
      } else {
        setActiveTrainingRun(null);
      }
    };

    loadActiveTrainingRun();
    
    // Poll every 3 seconds
    const interval = setInterval(loadActiveTrainingRun, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await mlAPI.getModels();
      
      // Map API response to UI format
      const mappedModels = (data.models || []).map(model => ({
        id: model.model_id,
        name: model.model_name,
        version: model.version || 'v1.0',
        algorithm: model.algorithm || extractAlgorithm(model.model_name),
        modelType: model.model_type, // 'base_model' or 'ensemble'
        status: 'promoted', // All models in registry are completed
        // Use test_auc if available, otherwise oof_auc
        accuracy: model.test_auc ? (model.test_auc * 100).toFixed(1) : 
                  model.oof_auc ? (model.oof_auc * 100).toFixed(1) : 'N/A',
        oof_auc: model.oof_auc ? (model.oof_auc * 100).toFixed(1) : 'N/A',
        test_auc: model.test_auc ? (model.test_auc * 100).toFixed(1) : 'N/A',
        precision: 'N/A', // Not available in list endpoint
        recall: 'N/A',
        f1Score: 'N/A',
        trainedDate: model.trained_at ? new Date(model.trained_at).toLocaleDateString() : 'N/A',
        samples: model.train_samples || 0,
        features: model.feature_count || 0,
        inEnsemble: model.in_ensemble || false,
        baseModelIds: model.base_model_ids || [],
        hyperparameters: model.hyperparameters || {}
      }));
      
      setModels(mappedModels);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError(err.message || 'Failed to fetch models');
    } finally {
      setLoading(false);
    }
  };

  // Extract algorithm name from model name
  const extractAlgorithm = (modelName) => {
    const parts = modelName.split(' ');
    return parts.slice(0, -1).join(' ') || modelName;
  };
  
  // Find training job for a model by algorithm name
  const findTrainingJob = (modelAlgorithm) => {
    if (!activeTrainingRun) return null;
    
    // Match by algorithm name (e.g., "xgboost", "random_forest")
    const normalizedAlgorithm = modelAlgorithm.toLowerCase().replace(/\s+/g, '_');
    const job = activeTrainingRun.jobs[normalizedAlgorithm];
    
    return job || null;
  };

  // Fetch detailed metrics for a specific model
  const fetchModelMetrics = async (modelId) => {
    try {
      const data = await mlAPI.getModelMetrics(modelId);
      setModelMetrics(data);
      setSelectedModel(modelId);
    } catch (err) {
      console.error('Error fetching model metrics:', err);
      alert(`Failed to load detailed metrics: ${err.message}`);
    }
  };

  // Handle base model selection for ensemble
  const toggleBaseModelSelection = (modelId) => {
    setSelectedBaseModels(prev => 
      prev.includes(modelId) 
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  // Sync models from MinIO
  const handleSyncFromMinIO = async () => {
    setSyncing(true);
    setSyncSuccess(null);
    setError(null);

    try {
      console.log('[ModelRegistry] Syncing models from MinIO...');
      const result = await mlAPI.syncModelsFromMinIO();
      console.log('[ModelRegistry] Sync result:', result);
      
      setSyncSuccess(result.message || `Synced ${result.synced_count} models from MinIO`);
      
      // Show success message
      alert(`✅ ${result.message}\n\nSynced: ${result.synced_count} models\nSkipped: ${result.skipped_count} models\nErrors: ${result.error_count} models`);
      
      // Refresh models list
      await fetchModels();
      
      // Clear success message after 5 seconds
      setTimeout(() => setSyncSuccess(null), 5000);
    } catch (err) {
      console.error('[ModelRegistry] Sync error:', err);
      setError(err.message || 'Failed to sync models from MinIO');
      alert(`❌ Failed to sync models: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  // Train ensemble
  const handleTrainEnsemble = async () => {
    if (selectedBaseModels.length < 2) {
      setEnsembleError('Please select at least 2 base models');
      return;
    }
    
    if (!datasetId.trim()) {
      setEnsembleError('Please enter a dataset ID');
      return;
    }

    setEnsembleTraining(true);
    setEnsembleError(null);

    try {
      const response = await mlAPI.trainEnsemble({
        dataset_id: datasetId,
        base_model_jobs: selectedBaseModels
      });
      
      alert(`Ensemble training started!\nJob ID: ${response.job_id}\nStatus: ${response.status}`);
      setShowEnsembleBuilder(false);
      setSelectedBaseModels([]);
      setDatasetId('');
      
      // Refresh models after a delay
      setTimeout(() => fetchModels(), 2000);
    } catch (err) {
      console.error('Error training ensemble:', err);
      setEnsembleError(err.message || 'Failed to start ensemble training');
    } finally {
      setEnsembleTraining(false);
    }
  };

  // Separate base learners from ensemble
  const baseLearners = models.filter(m => m.modelType === 'base_model');
  const ensembleModels = models.filter(m => m.modelType === 'ensemble');

  // Filter models
  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         model.algorithm.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || model.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const promotedCount = models.filter(m => m.status === 'promoted').length;
  const avgAccuracy = models.length > 0 
    ? (models.reduce((sum, m) => sum + parseFloat(m.accuracy), 0) / models.length).toFixed(1)
    : '0.0';

  // Loading state
  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
          <div className="text-center">
            <RefreshCw className="w-12 h-12 text-purple-primary animate-spin mx-auto mb-4" />
            <p className="text-sm text-gray-muted">Loading models from API...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout>
        <div className="h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
          <div className="bg-white/80 backdrop-blur-sm border border-red-200 rounded-2xl p-8 max-w-md">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="font-syne text-lg font-bold text-black-text mb-2 text-center">Failed to Load Models</h3>
            <p className="text-sm text-gray-muted mb-4 text-center">{error}</p>
            <button 
              onClick={fetchModels}
              className="w-full px-4 py-2 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium"
            >
              <RefreshCw className="w-4 h-4 inline mr-2" />
              Retry
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageHeader title="Model Registry" subtitle="Registry" user={user} />
      <div className="flex-1 overflow-y-auto" style={{ background: '#FAFBFC', zoom: 0.78 }}>
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          {/* Top Actions Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={fetchModels}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={() => setShowEnsembleBuilder(true)}
                disabled={baseLearners.length < 2}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-purple-200 bg-white text-purple-700 hover:bg-purple-50 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                title={baseLearners.length < 2 ? 'Need at least 2 base learners' : 'Build ensemble from base learners'}
              >
                <Sparkles className="w-4 h-4" />
                Build Ensemble
              </button>
            </div>
            <button
              onClick={() => navigate('/training')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors text-sm font-medium shadow-sm"
            >
              <Zap className="w-4 h-4" />
              Train New Model
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
              <StatCard 
                icon={Layers} 
                label="Total Models" 
                value={models.length} 
                color="purple" 
              />
              <StatCard 
                icon={CheckCircle} 
                label="Base Learners" 
                value={baseLearners.length} 
                color="blue" 
              />
              <StatCard 
                icon={Sparkles} 
                label="Ensemble Models" 
                value={ensembleModels.length} 
                color="green" 
              />
              <StatCard 
                icon={BarChart3} 
                label="Avg Accuracy" 
                value={`${avgAccuracy}%`} 
                color="amber" 
            />
          </div>

          {/* Search & Filters */}
          <div className="flex items-center gap-3">
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search models by name or algorithm..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 bg-white focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 text-sm"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2.5 rounded-lg border border-gray-200 bg-white focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 text-sm min-w-[140px]"
            >
              <option value="all">All Status</option>
              <option value="promoted">Promoted</option>
              <option value="draft">Draft</option>
            </select>
          </div>

          {/* Models */}
            {/* Ensemble Models Section */}
            {ensembleModels.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-5 py-4 bg-purple-50 border-b border-purple-100">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                    <h2 className="font-semibold text-base text-purple-700">
                      Ensemble Models
                    </h2>
                    <span className="px-2 py-0.5 rounded-full bg-purple-600 text-white text-xs font-bold">
                      {ensembleModels.length}
                    </span>
                  </div>
                </div>
                <div className="p-5 space-y-3">
                  {ensembleModels.map(model => (
                    <ModelCard 
                      key={model.id} 
                      model={model} 
                      onViewMetrics={fetchModelMetrics}
                      isEnsemble={true}
                      trainingJob={findTrainingJob(model.algorithm)}
                      onClickTraining={() => navigate('/training')}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Base Learners Section */}
            {baseLearners.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-5 py-4 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-blue-500" />
                    <h2 className="font-semibold text-base text-gray-800">
                      Base Learners
                    </h2>
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-500 text-xs font-bold">
                      {baseLearners.length}
                    </span>
                  </div>
                </div>
                <div className="p-5 grid grid-cols-2 gap-4">
                  {baseLearners.filter(model => {
                    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                         model.algorithm.toLowerCase().includes(searchQuery.toLowerCase());
                    const matchesStatus = filterStatus === 'all' || model.status === filterStatus;
                    return matchesSearch && matchesStatus;
                  }).map(model => (
                    <ModelCard 
                      key={model.id} 
                      model={model} 
                      onViewMetrics={fetchModelMetrics}
                      isEnsemble={false}
                      trainingJob={findTrainingJob(model.algorithm)}
                      onClickTraining={() => navigate('/training')}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {models.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">
                <Layers className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="font-syne text-lg font-bold text-black-text mb-2">No Models Found</h3>
                <p className="text-sm text-gray-muted mb-6">Train your first model to get started</p>
                <button
                  onClick={() => navigate('/training')}
                  className="px-6 py-3 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium"
                >
                  <Zap className="w-5 h-5 inline mr-2" />
                  Start Training
                </button>
              </div>
            )}

            {/* No Results from Filter */}
            {models.length > 0 && filteredModels.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-8 text-center shadow-sm">
                <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <h3 className="font-syne text-base font-bold text-black-text mb-1">No matching models</h3>
                <p className="text-sm text-gray-muted">Try adjusting your search or filters</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model Details Modal */}
      {selectedModel && modelMetrics && (
        <ModelMetricsModal 
          model={models.find(m => m.id === selectedModel)}
          metrics={modelMetrics}
          onClose={() => {
            setSelectedModel(null);
            setModelMetrics(null);
          }}
        />
      )}

      {/* Ensemble Builder Modal */}
      {showEnsembleBuilder && (
        <EnsembleBuilderModal
          baseLearners={baseLearners}
          selectedModels={selectedBaseModels}
          onToggleModel={toggleBaseModelSelection}
          datasetId={datasetId}
          onDatasetIdChange={setDatasetId}
          onTrain={handleTrainEnsemble}
          onClose={() => {
            setShowEnsembleBuilder(false);
            setSelectedBaseModels([]);
            setDatasetId('');
            setEnsembleError(null);
          }}
          isTraining={ensembleTraining}
          error={ensembleError}
        />
      )}
    </DashboardLayout>
  );
}

// Stat Card Component
function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    purple: { bg: 'bg-purple-dim', text: 'text-purple-primary' },
    blue: { bg: 'bg-blue-50', text: 'text-blue-500' },
    green: { bg: 'bg-green-dim', text: 'text-green' },
    amber: { bg: 'bg-amber-dim', text: 'text-amber' }
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

// Algorithm descriptions
const algorithmInfo = {
  'Random Forest': 'Ensemble of decision trees. Best for: High accuracy, handling missing data, feature importance analysis. Works well with complex medical datasets.',
  'random_forest': 'Ensemble of decision trees. Best for: High accuracy, handling missing data, feature importance analysis. Works well with complex medical datasets.',
  'XGBoost': 'Gradient boosting framework. Best for: Speed, efficiency, handling imbalanced data. Excellent for structured clinical data.',
  'xgboost': 'Gradient boosting framework. Best for: Speed, efficiency, handling imbalanced data. Excellent for structured clinical data.',
  'Gradient Boosting': 'Sequential tree boosting. Best for: High performance, reduced overfitting. Good for biomarker prediction.',
  'gradient_boosting': 'Sequential tree boosting. Best for: High performance, reduced overfitting. Good for biomarker prediction.',
  'SVM': 'Support Vector Machine. Best for: High-dimensional data, clear margin classification. Ideal for gene expression analysis.',
  'svm': 'Support Vector Machine. Best for: High-dimensional data, clear margin classification. Ideal for gene expression analysis.',
  'Logistic Regression': 'Linear classification. Best for: Interpretability, baseline models. Good for binary disease classification.',
  'logistic_regression': 'Linear classification. Best for: Interpretability, baseline models. Good for binary disease classification.',
  'Ridge Classifier': 'Regularized linear model. Best for: Preventing overfitting, multicollinearity. Suitable for correlated biomarkers.',
  'ridge_classifier': 'Regularized linear model. Best for: Preventing overfitting, multicollinearity. Suitable for correlated biomarkers.',
  'LightGBM': 'Fast gradient boosting. Best for: Large datasets, speed, memory efficiency. Great for high-volume clinical records.',
  'lightgbm': 'Fast gradient boosting. Best for: Large datasets, speed, memory efficiency. Great for high-volume clinical records.',
  'K-Nearest Neighbors': 'Instance-based learning. Best for: Pattern recognition, small datasets. Good for patient similarity matching.',
  'knn': 'Instance-based learning. Best for: Pattern recognition, small datasets. Good for patient similarity matching.',
  'Decision Tree': 'Tree-based classifier. Best for: Interpretability, feature selection. Useful for clinical decision rules.',
  'decision_tree': 'Tree-based classifier. Best for: Interpretability, feature selection. Useful for clinical decision rules.',
  'Discriminant Analysis': 'Linear discriminant. Best for: Dimensionality reduction, multiclass problems. Good for subtype classification.',
  'discriminant_analysis': 'Linear discriminant. Best for: Dimensionality reduction, multiclass problems. Good for subtype classification.',
  'ANN (MLP)': 'Neural network. Best for: Complex patterns, non-linear relationships. Powerful for multi-modal medical data.',
  'ann': 'Neural network. Best for: Complex patterns, non-linear relationships. Powerful for multi-modal medical data.',
  'mlp': 'Neural network. Best for: Complex patterns, non-linear relationships. Powerful for multi-modal medical data.',
  'Ensemble': 'Combines multiple models. Best for: Maximum accuracy, robust predictions. Meta-learner for final diagnosis.',
  'ensemble': 'Combines multiple models. Best for: Maximum accuracy, robust predictions. Meta-learner for final diagnosis.',
  'default': 'Machine learning algorithm for classification tasks.'
};

// Model Card Component
function ModelCard({ model, onViewMetrics, isEnsemble, trainingJob, onClickTraining }) {
  const [showTooltip, setShowTooltip] = useState(false);
  
  // Check if model is currently training
  const isTraining = trainingJob && (trainingJob.status === 'queued' || trainingJob.status === 'running');
  
  const statusConfig = {
    promoted: { color: 'text-green', bg: 'bg-green-dim', label: 'Promoted' },
    draft: { color: 'text-amber', bg: 'bg-amber-dim', label: 'Draft' }
  };
  const status = statusConfig[model.status];
  
  const algorithmDescription = algorithmInfo[model.algorithm] || algorithmInfo['default'];

  return (
    <div 
      className={`bg-white/60 border border-white/40 rounded-xl p-4 hover:shadow-lg hover:border-purple-primary/40 transition-all group ${isTraining ? 'cursor-pointer' : ''}`}
      onClick={isTraining ? onClickTraining : undefined}
    >
      <div className="flex items-start gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg ${isEnsemble ? 'bg-gradient-to-br from-purple-primary to-purple-primary/80' : 'bg-gradient-to-br from-blue-500 to-blue-600'} flex items-center justify-center flex-shrink-0 relative`}>
          {isTraining ? (
            <Loader2 className="w-5 h-5 text-white animate-spin" />
          ) : isEnsemble ? (
            <Sparkles className="w-5 h-5 text-white" />
          ) : (
            <Brain className="w-5 h-5 text-white" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm text-black-text mb-1 truncate">{model.name}</h3>
          <div className="flex items-center gap-2 text-xs">
            {isTraining ? (
              <span className="px-2 py-0.5 rounded bg-amber-dim text-amber font-medium flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                {trainingJob.status === 'queued' ? 'Queued' : 'Training'}
              </span>
            ) : (
              <span className={`px-2 py-0.5 rounded ${status.bg} ${status.color} font-medium`}>
                {status.label}
              </span>
            )}
            <span className="text-gray-muted">{model.algorithm}</span>
            <div className="relative">
              <HelpCircle 
                className="w-3.5 h-3.5 text-purple-primary cursor-help" 
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
              />
              {showTooltip && (
                <div className="absolute left-0 top-5 z-10 w-64 p-3 bg-black/90 text-white text-xs rounded-lg shadow-lg">
                  <div className="font-semibold mb-1">{model.algorithm}</div>
                  <div className="text-white/90">{algorithmDescription}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Training Progress Bar */}
      {isTraining && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-muted mb-1">
            <span>Training Progress</span>
            <span>{trainingJob.progress || 0}%</span>
          </div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-amber to-amber/60 transition-all duration-500"
              style={{ width: `${trainingJob.progress || 5}%` }}
            />
          </div>
          <div className="mt-2 text-xs text-amber font-medium">
            Click to view training details
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="bg-white/80 rounded-lg p-2">
          <div className="text-[10px] text-gray-muted mb-0.5">Accuracy</div>
          <div className="font-bold text-sm text-purple-primary">{model.accuracy}%</div>
        </div>
        <div className="bg-white/80 rounded-lg p-2">
          <div className="text-[10px] text-gray-muted mb-0.5">Precision</div>
          <div className="font-bold text-sm text-black-text">{model.precision}%</div>
        </div>
        <div className="bg-white/80 rounded-lg p-2">
          <div className="text-[10px] text-gray-muted mb-0.5">Recall</div>
          <div className="font-bold text-sm text-black-text">{model.recall}%</div>
        </div>
        <div className="bg-white/80 rounded-lg p-2">
          <div className="text-[10px] text-gray-muted mb-0.5">F1 Score</div>
          <div className="font-bold text-sm text-black-text">{model.f1Score}%</div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-muted pt-3 border-t border-white/40">
        <div className="flex items-center gap-3">
          <span>{model.samples} samples</span>
          <span>•</span>
          <span>{model.features} features</span>
        </div>
        <button
          onClick={() => onViewMetrics(model.id)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium opacity-0 group-hover:opacity-100"
        >
          <Eye className="w-3.5 h-3.5" />
          Details
        </button>
      </div>

      {isEnsemble && model.baseModelIds.length > 0 && (
        <div className="mt-2 pt-2 border-t border-white/40">
          <div className="flex items-center gap-1.5 text-xs text-purple-primary">
            <GitBranch className="w-3.5 h-3.5" />
            <span className="font-medium">Uses {model.baseModelIds.length} base learners</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Model Metrics Modal
function ModelMetricsModal({ model, metrics, onClose }) {
  if (!model || !metrics) return null;

  return (
    <Dialog.Root open={true} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-xl z-50">
          <div className="px-6 py-5 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <Dialog.Title className="font-syne text-xl font-bold text-black-text">{model.name}</Dialog.Title>
                <Dialog.Description className="text-sm text-gray-muted mt-1">Detailed Metrics & Performance</Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <button
                  className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors"
                >
                  <X className="w-5 h-5 text-gray-muted" />
                </button>
              </Dialog.Close>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Main Metrics */}
            <div>
              <h3 className="font-semibold text-sm text-black-text mb-3">Classification Metrics</h3>
              <div className="grid grid-cols-4 gap-4">
                <MetricBox label="Accuracy" value={`${model.accuracy}%`} />
                <MetricBox label="Precision" value={`${model.precision}%`} />
                <MetricBox label="Recall" value={`${model.recall}%`} />
                <MetricBox label="F1 Score" value={`${model.f1Score}%`} />
              </div>
            </div>

            {/* Additional Metrics from API */}
            {metrics.auc_roc && (
              <div>
                <h3 className="font-semibold text-sm text-black-text mb-3">Advanced Metrics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <MetricBox label="AUC-ROC" value={metrics.auc_roc.toFixed(3)} />
                  {metrics.specificity && <MetricBox label="Specificity" value={metrics.specificity.toFixed(3)} />}
                </div>
              </div>
            )}

            {/* Training Info */}
            <div>
              <h3 className="font-semibold text-sm text-black-text mb-3">Training Information</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-muted">Training Samples:</span>
                  <span className="font-medium text-black-text">{model.samples}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-muted">Features:</span>
                  <span className="font-medium text-black-text">{model.features}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-muted">Algorithm:</span>
                  <span className="font-medium text-black-text">{model.algorithm}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-muted">Version:</span>
                  <span className="font-medium text-black-text">{model.version}</span>
                </div>
              </div>
            </div>

            {/* Confusion Matrix */}
            {metrics.confusion_matrix && (
              <div>
                <h3 className="font-semibold text-sm text-black-text mb-3">Confusion Matrix</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-xs font-mono">{JSON.stringify(metrics.confusion_matrix, null, 2)}</pre>
                </div>
              </div>
            )}

            {/* Actions */}
            <Tooltip.Provider delayDuration={300}>
              <div className="flex gap-3 pt-4 border-t">
                <Tooltip.Root>
                  <Tooltip.Trigger asChild>
                    <button className="flex-1 px-4 py-2.5 rounded-lg border border-purple-primary/20 bg-white text-purple-primary hover:bg-purple-dim transition-colors font-medium">
                      <Download className="w-4 h-4 inline mr-2" />
                      Export Model
                    </button>
                  </Tooltip.Trigger>
                  <Tooltip.Portal>
                    <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
                      Download model artifacts
                      <Tooltip.Arrow className="fill-gray-900" />
                    </Tooltip.Content>
                  </Tooltip.Portal>
                </Tooltip.Root>

                <Tooltip.Root>
                  <Tooltip.Trigger asChild>
                    <button className="flex-1 px-4 py-2.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium">
                      <Zap className="w-4 h-4 inline mr-2" />
                      Deploy Model
                    </button>
                  </Tooltip.Trigger>
                  <Tooltip.Portal>
                    <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
                      Deploy to production
                      <Tooltip.Arrow className="fill-gray-900" />
                    </Tooltip.Content>
                  </Tooltip.Portal>
                </Tooltip.Root>
              </div>
            </Tooltip.Provider>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function MetricBox({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="text-xs text-gray-muted mb-1">{label}</div>
      <div className="font-syne text-2xl font-bold text-purple-primary">{value}</div>
    </div>
  );
}

// Ensemble Builder Modal
function EnsembleBuilderModal({ 
  baseLearners, 
  selectedModels, 
  onToggleModel, 
  datasetId, 
  onDatasetIdChange, 
  onTrain, 
  onClose, 
  isTraining,
  error 
}) {
  const allSelected = selectedModels.length === baseLearners.length && baseLearners.length > 0;
  const someSelected = selectedModels.length > 0 && selectedModels.length < baseLearners.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      baseLearners.forEach(model => onToggleModel(model.id));
    } else {
      baseLearners.forEach(model => {
        if (!selectedModels.includes(model.id)) {
          onToggleModel(model.id);
        }
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-5 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-syne text-xl font-bold text-black-text">Build Ensemble Model</h2>
                <p className="text-sm text-gray-muted mt-0.5">
                  Combine base learners to create a more powerful meta-learner
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isTraining}
              className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors disabled:opacity-50"
            >
              <X className="w-5 h-5 text-gray-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Info Banner */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex gap-3">
              <Beaker className="w-5 h-5 text-purple-primary flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="font-semibold text-purple-primary mb-1">
                  What is Stacking Ensemble?
                </div>
                <div className="text-gray-700 leading-relaxed">
                  Stacking combines predictions from multiple base learners using a meta-learner. 
                  The meta-learner learns which models to trust for different types of cases, 
                  typically achieving higher accuracy than any individual model.
                </div>
              </div>
            </div>
          </div>

          {/* Dataset ID Input */}
          <div>
            <label className="block text-sm font-semibold text-black-text mb-2">
              Dataset ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={datasetId}
              onChange={(e) => onDatasetIdChange(e.target.value)}
              placeholder="Enter dataset ID (e.g., dataset_001)"
              disabled={isTraining}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <p className="text-xs text-gray-muted mt-1.5">
              Use the same dataset ID that was used to train the base models
            </p>
          </div>

          {/* Base Learner Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-semibold text-black-text">
                Select Base Learners <span className="text-red-500">*</span>
                <span className="text-gray-muted font-normal ml-2">
                  (minimum 2 required)
                </span>
              </label>
              <button
                onClick={toggleSelectAll}
                disabled={isTraining || baseLearners.length === 0}
                className="text-xs text-purple-primary hover:text-purple-primary/80 font-medium disabled:opacity-50"
              >
                {allSelected ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="border border-gray-200 rounded-lg max-h-[320px] overflow-y-auto">
              {baseLearners.length === 0 ? (
                <div className="p-8 text-center">
                  <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-muted">No base learners available</p>
                  <p className="text-xs text-gray-muted mt-1">Train some base models first</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {baseLearners.map((model) => {
                    const isSelected = selectedModels.includes(model.id);
                    return (
                      <label
                        key={model.id}
                        className={`flex items-center gap-3 p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                          isSelected ? 'bg-purple-50/50' : ''
                        } ${isTraining ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => onToggleModel(model.id)}
                          disabled={isTraining}
                          className="w-4 h-4 text-purple-primary rounded border-gray-300 focus:ring-purple-primary"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm text-black-text truncate">
                              {model.name}
                            </span>
                            <span className="text-xs text-gray-muted">
                              ({model.algorithm})
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-gray-muted">
                            <span>Accuracy: <span className="font-medium text-purple-primary">{model.accuracy}%</span></span>
                            <span>F1: {model.f1Score}%</span>
                            <span>{model.samples} samples</span>
                          </div>
                        </div>
                        {isSelected && (
                          <CheckCircle className="w-5 h-5 text-purple-primary flex-shrink-0" />
                        )}
                      </label>
                    );
                  })}
                </div>
              )}
            </div>

            {selectedModels.length > 0 && (
              <div className="mt-2 flex items-center gap-2 text-sm">
                <div className="flex items-center gap-1.5 text-purple-primary">
                  <CheckCircle className="w-4 h-4" />
                  <span className="font-medium">{selectedModels.length} models selected</span>
                </div>
                {selectedModels.length < 2 && (
                  <span className="text-amber-600 text-xs">• Need at least 2 models</span>
                )}
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              disabled={isTraining}
              className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={onTrain}
              disabled={isTraining || selectedModels.length < 2 || !datasetId.trim()}
              className="flex-1 px-4 py-2.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isTraining ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Training Ensemble...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Train Ensemble
                </>
              )}
            </button>
          </div>

          {/* Meta-learner Info */}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
            <div className="font-semibold text-black-text mb-1">ℹ️ Default Configuration</div>
            <div className="space-y-0.5">
              <div>• Meta-learner: Logistic Regression (optimized for stacking)</div>
              <div>• CV Strategy: 5-fold stratified cross-validation</div>
              <div>• Prediction method: Out-of-fold predictions (prevents overfitting)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
