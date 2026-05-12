/**
 * Batch Prediction Page
 * Deploy trained models for batch inference on new data
 * Author: Syarifah Fajriyah
 * Date: April 12, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  Brain,
  CheckCircle,
  AlertCircle,
  PlayCircle,
  RefreshCw,
  Target,
  BarChart3,
  Zap,
  Database,
  Layers
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { mlAPI, authAPI } from '../services/api';

export default function BatchPredictionPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [predictions, setPredictions] = useState(null);
  const [error, setError] = useState(null);

  // Fetch available models, datasets and load user
  useEffect(() => {
    fetchModels();
    fetchDatasets();
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

  const fetchModels = async () => {
    try {
      const data = await mlAPI.getModels();
      const availableModels = (data.models || []).map(model => ({
        id: model.model_id,
        name: model.model_name,
        algorithm: model.algorithm || extractAlgorithm(model.model_name),
        accuracy: (model.accuracy * 100).toFixed(2),
        modelType: model.model_type,
        trainedDate: model.trained_at ? new Date(model.trained_at).toLocaleDateString() : 'N/A'
      }));
      setModels(availableModels);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to fetch models');
    }
  };

  const fetchDatasets = async () => {
    try {
      const data = await mlAPI.listDatasets(50, 0);
      setDatasets(data.datasets || []);
    } catch (err) {
      console.error('Error fetching datasets:', err);
    }
  };

  const extractAlgorithm = (modelName) => {
    const parts = modelName.split(' ');
    return parts.slice(0, -1).join(' ') || modelName;
  };

  // Run batch prediction
  const runPrediction = async () => {
    if (!selectedModel || !selectedDatasetId) {
      setError('Please select a model and a dataset');
      return;
    }

    setPredicting(true);
    setError(null);

    try {
      // Call actual API endpoint using dataset_id
      const response = await mlAPI.batchPredictByDataset(selectedModel.id, selectedDatasetId);
      
      // Transform response to match expected format
      const predictionResults = {
        total_records: response.total_predictions || response.predictions?.length || 0,
        predictions: (response.predictions || []).map((pred, i) => ({
          record_id: pred.record_id || i + 1,
          prediction: pred.predicted_class || pred.prediction || 'Unknown',
          confidence: ((pred.confidence || pred.probability || 0.5) * 100).toFixed(2),
          probabilities: pred.probabilities || pred.class_probabilities || {}
        })),
        summary: response.summary || {},
        processing_time: response.processing_time || 0
      };
      
      // Calculate summary if not provided
      if (Object.keys(predictionResults.summary).length === 0) {
        predictionResults.predictions.forEach(pred => {
          predictionResults.summary[pred.prediction] = (predictionResults.summary[pred.prediction] || 0) + 1;
        });
      }
      
      setPredictions(predictionResults);
      setPredicting(false);
    } catch (err) {
      console.error('Error running predictions:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run predictions');
      setPredicting(false);
    }
  };

  // Download predictions as CSV
  const downloadPredictions = () => {
    if (!predictions) return;

    const csv = [
      ['Record ID', 'Prediction', 'Confidence (%)', ...Object.keys(predictions.predictions[0].probabilities).map(k => `Prob_${k}`)].join(','),
      ...predictions.predictions.map(pred => 
        [
          pred.record_id,
          pred.prediction,
          pred.confidence,
          ...Object.values(pred.probabilities)
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_${selectedModel.name}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <DashboardLayout>
      <PageHeader title="Batch Prediction" subtitle="Predictions" user={user} />
      <div className="flex-1 overflow-y-auto p-6" style={{ background: '#FAFBFC', zoom: 0.78 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Top Actions */}
          <div className="flex justify-end">
            <button
              onClick={() => { fetchModels(); fetchDatasets(); }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Content */}
          <div className="space-y-5">
            {/* Step 1: Select Model */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold text-sm">1</div>
                <h3 className="font-semibold text-base text-gray-800">Select Trained Model</h3>
              </div>

              {models.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-4">No trained models available</p>
                  <button
                    onClick={() => navigate('/training')}
                    className="px-6 py-2.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
                  >
                    Train Models
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-4">
                  {models.map((model) => (
                    <div
                      key={model.id}
                      onClick={() => setSelectedModel(model)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedModel?.id === model.id
                          ? 'border-purple-600 bg-purple-50'
                          : 'border-gray-200 bg-white hover:border-purple-300'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm text-gray-900 mb-1">{model.name}</h4>
                          <p className="text-xs text-gray-500">{model.algorithm}</p>
                        </div>
                        {selectedModel?.id === model.id && (
                          <CheckCircle className="w-5 h-5 text-purple-600" />
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-gray-100">
                        <span className="text-gray-600">Accuracy</span>
                        <span className="font-bold text-purple-600">{model.accuracy}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Step 2: Select Dataset */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedModel ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>2</div>
                <h3 className="font-semibold text-base text-gray-800">Select Dataset</h3>
              </div>
              <div className={`${!selectedModel ? 'opacity-50 pointer-events-none' : ''}`}>
                {datasets.length === 0 ? (
                  <div className="text-center py-6 border border-dashed border-gray-200 rounded-lg">
                    <Layers className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No datasets available in the system</p>
                    <button
                      onClick={() => navigate('/data-preparation')}
                      className="mt-3 text-sm text-purple-600 hover:text-purple-700 font-medium"
                    >
                      Go to Data Preparation
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-3">
                    {datasets.slice(0, 9).map((ds) => (
                      <div
                        key={ds.id || ds.dataset_id}
                        onClick={() => setSelectedDatasetId(ds.id || ds.dataset_id)}
                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          selectedDatasetId === (ds.id || ds.dataset_id)
                            ? 'border-purple-600 bg-purple-50'
                            : 'border-gray-200 bg-white hover:border-purple-300'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <Database className="w-4 h-4 text-purple-400 mt-0.5" />
                          {selectedDatasetId === (ds.id || ds.dataset_id) && (
                            <CheckCircle className="w-4 h-4 text-purple-600" />
                          )}
                        </div>
                        <p className="font-medium text-sm text-gray-900 mt-2 truncate">{ds.name || ds.dataset_name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{ds.row_count ? `${ds.row_count.toLocaleString()} rows` : 'Dataset'}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Step 3: Run Prediction */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedModel && selectedDatasetId ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>3</div>
                <h3 className="font-semibold text-base text-gray-800">Run Prediction</h3>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-2">
                    {!selectedModel && 'Select a model first'}
                    {selectedModel && !selectedDatasetId && 'Select a dataset'}
                    {selectedModel && selectedDatasetId && !predictions && 'Ready to run predictions'}
                    {predictions && `Predicted ${predictions.total_records} records`}
                  </p>
                  {selectedModel && selectedDatasetId && (
                    <div className="text-xs text-gray-600">
                      Model: <span className="font-semibold">{selectedModel.name}</span>
                    </div>
                  )}
                </div>

                <button
                  onClick={runPrediction}
                  disabled={!selectedModel || !selectedDatasetId || predicting}
                  className="flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {predicting ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Predicting...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="w-5 h-5" />
                      Run Prediction
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Prediction Results */}
            {predictions && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-500 uppercase">Total Records</span>
                      <Database className="w-4 h-4 text-purple-600" />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{predictions.total_records}</div>
                  </div>
                  
                  {Object.entries(predictions.summary).map(([label, count]) => (
                    <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-500 uppercase">{label}</span>
                        <Target className="w-4 h-4 text-purple-600" />
                      </div>
                      <div className="text-2xl font-bold text-purple-600">{count}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {((count / predictions.total_records) * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>

                {/* Results Table */}
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="font-syne text-lg font-bold text-black-text">Prediction Results</h3>
                    <button
                      onClick={downloadPredictions}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors text-sm font-medium"
                    >
                      <Download className="w-4 h-4" />
                      Download CSV
                    </button>
                  </div>

                  <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Record</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Prediction</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Confidence</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Probabilities</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {predictions.predictions.map((pred) => (
                          <tr key={pred.record_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm text-gray-900">#{pred.record_id}</td>
                            <td className="px-6 py-4">
                              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-50 text-purple-700">
                                {pred.prediction}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-green-500 rounded-full"
                                    style={{ width: `${pred.confidence}%` }}
                                  />
                                </div>
                                <span className="text-sm font-semibold text-gray-700 w-12">
                                  {pred.confidence}%
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex gap-2 text-xs">
                                {Object.entries(pred.probabilities).map(([label, prob]) => (
                                  <span key={label} className="text-gray-600">
                                    {label}: <span className="font-semibold">{prob}%</span>
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
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
