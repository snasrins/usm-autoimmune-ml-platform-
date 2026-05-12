/**
 * Model Comparison Page
 * Compare multiple trained models side-by-side
 * Author: Syarifah Fajriyah
 * Date: April 12, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  CheckCircle,
  XCircle,
  Download,
  Eye,
  Sparkles,
  ArrowLeft,
  RefreshCw,
  Target,
  Zap,
  Brain,
  AlertCircle,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { trainingAPI } from '../services/api-complete';
import { authAPI } from '../services/api';

export default function ModelComparisonPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  const [models, setModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bestModelId, setBestModelId] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [chartType, setChartType] = useState('bar'); // 'bar', 'radar', 'line'
  const modelsPerPage = 4;

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
  
  // Load trained model IDs from sessionStorage (from training workflow)
  useEffect(() => {
    const savedModelIds = sessionStorage.getItem('trained_model_ids');
    if (savedModelIds) {
      try {
        const modelIds = JSON.parse(savedModelIds);
        console.log('[Comparison] Loaded model IDs from session:', modelIds);
        setSelectedModels(modelIds.slice(0, 4)); // Auto-select up to 4 models
      } catch (err) {
        console.error('[Comparison] Error parsing model IDs:', err);
      }
    }
  }, []);

  // Fetch all trained models
  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      console.log('[Comparison] Fetching trained models...');
      const data = await trainingAPI.getModels();
      console.log('[Comparison] Got models:', data.models?.length || 0);
      
      // Filter only base learners for comparison
      const baseLearners = (data.models || [])
        .filter(m => m.model_type === 'base_model' || !m.model_type)
        .map(model => ({
          id: model.model_id,
          name: model.model_name || model.algorithm,
          algorithm: model.algorithm || extractAlgorithm(model.model_name),
          // Use test_auc if available, otherwise oof_auc
          auc: model.test_auc ? (model.test_auc * 100).toFixed(2) : 
               model.oof_auc ? (model.oof_auc * 100).toFixed(2) : 'N/A',
          oof_auc: model.oof_auc ? (model.oof_auc * 100).toFixed(2) : 'N/A',
          test_auc: model.test_auc ? (model.test_auc * 100).toFixed(2) : 'N/A',
          accuracy: model.test_auc ? (model.test_auc * 100).toFixed(2) : 
                    model.oof_auc ? (model.oof_auc * 100).toFixed(2) : 'N/A',
          precision: 'N/A', // Not in list endpoint
          recall: 'N/A',
          f1Score: 'N/A',
          trainedDate: model.trained_at ? new Date(model.trained_at).toLocaleDateString() : 'N/A',
          features: model.feature_count || 0
        }));
      
      console.log('[Comparison] Processed models:', baseLearners.length);
      setModels(baseLearners);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to fetch models: ' + err.message);
    }
  };

  const extractAlgorithm = (modelName) => {
    const parts = modelName.split(' ');
    return parts.slice(0, -1).join(' ') || modelName;
  };

  // Toggle model selection (NO LIMIT)
  const toggleModelSelection = (modelId) => {
    if (selectedModels.includes(modelId)) {
      setSelectedModels(selectedModels.filter(id => id !== modelId));
    } else {
      setSelectedModels([...selectedModels, modelId]);
    }
  };

  // Run comparison
  const runComparison = async () => {
    if (selectedModels.length < 2) {
      alert('Select at least 2 models to compare');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[Comparison] Comparing models:', selectedModels);
      const data = await trainingAPI.compareModels(selectedModels);
      console.log('[Comparison] Comparison result:', data);
      setComparisonData(data);
      
      // Automatically select best model by F1 score
      if (data.best_by_metric?.f1_score) {
        setBestModelId(data.best_by_metric.f1_score);
        console.log('[Comparison] Best model by F1:', data.best_by_metric.f1_score);
      }
    } catch (err) {
      console.error('Error comparing models:', err);
      setError(err.message || 'Failed to compare models');
    } finally {
      setLoading(false);
    }
  };

  // Navigate to scorecard with selected model
  const proceedToScorecard = () => {
    if (!bestModelId) {
      alert('Please select a model for scorecard generation');
      return;
    }
    
    sessionStorage.setItem('selected_model_id', bestModelId);
    sessionStorage.setItem('workflow_stage', 'scorecard');
    console.log('[Comparison] Proceeding to scorecard with model:', bestModelId);
    navigate('/scorecard');
  };

  // Get selected model objects
  const selectedModelObjects = models.filter(m => selectedModels.includes(m.id));

  // Pagination for viewing models
  const totalPages = Math.ceil(selectedModelObjects.length / modelsPerPage);
  const startIdx = currentPage * modelsPerPage;
  const endIdx = startIdx + modelsPerPage;
  const visibleModels = selectedModelObjects.slice(startIdx, endIdx);

  // Find best model for each metric
  const getBestModelForMetric = (metric) => {
    if (!selectedModelObjects.length) return null;
    return selectedModelObjects.reduce((best, model) => 
      parseFloat(model[metric]) > parseFloat(best[metric]) ? model : best
    );
  };
  
  // Prepare data for recharts
  const prepareChartData = () => {
    const metrics = ['accuracy', 'precision', 'recall', 'f1Score', 'auc'];
    return metrics.map(metric => {
      const dataPoint = {
        metric: metric === 'f1Score' ? 'F1 Score' : 
                metric === 'auc' ? 'AUC-ROC' :
                metric.charAt(0).toUpperCase() + metric.slice(1)
      };
      
      visibleModels.forEach(model => {
        const value = parseFloat(model[metric]);
        dataPoint[model.name] = isNaN(value) ? 0 : value;
      });
      
      return dataPoint;
    });
  };
  
  // Prepare data for radar chart
  const prepareRadarData = () => {
    const metrics = ['accuracy', 'precision', 'recall', 'f1Score'];
    return metrics.map(metric => {
      const dataPoint = {
        metric: metric === 'f1Score' ? 'F1' : metric.charAt(0).toUpperCase() + metric.slice(1),
        fullMark: 100
      };
      
      visibleModels.forEach(model => {
        const value = parseFloat(model[metric]);
        dataPoint[model.name] = isNaN(value) ? 0 : value;
      });
      
      return dataPoint;
    });
  };
  
  const chartData = prepareChartData();
  const radarData = prepareRadarData();

  // Colors for different models
  const colors = [
    '#8B5CF6', // purple
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // amber
    '#EF4444', // red
    '#EC4899', // pink
    '#6366F1', // indigo
    '#14B8A6'  // teal
  ];

  return (
    <DashboardLayout>
      <PageHeader title="Model Comparison" subtitle="Comparison" user={user} />
      <div className="min-h-screen p-6" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)', zoom: 0.75 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Top Actions Bar */}
          <div className="flex items-center justify-between">
            <button
              onClick={fetchModels}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-purple-primary/20 bg-white/80 text-purple-primary hover:bg-purple-dim transition-colors text-sm font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={runComparison}
              disabled={selectedModels.length < 2 || loading}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Comparing...
                </>
              ) : (
                <>
                  <BarChart3 className="w-4 h-4" />
                  Compare Selected ({selectedModels.length})
                </>
              )}
            </button>
          </div>

          {/* Selection Info */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-primary" />
                <span className="text-sm font-medium text-purple-primary">
                  {selectedModels.length === 0 && 'Select at least 2 models to compare (unlimited)'}
                  {selectedModels.length === 1 && 'Select at least 1 more model'}
                  {selectedModels.length >= 2 && `${selectedModels.length} models selected - Ready to compare!`}
                </span>
              </div>
              {selectedModels.length > 0 && (
                <button
                  onClick={() => setSelectedModels([])}
                  className="text-sm text-purple-primary hover:text-purple-primary/80 font-medium"
                >
                  Clear Selection
                </button>
              )}
            </div>

            {/* Model Selection Grid */}
            {!comparisonData && (
              <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                <h3 className="font-syne text-lg font-bold text-black-text mb-4">
                  Select Models to Compare (No Limit - View 4 at a time)
                </h3>
                
                {models.length === 0 ? (
                  <div className="text-center py-12">
                    <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-muted">No trained models available</p>
                    <button
                      onClick={() => navigate('/training')}
                      className="mt-4 px-6 py-2.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all"
                    >
                      Train Models
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    {models.map((model) => {
                      const isSelected = selectedModels.includes(model.id);
                      return (
                        <div
                          key={model.id}
                          onClick={() => toggleModelSelection(model.id)}
                          className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                            isSelected
                              ? 'border-purple-primary bg-purple-50'
                              : 'border-gray-200 bg-white hover:border-purple-primary/40'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-black-text mb-1">{model.name}</h4>
                              <p className="text-xs text-gray-muted">{model.algorithm}</p>
                            </div>
                            {isSelected && (
                              <CheckCircle className="w-5 h-5 text-purple-primary flex-shrink-0" />
                            )}
                          </div>

                          <div className="grid grid-cols-4 gap-2">
                            <div className="text-center">
                              <div className="text-xs text-gray-muted">Accuracy</div>
                              <div className="font-bold text-sm text-purple-primary">{model.accuracy}%</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-muted">Precision</div>
                              <div className="font-bold text-sm">{model.precision}%</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-muted">Recall</div>
                              <div className="font-bold text-sm">{model.recall}%</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-muted">F1</div>
                              <div className="font-bold text-sm">{model.f1Score}%</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Comparison Results */}
            {comparisonData && selectedModelObjects.length > 0 && (
              <>
                {/* Back to Selection */}
                <div className="flex items-center justify-between">
                  <h2 className="font-syne text-xl font-bold text-black-text">
                    Comparison Results ({selectedModelObjects.length} models)
                  </h2>
                  <button
                    onClick={() => {
                      setComparisonData(null);
                      setCurrentPage(0);
                    }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm font-medium"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Selection
                  </button>
                </div>

                {/* Chart Type Selector */}
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">Chart Type:</span>
                  <div className="flex gap-1 bg-white rounded-lg border border-gray-200 p-1">
                    <button
                      onClick={() => setChartType('bar')}
                      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                        chartType === 'bar' 
                          ? 'bg-purple-primary text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Bar Chart
                    </button>
                    <button
                      onClick={() => setChartType('radar')}
                      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                        chartType === 'radar' 
                          ? 'bg-purple-primary text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Radar Chart
                    </button>
                    <button
                      onClick={() => setChartType('line')}
                      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                        chartType === 'line' 
                          ? 'bg-purple-primary text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Line Chart
                    </button>
                  </div>
                </div>

                {/* Pagination Controls for Viewing Models */}
                {selectedModelObjects.length > modelsPerPage && (
                  <div className="bg-white/80 backdrop-blur-sm border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Viewing models {startIdx + 1}-{Math.min(endIdx, selectedModelObjects.length)} of {selectedModelObjects.length}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                          disabled={currentPage === 0}
                          className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-sm font-medium px-3">
                          Page {currentPage + 1} of {totalPages}
                        </span>
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                          disabled={currentPage === totalPages - 1}
                          className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Chart Visualization */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <h3 className="font-syne text-lg font-bold text-black-text mb-4">
                    Performance Comparison - {chartType === 'bar' ? 'Bar Chart' : chartType === 'radar' ? 'Radar Chart' : 'Line Chart'}
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    {chartType === 'bar' ? (
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="metric" />
                        <YAxis domain={[0, 100]} />
                        <RechartsTooltip />
                        <Legend />
                        {visibleModels.map((model, idx) => (
                          <Bar 
                            key={model.id} 
                            dataKey={model.name} 
                            fill={colors[idx % colors.length]} 
                          />
                        ))}
                      </BarChart>
                    ) : chartType === 'radar' ? (
                      <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <RechartsTooltip />
                        <Legend />
                        {visibleModels.map((model, idx) => (
                          <Radar
                            key={model.id}
                            name={model.name}
                            dataKey={model.name}
                            stroke={colors[idx % colors.length]}
                            fill={colors[idx % colors.length]}
                            fillOpacity={0.3}
                          />
                        ))}
                      </RadarChart>
                    ) : (
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="metric" />
                        <YAxis domain={[0, 100]} />
                        <RechartsTooltip />
                        <Legend />
                        {visibleModels.map((model, idx) => (
                          <Line
                            key={model.id}
                            type="monotone"
                            dataKey={model.name}
                            stroke={colors[idx % colors.length]}
                            strokeWidth={2}
                            dot={{ r: 4 }}
                          />
                        ))}
                      </LineChart>
                    )}
                  </ResponsiveContainer>
                </div>

                {/* Metrics Comparison Table */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-200">
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Metric</th>
                          {visibleModels.map((model) => (
                            <th key={model.id} className="px-6 py-4 text-center text-sm font-semibold text-gray-700">
                              <div className="mb-1">{model.name}</div>
                              <div className="text-xs font-normal text-gray-500">{model.algorithm}</div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {['accuracy', 'precision', 'recall', 'f1Score', 'auc'].map((metric) => {
                          const bestModel = getBestModelForMetric(metric);
                          const metricLabel = metric === 'f1Score' ? 'F1 Score' : 
                                            metric === 'auc' ? 'AUC-ROC' :
                                            metric.charAt(0).toUpperCase() + metric.slice(1);
                          
                          return (
                            <tr key={metric} className="hover:bg-gray-50">
                              <td className="px-6 py-4 font-medium text-gray-900">{metricLabel}</td>
                              {visibleModels.map((model) => {
                                const isBest = bestModel && model.id === bestModel.id;
                                const value = model[metric];
                                
                                return (
                                  <td key={model.id} className="px-6 py-4 text-center">
                                    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                                      isBest 
                                        ? 'bg-green-50 border border-green-200' 
                                        : 'bg-gray-50'
                                    }`}>
                                      <span className={`font-bold ${
                                        isBest ? 'text-green-700' : 'text-gray-700'
                                      }`}>
                                        {value}{metric !== 'auc' && '%'}
                                      </span>
                                      {isBest && <CheckCircle className="w-4 h-4 text-green-600" />}
                                    </div>
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

                {/* Winner Summary */}
                <div className="bg-gradient-to-br from-purple-50 to-purple-50/50 border border-purple-200 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Sparkles className="w-6 h-6 text-purple-primary" />
                    <h3 className="font-syne text-lg font-bold text-purple-primary">Best Performing Models</h3>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    {['accuracy', 'f1Score'].map((metric) => {
                      const bestModel = getBestModelForMetric(metric);
                      const metricLabel = metric === 'f1Score' ? 'F1 Score' : 'Accuracy';
                      
                      return bestModel ? (
                        <div key={metric} className="bg-white rounded-lg p-4 border border-purple-100">
                          <div className="text-sm text-gray-600 mb-1">Best {metricLabel}</div>
                          <div className="font-bold text-lg text-purple-primary mb-1">{bestModel.name}</div>
                          <div className="text-2xl font-syne font-bold text-black-text">
                            {bestModel[metric]}%
                          </div>
                        </div>
                      ) : null;
                    })}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setComparisonData(null);
                      setCurrentPage(0);
                    }}
                    className="flex-1 px-6 py-3 rounded-lg border-2 border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                  >
                    <ArrowLeft className="w-5 h-5 inline mr-2" />
                    Back to Selection
                  </button>
                  <button
                    onClick={proceedToScorecard}
                    disabled={!bestModelId}
                    className="flex-1 px-6 py-3 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Sparkles className="w-5 h-5 inline mr-2" />
                    Generate Scorecard (Best Model)
                  </button>
                </div>
              </>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-red-900">Error</div>
                  <div className="text-sm text-red-700">{error}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
