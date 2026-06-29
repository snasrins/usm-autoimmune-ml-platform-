import { useState, useEffect } from 'react';
import { ChevronRight, Brain, Sparkles, Info, RefreshCw, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import ModelingStepsNav from '../components/ModelingStepsNav';
import PageHeader from '../components/PageHeader';
import { explainabilityAPI } from '../services/api-complete';
import { authAPI } from '../services/api';
import api from '../services/api';

export default function ModelExplainabilityPageConnected() {
  const [user, setUser] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedModelFeatures, setSelectedModelFeatures] = useState([]);
  const [tab, setTab] = useState('single');
  const [patientData, setPatientData] = useState({});
  const [analyzing, setAnalyzing] = useState(false);
  const [shapResult, setShapResult] = useState(null);
  const [aiExplanation, setAiExplanation] = useState('');
  const [error, setError] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [userMessage, setUserMessage] = useState('');

  // Load available models and user on mount
  useEffect(() => {
    loadModels();
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

  const loadModels = async () => {
    try {
      const response = await api.get('/ml/models/list');
      const data = response.data;
      const modelList = (data.models || []).map(m => {
        const aucStr = m.test_auc ? ` — AUC ${(m.test_auc * 100).toFixed(1)}%` : '';
        const typeTag = m.model_type === 'ensemble' ? '🔵 Ensemble' : '⚙️ Base';
        return {
          id: m.model_id,
          name: `${m.model_name} (${typeTag}${aucStr})`,
          type: m.model_name,
          version: m.version,
          model_type: m.model_type,
          feature_names: m.feature_names || [],
        };
      });
      if (modelList.length === 0) {
        setError('No trained models found. Complete training first.');
        return;
      }
      setModels(modelList);
      setSelectedModel(modelList[0].id);
      // Auto-populate feature template for first model
      if (modelList[0].feature_names?.length > 0) {
        const template = Object.fromEntries(modelList[0].feature_names.map(f => [f, 0]));
        setPatientData(template);
        setSelectedModelFeatures(modelList[0].feature_names);
      }
    } catch (err) {
      console.error('Error loading models:', err);
      setError('Failed to load trained models. ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAnalyzeSHAP = async () => {
    if (!selectedModel || Object.keys(patientData).length === 0) {
      setError('Please select a model and provide patient data');
      return;
    }

    setAnalyzing(true);
    setError(null);

    try {
      // Use job-id based SHAP endpoint with the real model artifact path
      const result = await explainabilityAPI.getSHAPByJobId(
        selectedModel,
        patientData,
        10 // top_k features
      );

      setShapResult(result);

      // Also get AI explanation
      await generateAIExplanation(result);
      
      setAnalyzing(false);
    } catch (err) {
      console.error('Error generating SHAP explanation:', err);
      setError('Failed to generate explanation: ' + (err.response?.data?.detail || err.message));
      setAnalyzing(false);
    }
  };

  const generateAIExplanation = async (shapData) => {
    try {
      const model = models.find(m => m.id === selectedModel);
      const response = await explainabilityAPI.generateLLMExplanation(
        model.type,
        patientData,
        'detailed'
      );
      setAiExplanation(response.explanation);
    } catch (err) {
      console.error('Error generating AI explanation:', err);
      setAiExplanation('AI explanation unavailable. SHAP values are shown in the visualization.');
    }
  };

  const handleChatWithDrMyra = async () => {
    if (!userMessage.trim()) return;

    const newMessages = [...chatMessages, { role: 'user', content: userMessage }];
    setChatMessages(newMessages);
    setUserMessage('');

    try {
      const context = shapResult ? {
        prediction: {
          predicted_class: shapResult.predicted_class,
          base_value: shapResult.base_value
        },
        shap: shapResult
      } : null;

      const response = await explainabilityAPI.chatWithDrMyra(userMessage, context);
      
      setChatMessages([...newMessages, { role: 'assistant', content: response.response }]);
    } catch (err) {
      console.error('Error chatting with Dr. Myra:', err);
      setChatMessages([
        ...newMessages,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    }
  };

  return (
    <DashboardLayout>
      <PageHeader title="Model Explainability" subtitle="Explainability (SHAP + AI)" user={user} />
      <ModelingStepsNav />

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#f5f3ff] via-[#faf9fc] to-[#f0edff]" style={{ zoom: 0.9 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Error Display */}
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Model & Data Input */}
          <section className="rounded-2xl border border-violet-100 bg-white p-5">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Step 1: Select Model & Patient Data</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-semibold text-gray-700">Select Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => {
                    setSelectedModel(e.target.value);
                    const m = models.find(x => x.id === e.target.value);
                    if (m?.feature_names?.length > 0) {
                      const template = Object.fromEntries(m.feature_names.map(f => [f, 0]));
                      setPatientData(template);
                      setSelectedModelFeatures(m.feature_names);
                    }
                  }}
                  className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  {models.map(model => (
                    <option key={model.id} value={model.id}>{model.name}</option>
                  ))}
                </select>
                {selectedModelFeatures.length > 0 && (
                  <p className="text-xs text-violet-600 mt-1">
                    ✓ {selectedModelFeatures.length} features loaded — edit values below
                  </p>
                )}
              </div>

              <div>
                <label className="text-sm font-semibold text-gray-700">Patient Data Source</label>
                <div className="mt-2 space-y-1 text-sm">
                  <label className="flex items-center gap-2">
                    <input type="radio" name="dataSource" defaultChecked />
                    Manual Entry
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="dataSource" />
                    Load from Dataset
                  </label>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <label className="text-sm font-semibold text-gray-700">Patient Features (JSON)</label>
              <textarea
                value={JSON.stringify(patientData, null, 2)}
                onChange={(e) => {
                  try {
                    setPatientData(JSON.parse(e.target.value));
                    setError(null);
                  } catch (err) {
                    setError('Invalid JSON format');
                  }
                }}
                className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono h-40"
                placeholder={`{
  "demographics_age": 35,
  "lab_results_CRP": 1.5,
  "lab_results_ESR": 45,
  "lab_results_C3": 0.45,
  "lab_results_C4": 0.08,
  "disease_activity_SLEDAI_score": 8
}`}
              />
              <p className="text-xs text-gray-500 mt-1">
                {selectedModelFeatures.length > 0
                  ? `Feature names are auto-loaded from the model. Replace the 0 values with real patient measurements.`
                  : `Enter patient feature values as JSON. Feature names must match training data columns.`}
              </p>
            </div>

            <button
              onClick={handleAnalyzeSHAP}
              disabled={analyzing}
              className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-semibold shadow-lg hover:from-violet-700 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              <Brain className="w-4 h-4" />
              {analyzing ? 'Analyzing...' : 'Generate SHAP Explanation'}
            </button>
          </section>

          {/* Results Tabs */}
          {shapResult && (
            <section className="rounded-2xl border border-violet-100 bg-white overflow-hidden">
              <div className="flex border-b border-violet-100">
                {[
                  { id: 'single', label: 'SHAP Values' },
                  { id: 'llm', label: 'AI Explanation (Gemma)' },
                  { id: 'chat', label: 'Chat with Dr. Myra' },
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={`px-5 py-3 text-sm font-semibold transition-all ${
                      tab === t.id
                        ? 'text-violet-700 border-b-2 border-violet-600 bg-violet-50/70'
                        : 'text-gray-500 hover:text-violet-700'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              <div className="p-6">
                {/* SHAP Values Tab */}
                {tab === 'single' && (
                  <div className="space-y-5">
                    <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-purple-50 p-5">
                      <h3 className="text-base font-bold text-gray-900 mb-3">
                        SHAP Explanation - {shapResult.predicted_class || 'Prediction'}
                      </h3>
                      
                      <div className="space-y-3 text-sm">
                        <p>
                          Base Value: <span className="font-bold">{shapResult.base_value.toFixed(3)}</span>
                        </p>
                        
                        <div className="border-t border-violet-200 pt-3">
                          <p className="font-semibold mb-2">Top Contributing Features:</p>
                          <div className="space-y-2">
                            {shapResult.top_features.map((feat, idx) => (
                              <div key={idx} className="flex items-center gap-2">
                                <span className="w-32 text-xs truncate">{feat.feature}</span>
                                <div 
                                  className={`h-4 rounded ${feat.shap_value > 0 ? 'bg-rose-300' : 'bg-emerald-300'}`}
                                  style={{ width: `${Math.abs(feat.shap_value) * 200}px` }}
                                />
                                <span className={`font-bold text-sm ${feat.shap_value > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
                                  {feat.shap_value > 0 ? '+' : ''}{feat.shap_value.toFixed(3)}
                                </span>
                                <span className="text-xs text-gray-500">
                                  (value: {feat.feature_value.toFixed(2)})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Waterfall Plot */}
                        {shapResult.waterfall_plot && (
                          <div className="border-t border-violet-200 pt-3">
                            <p className="font-semibold mb-2">SHAP Waterfall Plot:</p>
                            <img 
                              src={`data:image/png;base64,${shapResult.waterfall_plot}`}
                              alt="SHAP Waterfall Plot"
                              className="w-full rounded-lg border border-gray-200"
                            />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Info Box */}
                    <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
                      <p className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <Info className="w-4 h-4 text-blue-600" />
                        Understanding SHAP Values
                      </p>
                      <div className="text-sm text-gray-700 space-y-2">
                        <p>
                          SHAP values show how much each feature contributed to moving the prediction from the baseline.
                        </p>
                        <ul className="ml-4 space-y-1">
                          <li>• Positive values push toward positive class (higher severity)</li>
                          <li>• Negative values push toward negative class (lower severity)</li>
                          <li>• Larger absolute values = stronger influence</li>
                        </ul>
                      </div>
                    </div>

                    {/* Feature Table */}
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                      <h3 className="text-sm font-bold text-gray-900 mb-3">All Features (Ranked by Importance)</h3>
                      <div className="max-h-96 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-800 text-white sticky top-0">
                            <tr>
                              <th className="px-4 py-2 text-left">#</th>
                              <th className="px-4 py-2 text-left">Feature</th>
                              <th className="px-4 py-2 text-left">Value</th>
                              <th className="px-4 py-2 text-left">SHAP Value</th>
                              <th className="px-4 py-2 text-left">Impact</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white">
                            {shapResult.top_features.map((feat, idx) => (
                              <tr key={idx} className="border-t hover:bg-violet-50/30">
                                <td className="px-4 py-2">{idx + 1}</td>
                                <td className="px-4 py-2 font-medium">{feat.feature}</td>
                                <td className="px-4 py-2 font-mono">{feat.feature_value.toFixed(3)}</td>
                                <td className={`px-4 py-2 font-bold ${feat.shap_value > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                                  {feat.shap_value > 0 ? '+' : ''}{feat.shap_value.toFixed(3)}
                                </td>
                                <td className="px-4 py-2">
                                  <span className={`text-xs px-2 py-1 rounded ${feat.contribution === 'positive' ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                    {feat.contribution === 'positive' ? '↑ Increases' : '↓ Decreases'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {/* AI Explanation Tab */}
                {tab === 'llm' && (
                  <div className="space-y-5">
                    <div className="rounded-xl border border-violet-100 overflow-hidden">
                      <div className="bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-3 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-white" />
                        <h3 className="text-base font-bold text-white">Gemma AI Clinical Explanation</h3>
                      </div>
                      <div className="p-5 bg-white">
                        {aiExplanation ? (
                          <>
                            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line">
                              {aiExplanation}
                            </div>
                            <div className="mt-5 pt-4 border-t border-gray-200 text-xs text-gray-500">
                              This explanation was generated using Gemma-4-E4B based on SHAP analysis and clinical guidelines.
                            </div>
                            <div className="mt-4 flex gap-2">
                              <button 
                                onClick={() => generateAIExplanation(shapResult)}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-semibold hover:bg-gray-50"
                              >
                                <RefreshCw className="w-4 h-4" />
                                Regenerate
                              </button>
                            </div>
                          </>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            <p>Generating AI explanation...</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Dr. Myra Chat Tab */}
                {tab === 'chat' && (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-violet-100 bg-white p-5">
                      <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
                        <Brain className="w-5 h-5 text-violet-600" />
                        Chat with Dr. Myra (Gemma AI)
                      </h3>
                      
                      {/* Chat Messages */}
                      <div className="h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 mb-4 space-y-3">
                        {chatMessages.length === 0 ? (
                          <div className="text-center text-gray-500 py-8">
                            <p className="mb-2">👋 Hi! I'm Dr. Myra, your AI clinical assistant.</p>
                            <p className="text-sm">Ask me anything about the SHAP explanation or SLE in general!</p>
                          </div>
                        ) : (
                          chatMessages.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
                                msg.role === 'user' 
                                  ? 'bg-violet-600 text-white' 
                                  : 'bg-gray-100 text-gray-900'
                              }`}>
                                <p className="text-sm whitespace-pre-line">{msg.content}</p>
                              </div>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Chat Input */}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={userMessage}
                          onChange={(e) => setUserMessage(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleChatWithDrMyra()}
                          placeholder="Ask Dr. Myra about the explanation..."
                          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                        />
                        <button
                          onClick={handleChatWithDrMyra}
                          className="px-6 py-2 rounded-lg bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700"
                        >
                          Send
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>
      </main>
    </DashboardLayout>
  );
}
