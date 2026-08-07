/**
 * Batch Prediction Page
 * Deploy trained models for batch inference on new data
 * Author: Syarifah Fajriyah
 * Date: April 12, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Download,
  Brain,
  CheckCircle,
  AlertCircle,
  Clock,
  PlayCircle,
  RefreshCw,
  FileText,
  Target,
  BarChart3,
  Eye,
  ArrowLeft,
  Zap,
  Database
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { mlAPI, authAPI } from '../services/api';

export default function BatchPredictionPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [predictions, setPredictions] = useState(null);
  const [error, setError] = useState(null);

  // Fetch available models and load user
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

  const extractAlgorithm = (modelName) => {
    const parts = modelName.split(' ');
    return parts.slice(0, -1).join(' ') || modelName;
  };

  // Handle file upload
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
        setError('Please upload a CSV or Excel file');
        return;
      }
      setUploadedFile(file);
      setError(null);
    }
  };

  // Run batch prediction
  const runPrediction = async () => {
    if (!selectedModel || !uploadedFile) {
      setError('Please select a model and upload a file');
      return;
    }

    setPredicting(true);
    setError(null);

    try {
      // Call actual API endpoint
      const response = await mlAPI.batchPredict(selectedModel.id, uploadedFile);
      
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
      <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)', zoom: 0.75 }}>
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-purple-primary/20 bg-white/80 text-purple-primary hover:bg-purple-dim transition-colors text-sm font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh Models
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Step 1: Select Model */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-purple-primary text-white flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <h3 className="font-syne text-lg font-bold text-black-text">Select Trained Model</h3>
              </div>

              {models.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-muted mb-4">No trained models available</p>
                  <button
                    onClick={() => navigate('/training')}
                    className="px-6 py-2.5 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all"
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
                          ? 'border-purple-primary bg-purple-50'
                          : 'border-gray-200 bg-white hover:border-purple-primary/40'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm text-black-text mb-1">{model.name}</h4>
                          <p className="text-xs text-gray-muted">{model.algorithm}</p>
                        </div>
                        {selectedModel?.id === model.id && (
                          <CheckCircle className="w-5 h-5 text-purple-primary" />
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-gray-200">
                        <span className="text-gray-600">Accuracy</span>
                        <span className="font-bold text-purple-primary">{model.accuracy}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Step 2: Upload Data */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedModel ? 'bg-purple-primary text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  2
                </div>
                <h3 className="font-syne text-lg font-bold text-black-text">Upload Data File</h3>
              </div>

              <div className={`${!selectedModel ? 'opacity-50 pointer-events-none' : ''}`}>
                <div className="border-2 border-dashed border-purple-primary/30 rounded-xl p-8 text-center hover:border-purple-primary/60 hover:bg-purple-dim/10 transition-all">
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                    disabled={!selectedModel}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="w-12 h-12 text-purple-primary mx-auto mb-3" />
                    <h4 className="font-semibold text-black-text mb-2">
                      {uploadedFile ? uploadedFile.name : 'Drop CSV file here or click to browse'}
                    </h4>
                    <p className="text-sm text-gray-muted">
                      {uploadedFile 
                        ? `File size: ${(uploadedFile.size / 1024).toFixed(2)} KB` 
                        : 'CSV or Excel files only • Must have same schema as training data'}
                    </p>
                  </label>
                </div>

                {uploadedFile && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <div>
                        <div className="font-semibold text-green-900">File Ready</div>
                        <div className="text-sm text-green-700">{uploadedFile.name}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => setUploadedFile(null)}
                      className="text-sm text-red-600 hover:text-red-700 font-medium"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Step 3: Run Prediction */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedModel && uploadedFile ? 'bg-purple-primary text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  3
                </div>
                <h3 className="font-syne text-lg font-bold text-black-text">Run Prediction</h3>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-muted mb-2">
                    {!selectedModel && 'Select a model first'}
                    {selectedModel && !uploadedFile && 'Upload a data file'}
                    {selectedModel && uploadedFile && !predictions && 'Ready to run predictions'}
                    {predictions && `Predicted ${predictions.total_records} records`}
                  </p>
                  {selectedModel && uploadedFile && (
                    <div className="text-xs text-gray-600">
                      Model: <span className="font-semibold">{selectedModel.name}</span> • 
                      File: <span className="font-semibold">{uploadedFile.name}</span>
                    </div>
                  )}
                </div>

                <button
                  onClick={runPrediction}
                  disabled={!selectedModel || !uploadedFile || predicting}
                  className="flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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
                  <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-muted uppercase">Total Records</span>
                      <Database className="w-4 h-4 text-purple-primary" />
                    </div>
                    <div className="font-syne text-2xl font-bold text-black-text">{predictions.total_records}</div>
                  </div>
                  
                  {Object.entries(predictions.summary).map(([label, count]) => (
                    <div key={label} className="bg-white/80 rounded-xl p-4 border border-white/40">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-muted uppercase">{label}</span>
                        <Target className="w-4 h-4 text-purple-primary" />
                      </div>
                      <div className="font-syne text-2xl font-bold text-purple-primary">{count}</div>
                      <div className="text-xs text-gray-muted mt-1">
                        {((count / predictions.total_records) * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>

                {/* Results Table */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="font-syne text-lg font-bold text-black-text">Prediction Results</h3>
                    <button
                      onClick={downloadPredictions}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all text-sm font-medium"
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
