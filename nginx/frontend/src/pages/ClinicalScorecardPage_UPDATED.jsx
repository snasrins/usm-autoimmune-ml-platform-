import { useState, useEffect } from 'react';
import { ChevronRight, Target, Download, CheckCircle2, Sparkles, Info, AlertCircle, Loader2 } from 'lucide-react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import { scorecardAPI, trainingAPI } from '../services/api-complete';

export default function ClinicalScorecardPage() {
  // === STATE MANAGEMENT ===
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState(null);
  const [scorecardId, setScorecardId] = useState(null);
  const [scorecardGenerated, setScorecardGenerated] = useState(false);
  
  // Generation config
  const [binningMethod, setBinningMethod] = useState('rolling_mean');
  const [numBins, setNumBins] = useState(4);
  const [useYouden, setUseYouden] = useState(true);
  
  // Data from backend
  const [binTables, setBinTables] = useState([]);
  const [riskStratification, setRiskStratification] = useState(null);
  const [selectedFeature, setSelectedFeature] = useState(null);
  
  // UI state
  const [tab, setTab] = useState('generate');
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Patient calculator
  const [patientData, setPatientData] = useState({});
  const [calculatedScore, setCalculatedScore] = useState(null);

  // === LOAD ON MOUNT ===
  useEffect(() => {
    loadModels();
    
    // Check if we have a pre-selected model from comparison page
    const selectedModelFromComparison = sessionStorage.getItem('selected_model_id');
    if (selectedModelFromComparison) {
      console.log('[Scorecard] Loaded model from comparison:', selectedModelFromComparison);
      setSelectedModelId(selectedModelFromComparison);
    }
    
    // Check if scorecard already exists
    const existingScorecardId = sessionStorage.getItem('scorecard_id');
    if (existingScorecardId) {
      console.log('[Scorecard] Found existing scorecard:', existingScorecardId);
      setScorecardId(existingScorecardId);
      setScorecardGenerated(true);
      loadScorecardData(existingScorecardId);
    }
  }, []);

  // === LOAD MODELS ===
  const loadModels = async () => {
    setLoading(true);
    try {
      const modelList = await trainingAPI.getModels(100, 0, true, 'completed');
      setModels(modelList.models || []);
    } catch (err) {
      console.error('Failed to load models:', err);
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  // === GENERATE SCORECARD ===
  const handleGenerateScorecard = async () => {
    if (!selectedModelId) {
      alert('Please select a model first');
      return;
    }

    setGenerating(true);
    setError(null);
    
    try {
      const result = await scorecardAPI.generateScorecard(selectedModelId, {
        binningMethod: binningMethod,
        numBins: numBins,
        useYouden: useYouden
      });
      
      setScorecardId(result.scorecard_id);
      sessionStorage.setItem('scorecard_id', result.scorecard_id);
      setScorecardGenerated(true);
      
      // Load scorecard data
      await loadScorecardData(result.scorecard_id);
      
      alert('Scorecard generated successfully!');
      setTab('bin-score'); // Switch to bin-score view
      
    } catch (err) {
      console.error('Scorecard generation failed:', err);
      setError(err.response?.data?.detail || 'Scorecard generation failed');
    } finally {
      setGenerating(false);
    }
  };

  // === LOAD SCORECARD DATA ===
  const loadScorecardData = async (scorecardId) => {
    setLoading(true);
    try {
      // Load bin tables
      const tables = await scorecardAPI.getBinScoreTables(scorecardId);
      setBinTables(tables);
      
      // Set first feature as selected if none selected
      if (!selectedFeature && tables.length > 0) {
        setSelectedFeature(tables[0].feature);
      }
      
      // Load risk stratification
      const stratification = await scorecardAPI.getRiskStratification(scorecardId);
      setRiskStratification(stratification);
      
    } catch (err) {
      console.error('Failed to load scorecard data:', err);
      setError('Failed to load scorecard data');
    } finally {
      setLoading(false);
    }
  };

  // === CALCULATE PATIENT SCORE ===
  const handleCalculatePatientScore = async () => {
    if (!scorecardId) {
      alert('Please generate scorecard first');
      return;
    }

    try {
      const result = await scorecardAPI.calculatePatientScore(scorecardId, patientData);
      setCalculatedScore(result);
      
    } catch (err) {
      console.error('Score calculation failed:', err);
      setError(err.response?.data?.detail || 'Score calculation failed');
    }
  };

  // === EXPORT CSV ===
  const handleExportCSV = async (exportType) => {
    if (!scorecardId) {
      alert('Please generate scorecard first');
      return;
    }

    try {
      const blob = await scorecardAPI.exportScorecardCSV(scorecardId, exportType);
      
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scorecard_${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert(`${exportType} exported successfully!`);
      
    } catch (err) {
      console.error('Export failed:', err);
      setError('Export failed');
    }
  };

  // === RENDER HELPERS ===
  const getCurrentBinTable = () => {
    if (!selectedFeature || !binTables.length) return null;
    return binTables.find(t => t.feature === selectedFeature);
  };

  const selectedBinTable = getCurrentBinTable();
  const selectedModel = models.find(m => m.id === selectedModelId);

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 border-b border-indigo-100 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Clinical Scorecard</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-indigo-600">Research-Grade Scorecard System</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#eef2ff] via-[#f9fafb] to-[#f0f4ff]" style={{ zoom: 0.9 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Error Display */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-sm text-red-700">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto text-red-600 hover:text-red-800"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Model Selection */}
          <section className="rounded-2xl border border-indigo-100 bg-white p-5">
            <h3 className="text-sm font-bold text-gray-900 mb-3">Model Selection</h3>
            <div className="grid grid-cols-3 gap-4 items-end">
              <div className="col-span-2">
                <label className="text-sm font-semibold text-gray-700">Select Model for Scorecard Generation</label>
                <select
                  value={selectedModelId || ''}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  disabled={loading}
                >
                  <option value="">-- Select a trained model --</option>
                  {models.map(model => (
                    <option key={model.id} value={model.id}>
                      {model.algorithm_name} (AUC: {model.metrics?.auc?.toFixed(4) || 'N/A'}) - {new Date(model.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                {scorecardGenerated ? (
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <span className="text-gray-700">Scorecard Generated</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-5 h-5 border-2 border-gray-300 rounded" />
                    Not Generated
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* Tabs */}
          <section className="rounded-2xl border border-indigo-100 bg-white overflow-hidden">
            <div className="flex border-b border-indigo-100">
              {[
                { id: 'generate', label: 'Generate Scorecard' },
                { id: 'bin-score', label: 'Bin-Score Tables', disabled: !scorecardGenerated },
                { id: 'stratification', label: 'Risk Stratification', disabled: !scorecardGenerated },
                { id: 'calculator', label: 'Patient Calculator', disabled: !scorecardGenerated },
                { id: 'export', label: 'Export Reports', disabled: !scorecardGenerated },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => !t.disabled && setTab(t.id)}
                  disabled={t.disabled}
                  className={`px-5 py-3 text-sm font-semibold transition-all ${
                    tab === t.id
                      ? 'text-indigo-700 border-b-2 border-indigo-600 bg-indigo-50/70'
                      : t.disabled
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-500 hover:text-indigo-700'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* TAB: GENERATE */}
              {tab === 'generate' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Scorecard Generation Settings</h3>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">Binning Method</label>
                    <select
                      value={binningMethod}
                      onChange={(e) => setBinningMethod(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    >
                      <option value="rolling_mean">Rolling Mean (Research Study) 🏆</option>
                      <option value="quantile">Quantile (equal frequency)</option>
                      <option value="equal_width">Equal Width (equal intervals)</option>
                      <option value="target_based">Target-Based (maximize separation)</option>
                      <option value="tree_based">Tree-Based (decision tree splits)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">
                      Number of Bins per Feature: <span className="text-indigo-600">{numBins}</span>
                    </label>
                    <input
                      type="range"
                      min="4"
                      max="10"
                      value={numBins}
                      onChange={(e) => setNumBins(parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={useYouden}
                      onChange={(e) => setUseYouden(e.target.checked)}
                      id="youden-checkbox"
                    />
                    <label htmlFor="youden-checkbox" className="text-sm text-gray-700 flex items-center gap-2">
                      Use Youden Index: Optimize threshold statistically (Sensitivity + Specificity - 1)
                      <Info className="w-4 h-4 text-gray-500" />
                    </label>
                  </div>

                  <button
                    onClick={handleGenerateScorecard}
                    disabled={generating || !selectedModelId}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-indigo-600 to-blue-600 text-white text-sm font-semibold shadow-lg hover:from-indigo-700 hover:to-blue-700 transition-all disabled:opacity-50"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Generating Scorecard...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5" />
                        Generate Clinical Scorecard
                      </>
                    )}
                  </button>

                  {generating && (
                    <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
                      <p className="text-sm text-indigo-700">
                        Generating scorecard with research-grade binning and Youden optimization...
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: BIN-SCORE TABLES */}
              {tab === 'bin-score' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Bin-Score Transparency Tables</h3>

                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                    </div>
                  ) : binTables.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <p>No bin tables available. Generate scorecard first.</p>
                    </div>
                  ) : (
                    <>
                      {/* Feature Selector */}
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Select Feature</label>
                        <select
                          value={selectedFeature || ''}
                          onChange={(e) => setSelectedFeature(e.target.value)}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        >
                          {binTables.map(table => (
                            <option key={table.feature} value={table.feature}>
                              {table.feature}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Bin Table */}
                      {selectedBinTable && (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-indigo-50 border-b border-indigo-200">
                              <tr>
                                <th className="px-4 py-2 text-left font-semibold text-gray-700">Bin Range</th>
                                <th className="px-4 py-2 text-right font-semibold text-gray-700">Score</th>
                                <th className="px-4 py-2 text-right font-semibold text-gray-700">Count</th>
                                <th className="px-4 py-2 text-right font-semibold text-gray-700">Proportion</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedBinTable.bins.map((bin, idx) => (
                                <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                                  <td className="px-4 py-2">{bin.range_label}</td>
                                  <td className="px-4 py-2 text-right font-semibold text-indigo-600">
                                    {bin.score.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-2 text-right">{bin.count}</td>
                                  <td className="px-4 py-2 text-right">
                                    {(bin.proportion * 100).toFixed(1)}%
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* TAB: RISK STRATIFICATION */}
              {tab === 'stratification' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Risk Stratification</h3>

                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                    </div>
                  ) : !riskStratification ? (
                    <div className="text-center py-12 text-gray-500">
                      <p>No stratification data available.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-indigo-50 rounded-lg">
                        <p className="text-sm text-gray-600">Optimal Threshold (Youden)</p>
                        <p className="text-2xl font-bold text-indigo-600">
                          {riskStratification.threshold?.toFixed(2)}
                        </p>
                      </div>
                      <div className="p-4 bg-emerald-50 rounded-lg">
                        <p className="text-sm text-gray-600">Youden Index</p>
                        <p className="text-2xl font-bold text-emerald-600">
                          {riskStratification.youden_index?.toFixed(4)}
                        </p>
                      </div>
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-gray-600">Sensitivity</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {(riskStratification.sensitivity * 100)?.toFixed(1)}%
                        </p>
                      </div>
                      <div className="p-4 bg-purple-50 rounded-lg">
                        <p className="text-sm text-gray-600">Specificity</p>
                        <p className="text-2xl font-bold text-purple-600">
                          {(riskStratification.specificity * 100)?.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: PATIENT CALCULATOR */}
              {tab === 'calculator' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Patient Risk Calculator</h3>

                  <div className="grid grid-cols-2 gap-4">
                    {binTables.slice(0, 6).map(table => (
                      <div key={table.feature}>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          {table.feature}
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="Enter value"
                          value={patientData[table.feature] || ''}
                          onChange={(e) => setPatientData(prev => ({
                            ...prev,
                            [table.feature]: e.target.value
                          }))}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        />
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={handleCalculatePatientScore}
                    className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                  >
                    <Target className="w-4 h-4 inline mr-2" />
                    Calculate Risk Score
                  </button>

                  {calculatedScore && (
                    <div className="mt-6 p-6 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg border-2 border-indigo-200">
                      <h4 className="text-lg font-bold text-gray-900 mb-4">Risk Assessment Result</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Total Score</p>
                          <p className="text-3xl font-bold text-indigo-600">
                            {calculatedScore.total_score?.toFixed(1)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Risk Group</p>
                          <p className={`text-3xl font-bold ${
                            calculatedScore.risk_group === 'HIGH_RISK' ? 'text-red-600' : 'text-emerald-600'
                          }`}>
                            {calculatedScore.risk_group?.replace('_', ' ')}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: EXPORT */}
              {tab === 'export' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Export Clinical Reports</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={() => handleExportCSV('bin_tables')}
                      className="flex items-center gap-3 p-4 rounded-lg border-2 border-indigo-200 hover:bg-indigo-50 transition-all"
                    >
                      <Download className="w-5 h-5 text-indigo-600" />
                      <div className="text-left">
                        <p className="font-semibold text-gray-900">Bin-Score Tables</p>
                        <p className="text-sm text-gray-600">All feature lookup tables</p>
                      </div>
                    </button>

                    <button
                      onClick={() => handleExportCSV('threshold_report')}
                      className="flex items-center gap-3 p-4 rounded-lg border-2 border-indigo-200 hover:bg-indigo-50 transition-all"
                    >
                      <Download className="w-5 h-5 text-indigo-600" />
                      <div className="text-left">
                        <p className="font-semibold text-gray-900">Threshold Report</p>
                        <p className="text-sm text-gray-600">Youden index & metrics</p>
                      </div>
                    </button>

                    <button
                      onClick={() => handleExportCSV('patient_scores')}
                      className="flex items-center gap-3 p-4 rounded-lg border-2 border-indigo-200 hover:bg-indigo-50 transition-all"
                    >
                      <Download className="w-5 h-5 text-indigo-600" />
                      <div className="text-left">
                        <p className="font-semibold text-gray-900">Patient Scores</p>
                        <p className="text-sm text-gray-600">Individual risk scores</p>
                      </div>
                    </button>

                    <button
                      onClick={() => handleExportCSV('comprehensive')}
                      className="flex items-center gap-3 p-4 rounded-lg border-2 border-emerald-200 bg-emerald-50 hover:bg-emerald-100 transition-all"
                    >
                      <Download className="w-5 h-5 text-emerald-600" />
                      <div className="text-left">
                        <p className="font-semibold text-gray-900">Comprehensive Report</p>
                        <p className="text-sm text-gray-600">All data combined</p>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </DashboardLayout>
  );
}
