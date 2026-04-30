import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Settings,
  Brain,
  Zap,
  Play,
  TrendingUp,
  BarChart3,
  Save,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Target,
  Cpu,
  Database,
  Layers,
  Copy,
  Grid3x3,
  Shuffle,
  GitBranch,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  Sliders,
  Beaker,
  Award,
  ArrowUpCircle,
  DollarSign,
  Timer,
  Lock,
  ChevronUp,
  Star,
  History,
  Search,
  Filter,
  Download,
  Code,
  Plus,
  Trash2,
  RotateCcw,
  Gauge,
  AlertTriangle,
  Info,
  ThumbsUp,
  Flame,
  Snowflake,
  Activity,
  GitCompare,
  Shield
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function HyperparameterTuningPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Main state
  const [selectedModel, setSelectedModel] = useState('Random Forest');
  const [selectedDataset, setSelectedDataset] = useState('AAM-SLE-E v2.1');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showComparison, setShowComparison] = useState(false);
  const [selectedExperiments, setSelectedExperiments] = useState([]);

  // Mock experiment history
  const [experiments, setExperiments] = useState([
    {
      id: 'exp-042',
      name: 'Random Forest Tuning',
      model: 'Random Forest',
      status: 'completed',
      accuracy: 87.3,
      f1Score: 87.1,
      runtime: '2m 14s',
      cost: '$1.20',
      timestamp: '2024-04-03 14:23',
      starred: true,
      params: { n_estimators: 200, max_depth: 15, min_samples_split: 5 },
      dataset: 'AAM-SLE-E v2.1'
    },
    {
      id: 'exp-041',
      name: 'XGBoost Baseline',
      model: 'XGBoost',
      status: 'completed',
      accuracy: 85.2,
      f1Score: 84.9,
      runtime: '3m 45s',
      cost: '$2.10',
      timestamp: '2024-04-03 13:15',
      starred: false,
      params: { max_depth: 8, learning_rate: 0.1, n_estimators: 150 },
      dataset: 'AAM-SLE-E v2.1'
    },
    {
      id: 'exp-040',
      name: 'LightGBM Fast Run',
      model: 'LightGBM',
      status: 'running',
      accuracy: 0,
      progress: 68,
      runtime: '1m 32s',
      estimatedTime: '48s',
      timestamp: '2024-04-03 14:28',
      starred: false,
      params: { num_leaves: 31, learning_rate: 0.12, n_estimators: 100 },
      dataset: 'AAM-SLE-E v2.1'
    },
    {
      id: 'exp-039',
      name: 'SVM Grid Search',
      model: 'SVM',
      status: 'failed',
      error: 'CUDA OOM',
      runtime: '0m 45s',
      timestamp: '2024-04-03 12:05',
      starred: false,
      params: { kernel: 'rbf', C: 1.5, gamma: 'scale' },
      dataset: 'AAM-SLE-E v2.1'
    },
    {
      id: 'exp-038',
      name: 'Gradient Boosting v2',
      model: 'Gradient Boosting',
      status: 'completed',
      accuracy: 86.2,
      f1Score: 86.0,
      runtime: '2m 55s',
      cost: '$1.45',
      timestamp: '2024-04-03 11:30',
      starred: true,
      params: { learning_rate: 0.05, n_estimators: 200, subsample: 0.8 },
      dataset: 'AAM-SLE-E v2.1'
    }
  ]);

  // Parameter presets
  const [parameters, setParameters] = useState({
    n_estimators: 100,
    max_depth: 15,
    min_samples_split: 5,
    learning_rate: 0.1
  });

  const modelOptions = [
    { name: 'Random Forest', type: 'Classification', popular: true },
    { name: 'XGBoost', type: 'Classification', popular: true },
    { name: 'Gradient Boosting', type: 'Classification', popular: true },
    { name: 'LightGBM', type: 'Classification', popular: true },
    { name: 'ANN (MLP)', type: 'Deep Learning', popular: true },
    { name: 'Support Vector Machine', type: 'Classification', popular: false },
    { name: 'Logistic Regression', type: 'Classification', popular: false },
    { name: 'Ridge Classifier', type: 'Classification', popular: false },
    { name: 'K-Nearest Neighbors', type: 'Classification', popular: false },
    { name: 'Decision Tree', type: 'Classification', popular: false },
    { name: 'Discriminant Analysis', type: 'Classification', popular: false }
  ];

  const handleStarExperiment = (id) => {
    setExperiments(prev => prev.map(exp => 
      exp.id === id ? { ...exp, starred: !exp.starred } : exp
    ));
  };

  const handleCloneExperiment = (experiment) => {
    setSelectedModel(experiment.model);
    setParameters(experiment.params);
    setSelectedDataset(experiment.dataset);
  };

  const filteredExperiments = experiments.filter(exp => {
    const matchesSearch = exp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         exp.model.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || exp.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white/60 backdrop-blur-sm border-b border-white/20">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-syne text-lg font-bold text-black-text">Hyperparameter Tuning</h1>
              <span className="px-2 py-0.5 rounded-md bg-purple-dim text-purple-primary text-[10px] font-semibold">
                {experiments.filter(e => e.status === 'running').length} running
              </span>
              <span className="px-2 py-0.5 rounded-md bg-green-dim text-green text-[10px] font-semibold">
                {experiments.filter(e => e.starred).length} starred
              </span>
            </div>
            <p className="text-xs text-gray-muted mt-0.5">Experiment, iterate, and optimize ML models</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowComparison(!showComparison)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/40 hover:border-purple-primary/40 hover:bg-white/60 text-gray-muted hover:text-purple-primary text-sm transition-all"
              disabled={selectedExperiments.length < 2}
            >
              <BarChart3 className="w-4 h-4" />
              Compare ({selectedExperiments.length})
            </button>
            <button
              onClick={() => navigate('/models')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/40 hover:border-purple-primary/40 hover:bg-white/60 text-gray-muted hover:text-purple-primary text-sm transition-all"
            >
              <Layers className="w-4 h-4" />
              Model Registry
            </button>
          </div>
        </div>

        {/* 3-Column Layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* LEFT: Experiment Tracker Sidebar */}
          <div className="w-[300px] border-r border-white/20 bg-white/40 backdrop-blur-sm overflow-y-auto">
            <div className="p-4 border-b border-white/20 bg-white/60">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-syne text-sm font-bold text-black-text flex items-center gap-2">
                  <History className="w-4 h-4" />
                  Experiment History
                </h2>
                <span className="text-xs text-gray-muted">{filteredExperiments.length} runs</span>
              </div>
              
              {/* Search */}
              <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search experiments..."
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-white/40 bg-white/80 text-xs focus:outline-none focus:border-purple-primary"
                />
              </div>
              
              {/* Filters */}
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-lg border border-white/40 bg-white/80 text-xs focus:outline-none focus:border-purple-primary"
                >
                  <option value="all">All Status</option>
                  <option value="running">Running</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>
            
            {/* Experiment List */}
            <div className="p-2 space-y-2">
              {filteredExperiments.map((exp) => (
                <ExperimentCard
                  key={exp.id}
                  experiment={exp}
                  onStar={handleStarExperiment}
                  onClone={handleCloneExperiment}
                  isSelected={selectedExperiments.includes(exp.id)}
                  onSelect={(id) => {
                    if (selectedExperiments.includes(id)) {
                      setSelectedExperiments(prev => prev.filter(i => i !== id));
                    } else {
                      setSelectedExperiments(prev => [...prev, id]);
                    }
                  }}
                />
              ))}
            </div>
          </div>

          {/* CENTER: Main Panel */}
          <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-gray-50 to-purple-50/20">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Quick Start Templates */}
              <QuickStartTemplates 
                onSelectTemplate={(params) => {
                  setParameters(params);
                }}
              />
              
              {/* Visual Parameter Studio */}
              <VisualParameterStudio
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                parameters={parameters}
                setParameters={setParameters}
                modelOptions={modelOptions}
              />
              
              {/* One-Click Actions */}
              <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
                <h3 className="font-syne text-base font-bold text-black-text mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-primary" />
                  Quick Actions
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  <button className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/40 hover:border-purple-primary/40 hover:bg-purple-dim transition-all">
                    <Play className="w-6 h-6 text-purple-primary" />
                    <span className="text-sm font-medium text-black-text">Start Training</span>
                  </button>
                  <button className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/40 hover:border-purple-primary/40 hover:bg-purple-dim transition-all">
                    <Code className="w-6 h-6 text-purple-primary" />
                    <span className="text-sm font-medium text-black-text">Export Code</span>
                  </button>
                  <button className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/40 hover:border-purple-primary/40 hover:bg-purple-dim transition-all">
                    <Download className="w-6 h-6 text-purple-primary" />
                    <span className="text-sm font-medium text-black-text">Export Config</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT: Live Results Board */}
          <div className="w-[320px] border-l border-white/20 bg-white/40 backdrop-blur-sm overflow-y-auto">
            <LiveResultsBoard 
              experiments={experiments}
              selectedExperiments={selectedExperiments}
              showComparison={showComparison}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// ================================
// EXPERIMENT CARD COMPONENT
// ================================
function ExperimentCard({ experiment, onStar, onClone, onSelect, isSelected }) {
  const statusColors = {
    completed: 'bg-green-dim text-green border-green/20',
    running: 'bg-amber-dim text-amber border-amber/20',
    failed: 'bg-red-50 text-red-600 border-red-200',
    queued: 'bg-gray-100 text-gray-muted border-gray-300'
  };

  return (
    <div className={`bg-white/60 border rounded-lg p-3 hover:bg-white/80 transition-all ${
      isSelected ? 'border-purple-primary ring-2 ring-purple-primary/20' : 'border-white/40'
    }`}>
      {/* Header Row */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect(experiment.id)}
              className="accent-purple-primary"
            />
            <h4 className="font-semibold text-sm text-black-text truncate">{experiment.name}</h4>
          </div>
          <div className="text-xs text-gray-muted mt-0.5">{experiment.model}</div>
        </div>
        <button
          onClick={() => onStar(experiment.id)}
          className="text-amber hover:scale-110 transition-transform flex-shrink-0"
        >
          <Star className={`w-4 h-4 ${experiment.starred ? 'fill-amber' : ''}`} />
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-2 mb-2 text-xs">
        <div className="bg-purple-dim/30 rounded px-2 py-1">
          <div className="text-gray-muted">Accuracy</div>
          <div className="font-bold text-purple-primary">{experiment.accuracy}%</div>
        </div>
        <div className="bg-white/60 rounded px-2 py-1">
          <div className="text-gray-muted">F1</div>
          <div className="font-bold text-black-text">{experiment.f1Score}%</div>
        </div>
      </div>

      {/* Status & Actions */}
      <div className="flex items-center justify-between">
        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${statusColors[experiment.status]}`}>
          {experiment.status.toUpperCase()}
        </span>
        <button
          onClick={() => onClone(experiment)}
          className="text-purple-primary hover:bg-purple-dim/30 rounded p-1 transition-colors"
          title="Clone experiment"
        >
          <Copy className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

// ================================
// QUICK START TEMPLATES
// ================================
function QuickStartTemplates({ onSelectTemplate }) {
  const templates = [
    {
      id: 'conservative',
      name: 'Conservative',
      icon: Shield,
      description: 'Safe defaults, minimal overfitting risk',
      color: 'blue',
      params: { n_estimators: 100, max_depth: 10, learning_rate: 0.01, min_samples_split: 10 }
    },
    {
      id: 'balanced',
      name: 'Balanced',
      icon: Target,
      description: 'Recommended for most use cases',
      color: 'purple',
      params: { n_estimators: 200, max_depth: 15, learning_rate: 0.05, min_samples_split: 5 }
    },
    {
      id: 'aggressive',
      name: 'Aggressive',
      icon: Zap,
      description: 'Max performance, watch for overfitting',
      color: 'amber',
      params: { n_estimators: 500, max_depth: 25, learning_rate: 0.1, min_samples_split: 2 }
    }
  ];

  const colorMap = {
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', hover: 'hover:bg-blue-100' },
    purple: { bg: 'bg-purple-dim', border: 'border-purple-primary/30', text: 'text-purple-primary', hover: 'hover:bg-purple-primary/10' },
    amber: { bg: 'bg-amber-dim', border: 'border-amber/30', text: 'text-amber', hover: 'hover:bg-amber/20' }
  };

  return (
    <div className="grid grid-cols-3 gap-3">
      {templates.map(template => {
        const colors = colorMap[template.color];
        const Icon = template.icon;
        return (
          <button
            key={template.id}
            onClick={() => onSelectTemplate(template.params)}
            className={`${colors.bg} ${colors.border} border-2 rounded-xl p-4 text-left ${colors.hover} transition-all group`}
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-5 h-5 ${colors.text}`} />
              <h4 className={`font-syne font-bold text-sm ${colors.text}`}>{template.name}</h4>
            </div>
            <p className="text-xs text-gray-muted mb-3">{template.description}</p>
            <div className="flex items-center gap-1 text-xs font-medium text-purple-primary opacity-0 group-hover:opacity-100 transition-opacity">
              <Play className="w-3 h-3" />
              Apply Preset
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ================================
// VISUAL PARAMETER STUDIO
// ================================
function VisualParameterStudio({ parameters, setParameters, modelOptions, selectedModel, setSelectedModel }) {
  const parameterConfig = {
    n_estimators: { label: 'Number of Estimators', min: 50, max: 1000, step: 50, description: 'More trees = better accuracy but slower' },
    max_depth: { label: 'Maximum Tree Depth', min: 3, max: 50, step: 1, description: 'Deeper trees capture complexity but risk overfitting' },
    learning_rate: { label: 'Learning Rate', min: 0.001, max: 0.3, step: 0.001, description: 'Lower = more conservative, higher = faster convergence' },
    min_samples_split: { label: 'Min Samples to Split', min: 2, max: 20, step: 1, description: 'Higher = more conservative splits' }
  };

  return (
    <div className="space-y-4">
      {/* Model & Dataset Selection */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-muted uppercase tracking-wider mb-2">
            Model Algorithm
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm font-medium focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
          >
            {modelOptions.map(model => (
              <option key={model.name} value={model.name}>{model.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-muted uppercase tracking-wider mb-2">
            Training Dataset
          </label>
          <select
            className="w-full px-3 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm font-medium focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
          >
            <option>AAM-SLE-E v2.1 (1,204 samples)</option>
            <option>AAM-SLE-E v2.0 (1,187 samples)</option>
            <option>HUSM_batch3 (856 samples)</option>
          </select>
        </div>
      </div>

      {/* Smart Parameter Sliders */}
      <div className="bg-white/80 border border-white/40 rounded-xl p-4 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Sliders className="w-4 h-4 text-purple-primary" />
          <h4 className="font-semibold text-sm text-black-text">Hyperparameters</h4>
        </div>
        
        {Object.entries(parameterConfig).map(([paramName, config]) => (
          <div key={paramName} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-black-text">{config.label}</label>
              <span className="text-sm font-bold text-purple-primary px-2 py-0.5 bg-purple-dim rounded">
                {parameters[paramName]}
              </span>
            </div>
            <input
              type="range"
              min={config.min}
              max={config.max}
              step={config.step}
              value={parameters[paramName]}
              onChange={(e) => setParameters({ ...parameters, [paramName]: parseFloat(e.target.value) })}
              className="w-full h-2 bg-purple-dim/30 rounded-lg appearance-none cursor-pointer accent-purple-primary"
            />
            <div className="text-[10px] text-gray-muted">{config.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ================================
// LIVE RESULTS BOARD
// ================================
function LiveResultsBoard({ experiments, selectedExperiments, showComparison }) {
  const runningExperiments = experiments.filter(e => e.status === 'running');
  const starredCompleted = experiments.filter(e => e.status === 'completed' && e.starred);

  if (showComparison && selectedExperiments.length > 0) {
    return (
      <div className="bg-white/80 border border-white/40 rounded-2xl">
        <div className="px-4 py-3 border-b border-white/40 bg-white/60">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-purple-primary" />
            <h3 className="font-semibold text-sm text-black-text">Compare ({selectedExperiments.length})</h3>
          </div>
        </div>
        <div className="p-4 space-y-2 max-h-[600px] overflow-y-auto">
          {selectedExperiments.map(expId => {
            const exp = experiments.find(e => e.id === expId);
            return (
              <div key={exp.id} className="bg-purple-dim/20 border border-purple-primary/20 rounded-lg p-3">
                <div className="font-medium text-xs text-black-text mb-2">{exp.name}</div>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <div className="text-gray-muted">Accuracy</div>
                    <div className="font-bold text-purple-primary">{exp.accuracy}%</div>
                  </div>
                  <div>
                    <div className="text-gray-muted">F1</div>
                    <div className="font-bold">{exp.f1Score}%</div>
                  </div>
                  <div>
                    <div className="text-gray-muted">Runtime</div>
                    <div className="font-medium">{exp.runtime}</div>
                  </div>
                  <div>
                    <div className="text-gray-muted">Cost</div>
                    <div className="font-medium">${exp.cost}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Running Experiments */}
      {runningExperiments.length > 0 && (
        <div className="bg-white/80 border border-white/40 rounded-2xl">
          <div className="px-4 py-3 border-b border-white/40 bg-amber-dim/20">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber" />
              <h3 className="font-semibold text-sm text-black-text">Running Now</h3>
              <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-dim text-amber text-xs font-bold">
                {runningExperiments.length}
              </span>
            </div>
          </div>
          <div className="p-4 space-y-3">
            {runningExperiments.map(exp => (
              <div key={exp.id} className="bg-amber-dim/20 border border-amber/20 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-xs text-black-text">{exp.name}</div>
                  <Activity className="w-3 h-3 text-amber animate-pulse" />
                </div>
                <div className="w-full bg-white/60 rounded-full h-1.5 mb-2">
                  <div className="bg-amber h-1.5 rounded-full" style={{ width: '67%' }}></div>
                </div>
                <div className="text-[10px] text-gray-muted">2.3 min elapsed • ~1.2 min remaining</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Starred Completed */}
      {starredCompleted.length > 0 && (
        <div className="bg-white/80 border border-white/40 rounded-2xl">
          <div className="px-4 py-3 border-b border-white/40 bg-white/60">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-amber fill-amber" />
              <h3 className="font-semibold text-sm text-black-text">Top Starred</h3>
            </div>
          </div>
          <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto">
            {starredCompleted.slice(0, 5).map(exp => (
              <div key={exp.id} className="bg-gradient-to-br from-green-50 to-green-50/50 border border-green-200 rounded-lg p-3">
                <div className="font-medium text-xs text-black-text mb-1">{exp.name}</div>
                <div className="flex items-center gap-3 text-[10px]">
                  <div>
                    <span className="text-gray-muted">Acc: </span>
                    <span className="font-bold text-green-600">{exp.accuracy}%</span>
                  </div>
                  <div>
                    <span className="text-gray-muted">F1: </span>
                    <span className="font-bold">{exp.f1Score}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ================================
// UTILITY COMPONENTS
// ================================
function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    purple: { bg: 'bg-purple-dim', text: 'text-purple-primary' },
    green: { bg: 'bg-green-dim', text: 'text-green' },
    amber: { bg: 'bg-amber-dim', text: 'text-amber' },
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

function ParameterControl({ name, label, min, max, step, value, onChange }) {
  return (
    <div className="bg-white/60 rounded-lg p-3 border border-white/40">
      <div className="flex items-center justify-between mb-2">
        <label className="text-xs font-medium text-black-text">{label}</label>
        <span className="text-xs font-bold text-purple-primary">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || parseInt(e.target.value))}
        className="w-full h-2 bg-purple-dim/30 rounded-lg appearance-none cursor-pointer accent-purple-primary"
      />
    </div>
  );
}

function StatusBadge({ status }) {
  const configs = {
    completed: { color: 'text-green', bg: 'bg-green-dim', icon: CheckCircle },
    running: { color: 'text-amber', bg: 'bg-amber-dim', icon: Zap },
    queued: { color: 'text-blue-500', bg: 'bg-blue-50', icon: Clock },
    failed: { color: 'text-red', bg: 'bg-red-dim', icon: AlertCircle }
  };
  const config = configs[status];
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${config.bg} ${config.color}`}>
      <Icon className="w-3 h-3" />
      <span className="text-xs font-medium capitalize">{status}</span>
    </div>
  );
}
