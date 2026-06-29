import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Search,
  Filter,
  Calendar,
  Clock,
  User,
  GitBranch,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Play,
  Download,
  Eye,
  Copy,
  Star,
  Tag,
  BarChart3,
  Cpu,
  TrendingUp,
  Award
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function ExperimentLogPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterModel, setFilterModel] = useState('all');
  const [timeRange, setTimeRange] = useState('7days');
  const [selectedExperiments, setSelectedExperiments] = useState([]);

  // Mock experiment data
  const experiments = [
    {
      id: 'EXP-2024-0087',
      name: 'SLE Classifier - Ensemble v3.2',
      model: 'Ensemble (RF + XGBoost + LightGBM)',
      status: 'completed',
      accuracy: 91.8,
      f1Score: 91.2,
      precision: 92.1,
      recall: 90.3,
      auc: 0.956,
      runtime: '4h 23m',
      dataset: 'AAM-SLE-E v2.1',
      samples: 1204,
      features: 47,
      hyperparameters: {
        n_estimators: 200,
        max_depth: 15,
        learning_rate: 0.05
      },
      author: 'Dr. Sarah Chen',
      timestamp: '2024-04-08 14:23',
      starred: true,
      tags: ['production', 'ensemble', 'validated'],
      notes: 'Best performing model to date. Recommended for production deployment.'
    },
    {
      id: 'EXP-2024-0086',
      name: 'RA Binary Classifier - XGBoost Tuned',
      model: 'XGBoost',
      status: 'completed',
      accuracy: 89.5,
      f1Score: 88.9,
      precision: 90.2,
      recall: 87.6,
      auc: 0.942,
      runtime: '2h 47m',
      dataset: 'RA-cohort v1.8',
      samples: 856,
      features: 52,
      hyperparameters: {
        n_estimators: 150,
        max_depth: 10,
        learning_rate: 0.1
      },
      author: 'Dr. Michael Torres',
      timestamp: '2024-04-08 11:15',
      starred: false,
      tags: ['ra', 'xgboost', 'tuned'],
      notes: 'Hyperparameter tuning improved accuracy by 2.3%'
    },
    {
      id: 'EXP-2024-0085',
      name: 'Multi-class Autoimmune Classifier',
      model: 'Random Forest',
      status: 'running',
      accuracy: null,
      progress: 67,
      estimatedTime: '1h 15m remaining',
      dataset: 'Multi-disease v3.0',
      samples: 3421,
      features: 89,
      hyperparameters: {
        n_estimators: 500,
        max_depth: 25
      },
      author: 'Dr. Emily Watson',
      timestamp: '2024-04-08 15:30',
      starred: false,
      tags: ['multi-class', 'in-progress'],
      notes: 'Testing increased complexity on larger dataset'
    },
    {
      id: 'EXP-2024-0084',
      name: 'Sjögren Syndrome Detector - LightGBM',
      model: 'LightGBM',
      status: 'completed',
      accuracy: 87.2,
      f1Score: 86.8,
      precision: 88.1,
      recall: 85.5,
      auc: 0.928,
      runtime: '1h 52m',
      dataset: 'Sjögren-cohort v2.3',
      samples: 642,
      features: 38,
      hyperparameters: {
        num_leaves: 31,
        learning_rate: 0.05,
        n_estimators: 200
      },
      author: 'Dr. David Kim',
      timestamp: '2024-04-07 16:45',
      starred: true,
      tags: ['sjogren', 'validated'],
      notes: 'Strong performance on rare disease classification'
    },
    {
      id: 'EXP-2024-0083',
      name: 'SLE Risk Predictor - Neural Network',
      model: 'ANN (MLP)',
      status: 'failed',
      error: 'Convergence failure - loss diverged after epoch 34',
      dataset: 'AAM-SLE-E v2.1',
      samples: 1204,
      features: 47,
      hyperparameters: {
        hidden_layers: [128, 64, 32],
        activation: 'relu',
        learning_rate: 0.001
      },
      author: 'Dr. Jennifer Lopez',
      timestamp: '2024-04-07 14:20',
      starred: false,
      tags: ['deep-learning', 'failed'],
      notes: 'Need to adjust learning rate and add regularization'
    },
    {
      id: 'EXP-2024-0082',
      name: 'Feature Selection Experiment - LASSO',
      model: 'Logistic Regression with LASSO',
      status: 'completed',
      accuracy: 84.3,
      f1Score: 83.9,
      precision: 85.1,
      recall: 82.7,
      auc: 0.912,
      runtime: '23m',
      dataset: 'AAM-SLE-E v2.1',
      samples: 1204,
      features: 47,
      selectedFeatures: 23,
      hyperparameters: {
        C: 0.5,
        penalty: 'l1',
        max_iter: 1000
      },
      author: 'Dr. Sarah Chen',
      timestamp: '2024-04-07 10:30',
      starred: false,
      tags: ['feature-selection', 'baseline'],
      notes: 'Reduced features by 51% with only 7% accuracy drop'
    }
  ];

  const filteredExperiments = experiments.filter(exp => {
    const matchesSearch = exp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         exp.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         exp.model.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || exp.status === filterStatus;
    const matchesModel = filterModel === 'all' || exp.model.includes(filterModel);
    return matchesSearch && matchesStatus && matchesModel;
  });

  const statusConfig = {
    completed: { 
      icon: CheckCircle, 
      bg: 'bg-green-dim', 
      text: 'text-green', 
      border: 'border-green/20',
      label: 'Completed'
    },
    running: { 
      icon: Activity, 
      bg: 'bg-amber-dim', 
      text: 'text-amber', 
      border: 'border-amber/20',
      label: 'Running'
    },
    failed: { 
      icon: XCircle, 
      bg: 'bg-red-50', 
      text: 'text-red-600', 
      border: 'border-red-200',
      label: 'Failed'
    }
  };

  const stats = {
    total: experiments.length,
    completed: experiments.filter(e => e.status === 'completed').length,
    running: experiments.filter(e => e.status === 'running').length,
    failed: experiments.filter(e => e.status === 'failed').length,
    avgAccuracy: (experiments.filter(e => e.accuracy).reduce((sum, e) => sum + e.accuracy, 0) / 
                  experiments.filter(e => e.accuracy).length).toFixed(1)
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)', zoom: 0.75 }}>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-syne text-2xl font-bold text-black-text">Experiment Log</h1>
                  <p className="text-xs text-gray-muted">Track and compare all ML experiments</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/40 bg-white/80 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
                <button 
                  onClick={() => navigate('/tuning')}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all text-sm font-medium"
                >
                  <Play className="w-4 h-4" />
                  New Experiment
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-5 gap-4">
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Total Experiments</span>
                  <GitBranch className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">{stats.total}</div>
                <div className="text-xs text-gray-muted mt-1">All time</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Completed</span>
                  <CheckCircle className="w-4 h-4 text-green" />
                </div>
                <div className="font-syne text-2xl font-bold text-green">{stats.completed}</div>
                <div className="text-xs text-gray-muted mt-1">{((stats.completed / stats.total) * 100).toFixed(0)}% success rate</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Running</span>
                  <Activity className="w-4 h-4 text-amber" />
                </div>
                <div className="font-syne text-2xl font-bold text-amber">{stats.running}</div>
                <div className="text-xs text-gray-muted mt-1">In progress</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Avg Accuracy</span>
                  <Award className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-purple-primary">{stats.avgAccuracy}%</div>
                <div className="text-xs text-gray-muted mt-1">Completed only</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Failed</span>
                  <XCircle className="w-4 h-4 text-red-600" />
                </div>
                <div className="font-syne text-2xl font-bold text-red-600">{stats.failed}</div>
                <div className="text-xs text-gray-muted mt-1">Need attention</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Filters */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <div className="grid grid-cols-4 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search experiments..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="running">Running</option>
                  <option value="failed">Failed</option>
                </select>
                <select
                  value={filterModel}
                  onChange={(e) => setFilterModel(e.target.value)}
                  className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary"
                >
                  <option value="all">All Models</option>
                  <option value="Ensemble">Ensemble</option>
                  <option value="XGBoost">XGBoost</option>
                  <option value="Random Forest">Random Forest</option>
                  <option value="LightGBM">LightGBM</option>
                  <option value="ANN">Neural Network</option>
                </select>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary"
                >
                  <option value="7days">Last 7 days</option>
                  <option value="30days">Last 30 days</option>
                  <option value="90days">Last 90 days</option>
                  <option value="all">All time</option>
                </select>
              </div>
            </div>

            {/* Experiment List */}
            <div className="space-y-4">
              {filteredExperiments.map((exp) => {
                const statusData = statusConfig[exp.status];
                const StatusIcon = statusData.icon;
                
                return (
                  <div key={exp.id} className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5 hover:shadow-lg transition-all">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4 flex-1">
                        <div className="w-12 h-12 rounded-lg bg-purple-dim flex items-center justify-center flex-shrink-0">
                          <GitBranch className="w-6 h-6 text-purple-primary" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-syne text-lg font-bold text-black-text">{exp.name}</h3>
                            {exp.starred && <Star className="w-4 h-4 text-amber fill-amber" />}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-muted">
                            <span className="flex items-center gap-1">
                              <Tag className="w-3 h-3" />
                              {exp.id}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <User className="w-3 h-3" />
                              {exp.author}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {exp.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${statusData.bg} ${statusData.text} ${statusData.border}`}>
                          <StatusIcon className="w-3.5 h-3.5" />
                          {statusData.label}
                        </span>
                      </div>
                    </div>

                    {/* Model & Dataset Info */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-purple-dim/30 rounded-lg p-3">
                        <div className="text-xs text-gray-muted mb-1 flex items-center gap-1">
                          <Cpu className="w-3 h-3" />
                          Model Architecture
                        </div>
                        <div className="font-semibold text-sm text-black-text">{exp.model}</div>
                      </div>
                      <div className="bg-purple-dim/30 rounded-lg p-3">
                        <div className="text-xs text-gray-muted mb-1 flex items-center gap-1">
                          <BarChart3 className="w-3 h-3" />
                          Dataset
                        </div>
                        <div className="font-semibold text-sm text-black-text">
                          {exp.dataset} ({exp.samples.toLocaleString()} samples, {exp.features} features)
                        </div>
                      </div>
                    </div>

                    {/* Metrics */}
                    {exp.status === 'completed' && (
                      <div className="grid grid-cols-5 gap-3 mb-4">
                        <div className="bg-gradient-to-br from-green-50 to-green-50/50 border border-green-200 rounded-lg p-3">
                          <div className="text-[10px] text-gray-muted uppercase mb-1">Accuracy</div>
                          <div className="font-syne text-xl font-bold text-green">{exp.accuracy}%</div>
                        </div>
                        <div className="bg-white/60 border border-white/40 rounded-lg p-3">
                          <div className="text-[10px] text-gray-muted uppercase mb-1">F1 Score</div>
                          <div className="font-syne text-xl font-bold text-black-text">{exp.f1Score}%</div>
                        </div>
                        <div className="bg-white/60 border border-white/40 rounded-lg p-3">
                          <div className="text-[10px] text-gray-muted uppercase mb-1">Precision</div>
                          <div className="font-syne text-xl font-bold text-black-text">{exp.precision}%</div>
                        </div>
                        <div className="bg-white/60 border border-white/40 rounded-lg p-3">
                          <div className="text-[10px] text-gray-muted uppercase mb-1">Recall</div>
                          <div className="font-syne text-xl font-bold text-black-text">{exp.recall}%</div>
                        </div>
                        <div className="bg-purple-dim/30 border border-purple-primary/20 rounded-lg p-3">
                          <div className="text-[10px] text-gray-muted uppercase mb-1">AUC</div>
                          <div className="font-syne text-xl font-bold text-purple-primary">{exp.auc}</div>
                        </div>
                      </div>
                    )}

                    {exp.status === 'running' && (
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-amber">Training Progress</span>
                          <span className="text-xs text-gray-muted">{exp.estimatedTime}</span>
                        </div>
                        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber to-amber/80 rounded-full transition-all"
                            style={{ width: `${exp.progress}%` }}
                          />
                        </div>
                        <div className="text-xs text-amber font-semibold mt-1">{exp.progress}% complete</div>
                      </div>
                    )}

                    {exp.status === 'failed' && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                        <div className="flex items-center gap-2 mb-1">
                          <AlertCircle className="w-4 h-4 text-red-600" />
                          <span className="text-xs font-semibold text-red-600 uppercase">Error</span>
                        </div>
                        <p className="text-xs text-red-600">{exp.error}</p>
                      </div>
                    )}

                    {/* Tags & Notes */}
                    <div className="flex items-start justify-between pt-4 border-t border-white/40">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap mb-2">
                          {exp.tags.map((tag, idx) => (
                            <span key={idx} className="px-2 py-1 rounded bg-purple-dim text-purple-primary text-xs font-medium">
                              #{tag}
                            </span>
                          ))}
                        </div>
                        {exp.notes && (
                          <p className="text-xs text-gray-muted italic">{exp.notes}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button className="p-2 rounded-lg border border-white/40 hover:bg-white text-purple-primary hover:border-purple-primary/40 transition-all">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 rounded-lg border border-white/40 hover:bg-white text-purple-primary hover:border-purple-primary/40 transition-all">
                          <Copy className="w-4 h-4" />
                        </button>
                        <button className="p-2 rounded-lg border border-white/40 hover:bg-white text-purple-primary hover:border-purple-primary/40 transition-all">
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
