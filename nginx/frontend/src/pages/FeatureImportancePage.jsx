import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Cpu,
  Layers,
  AlertCircle,
  Info,
  Download,
  RefreshCw,
  ChevronRight,
  Zap,
  Shield,
  Activity
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function FeatureImportancePage() {
  const navigate = useNavigate();
  const [selectedModel, setSelectedModel] = useState('ensemble');
  const [selectedDisease, setSelectedDisease] = useState('all');
  const [viewMode, setViewMode] = useState('global'); // 'global' or 'shap'

  // Mock feature importance data
  const featureImportance = [
    { 
      feature: 'Anti-dsDNA Antibodies', 
      importance: 0.234, 
      rank: 1,
      category: 'Antibodies',
      description: 'Double-stranded DNA antibodies, highly specific for SLE',
      correlation: 'positive',
      diseases: ['SLE'],
      trend: 'up',
      change: 3.2
    },
    { 
      feature: 'C3 Complement Level', 
      importance: 0.187, 
      rank: 2,
      category: 'Complement',
      description: 'Low C3 indicates complement consumption in active disease',
      correlation: 'negative',
      diseases: ['SLE', 'Lupus Nephritis'],
      trend: 'stable',
      change: 0.5
    },
    { 
      feature: 'Anti-CCP Antibodies', 
      importance: 0.165, 
      rank: 3,
      category: 'Antibodies',
      description: 'Cyclic citrullinated peptide antibodies, specific for RA',
      correlation: 'positive',
      diseases: ['Rheumatoid Arthritis'],
      trend: 'up',
      change: 2.8
    },
    { 
      feature: 'ESR (Erythrocyte Sedimentation Rate)', 
      importance: 0.142, 
      rank: 4,
      category: 'Inflammation Markers',
      description: 'Non-specific inflammation marker',
      correlation: 'positive',
      diseases: ['RA', 'SLE', 'Vasculitis'],
      trend: 'stable',
      change: -0.3
    },
    { 
      feature: 'C4 Complement Level', 
      importance: 0.128, 
      rank: 5,
      category: 'Complement',
      description: 'Low C4 indicates active autoimmune process',
      correlation: 'negative',
      diseases: ['SLE'],
      trend: 'down',
      change: -1.2
    },
    { 
      feature: 'Anti-SSA/Ro Antibodies', 
      importance: 0.115, 
      rank: 6,
      category: 'Antibodies',
      description: 'Associated with Sjögren syndrome and neonatal lupus',
      correlation: 'positive',
      diseases: ['Sjögren Syndrome', 'SLE'],
      trend: 'up',
      change: 4.1
    },
    { 
      feature: 'Rheumatoid Factor (RF)', 
      importance: 0.098, 
      rank: 7,
      category: 'Antibodies',
      description: 'Present in RA and other connective tissue diseases',
      correlation: 'positive',
      diseases: ['RA', 'Sjögren Syndrome'],
      trend: 'stable',
      change: 0.2
    },
    { 
      feature: 'CRP (C-Reactive Protein)', 
      importance: 0.091, 
      rank: 8,
      category: 'Inflammation Markers',
      description: 'Acute phase reactant indicating inflammation',
      correlation: 'positive',
      diseases: ['RA', 'Vasculitis'],
      trend: 'up',
      change: 1.5
    },
    { 
      feature: 'Anti-Sm Antibodies', 
      importance: 0.074, 
      rank: 9,
      category: 'Antibodies',
      description: 'Highly specific for SLE',
      correlation: 'positive',
      diseases: ['SLE'],
      trend: 'stable',
      change: -0.1
    },
    { 
      feature: 'Platelet Count', 
      importance: 0.067, 
      rank: 10,
      category: 'Hematology',
      description: 'Thrombocytopenia common in active SLE',
      correlation: 'negative',
      diseases: ['SLE', 'Antiphospholipid Syndrome'],
      trend: 'down',
      change: -2.3
    }
  ];

  const modelMetrics = {
    ensemble: { accuracy: 91.8, f1: 91.2, auc: 0.956 },
    randomForest: { accuracy: 89.3, f1: 88.7, auc: 0.942 },
    xgboost: { accuracy: 90.1, f1: 89.5, auc: 0.948 }
  };

  const categoryColors = {
    'Antibodies': { bg: 'bg-purple-dim', text: 'text-purple-primary', dot: 'bg-purple-primary' },
    'Complement': { bg: 'bg-blue-50', text: 'text-blue-600', dot: 'bg-blue-600' },
    'Inflammation Markers': { bg: 'bg-amber-dim', text: 'text-amber', dot: 'bg-amber' },
    'Hematology': { bg: 'bg-green-dim', text: 'text-green', dot: 'bg-green' }
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-syne text-2xl font-bold text-black-text">Feature Importance</h1>
                  <p className="text-xs text-gray-muted">Understand which biomarkers drive classification decisions</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/40 bg-white/80 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <RefreshCw className="w-4 h-4" />
                  Recalculate
                </button>
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all text-sm font-medium">
                  <Download className="w-4 h-4" />
                  Export Report
                </button>
              </div>
            </div>

            {/* Model Selection */}
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(modelMetrics).map(([model, metrics]) => (
                <button
                  key={model}
                  onClick={() => setSelectedModel(model)}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    selectedModel === model
                      ? 'border-purple-primary bg-purple-dim'
                      : 'border-white/40 bg-white/80 hover:border-purple-primary/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-muted uppercase">
                      {model === 'ensemble' ? 'Ensemble Stack' : model === 'randomForest' ? 'Random Forest' : 'XGBoost'}
                    </span>
                    <Layers className={`w-4 h-4 ${selectedModel === model ? 'text-purple-primary' : 'text-gray-muted'}`} />
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-gray-muted">Acc</span>
                      <div className="font-bold text-black-text">{metrics.accuracy}%</div>
                    </div>
                    <div>
                      <span className="text-gray-muted">F1</span>
                      <div className="font-bold text-black-text">{metrics.f1}%</div>
                    </div>
                    <div>
                      <span className="text-gray-muted">AUC</span>
                      <div className="font-bold text-black-text">{metrics.auc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* View Mode Selector */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-syne text-base font-bold text-black-text">Analysis Method</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setViewMode('global')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      viewMode === 'global'
                        ? 'bg-purple-primary text-white'
                        : 'bg-white/80 text-gray-muted hover:text-black-text'
                    }`}
                  >
                    Global Importance
                  </button>
                  <button
                    onClick={() => setViewMode('shap')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      viewMode === 'shap'
                        ? 'bg-purple-primary text-white'
                        : 'bg-white/80 text-gray-muted hover:text-black-text'
                    }`}
                  >
                    SHAP Values
                  </button>
                </div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
                <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-blue-600">
                  <span className="font-semibold">Global Importance:</span> Shows average impact of each feature across all predictions.{' '}
                  <span className="font-semibold">SHAP Values:</span> Explains individual prediction contributions with directional impact.
                </p>
              </div>
            </div>

            {/* Top Features Summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-purple-50 to-purple-50/50 border border-purple-200 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-purple-primary uppercase">Most Important</span>
                  <Target className="w-5 h-5 text-purple-primary" />
                </div>
                <div className="font-syne text-xl font-bold text-purple-primary mb-1">Anti-dsDNA</div>
                <div className="text-xs text-gray-muted">23.4% contribution to model decisions</div>
                <div className="mt-3 flex items-center gap-1 text-xs text-green">
                  <TrendingUp className="w-3 h-3" />
                  <span className="font-semibold">+3.2%</span>
                  <span className="text-gray-muted">vs last month</span>
                </div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-50/50 border border-green-200 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-green uppercase">Fastest Rising</span>
                  <Zap className="w-5 h-5 text-green" />
                </div>
                <div className="font-syne text-xl font-bold text-green mb-1">Anti-SSA/Ro</div>
                <div className="text-xs text-gray-muted">11.5% importance, rapid increase</div>
                <div className="mt-3 flex items-center gap-1 text-xs text-green">
                  <TrendingUp className="w-3 h-3" />
                  <span className="font-semibold">+4.1%</span>
                  <span className="text-gray-muted">trending up</span>
                </div>
              </div>
              <div className="bg-gradient-to-br from-amber-50 to-amber-50/50 border border-amber-200 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-amber uppercase">Declining</span>
                  <TrendingDown className="w-5 h-5 text-amber" />
                </div>
                <div className="font-syne text-xl font-bold text-amber mb-1">Platelet Count</div>
                <div className="text-xs text-gray-muted">6.7% importance, decreasing</div>
                <div className="mt-3 flex items-center gap-1 text-xs text-red-600">
                  <TrendingDown className="w-3 h-3" />
                  <span className="font-semibold">-2.3%</span>
                  <span className="text-gray-muted">vs last month</span>
                </div>
              </div>
            </div>

            {/* Feature Importance List */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                <div className="flex items-center justify-between">
                  <h3 className="font-syne text-base font-bold text-black-text">Feature Rankings</h3>
                  <select
                    value={selectedDisease}
                    onChange={(e) => setSelectedDisease(e.target.value)}
                    className="px-3 py-1.5 rounded-lg border border-white/40 bg-white/90 text-xs focus:outline-none focus:border-purple-primary"
                  >
                    <option value="all">All Diseases</option>
                    <option value="sle">SLE</option>
                    <option value="ra">Rheumatoid Arthritis</option>
                    <option value="sjogren">Sjögren Syndrome</option>
                  </select>
                </div>
              </div>

              <div className="p-5 space-y-4">
                {featureImportance.map((feature, idx) => {
                  const categoryStyle = categoryColors[feature.category];
                  const widthPercentage = (feature.importance * 100).toFixed(1);
                  
                  return (
                    <div key={idx} className="group">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3 flex-1">
                          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-dim">
                            <span className="text-xs font-bold text-purple-primary">#{feature.rank}</span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-sm text-black-text">{feature.feature}</h4>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${categoryStyle.bg} ${categoryStyle.text}`}>
                                {feature.category}
                              </span>
                            </div>
                            <p className="text-xs text-gray-muted">{feature.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="font-syne text-lg font-bold text-purple-primary">{(feature.importance * 100).toFixed(1)}%</div>
                            <div className="flex items-center gap-1 text-xs">
                              {feature.trend === 'up' && (
                                <>
                                  <TrendingUp className="w-3 h-3 text-green" />
                                  <span className="text-green font-semibold">+{feature.change}%</span>
                                </>
                              )}
                              {feature.trend === 'down' && (
                                <>
                                  <TrendingDown className="w-3 h-3 text-red-600" />
                                  <span className="text-red-600 font-semibold">{feature.change}%</span>
                                </>
                              )}
                              {feature.trend === 'stable' && (
                                <span className="text-gray-muted">Stable</span>
                              )}
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-muted group-hover:text-purple-primary transition-colors" />
                        </div>
                      </div>
                      
                      {/* Importance Bar */}
                      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div
                          className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-primary to-purple-primary/80 rounded-full transition-all duration-500"
                          style={{ width: `${widthPercentage}%` }}
                        />
                      </div>

                      {/* Associated Diseases */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-muted">Associated with:</span>
                        {feature.diseases.map((disease, dIdx) => (
                          <span key={dIdx} className="px-2 py-0.5 rounded bg-white border border-white/40 text-gray-muted">
                            {disease}
                          </span>
                        ))}
                        <span className={`ml-2 px-2 py-0.5 rounded font-medium ${
                          feature.correlation === 'positive' 
                            ? 'bg-green-dim text-green' 
                            : 'bg-blue-50 text-blue-600'
                        }`}>
                          {feature.correlation === 'positive' ? '↑ Positive' : '↓ Negative'} Correlation
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
