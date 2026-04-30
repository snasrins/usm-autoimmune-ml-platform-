import { useState } from 'react';
import { ChevronRight, Upload, Download, Brain, Sparkles, Info, RefreshCw } from 'lucide-react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import DashboardLayout from '../components/DashboardLayout';

const SHAP_FEATURE_DATA = [
  { feature: 'CRP_high', value: 1.5, shap: 0.18, direction: 'high' },
  { feature: 'ESR_high', value: 95, shap: 0.12, direction: 'high' },
  { feature: 'Low_C3', value: 0.45, shap: 0.08, direction: 'high' },
  { feature: 'PLT_normal', value: 230, shap: -0.06, direction: 'low' },
  { feature: 'WBC_normal', value: 5.2, shap: -0.04, direction: 'low' },
  { feature: 'Anti_dsDNA', value: 120, shap: 0.03, direction: 'high' },
];

const GLOBAL_IMPORTANCE = [
  { feature: 'CRP_high', importance: 0.142 },
  { feature: 'ESR_high', importance: 0.118 },
  { feature: 'Low_C3', importance: 0.095 },
  { feature: 'Anti_dsDNA', importance: 0.087 },
  { feature: 'Urine_protein', importance: 0.076 },
  { feature: 'C4', importance: 0.064 },
  { feature: 'ALB', importance: 0.052 },
];

const LLM_EXPLANATION = `**Patient Risk Assessment for Patient P001**

The model predicts this patient is at **HIGH RISK** (73% confidence) for severe disease activity. Here's why:

**Key Risk Factors:**

1. **Elevated CRP (1.5 mg/dL)** - Strongest risk indicator
   • CRP is significantly elevated, suggesting active inflammation
   • This single factor increases risk probability by 18%
   • Clinical Note: CRP > 1.0 is associated with flare risk

2. **High ESR (95 mm/hr)** - Second strongest indicator
   • ESR is markedly elevated, confirming systemic inflammation
   • Contributes an additional 12% to risk probability
   • Combined CRP+ESR elevation is highly predictive

3. **Low Complement C3 (0.45 g/L)** - Immune system activation
   • C3 below normal range indicates complement consumption
   • Adds 8% to risk probability
   • Suggests active immune complex formation

**Protective Factors:**

1. **Normal Platelet Count (230 × 10⁹/L)**
   • Reduces risk by 6%
   • No evidence of thrombocytopenia

2. **Normal WBC (5.2 × 10⁹/L)**
   • Reduces risk by 4%
   • No leukopenia detected

**Clinical Interpretation:**

The combination of elevated inflammatory markers (CRP, ESR) and low complement strongly suggests active disease. While blood counts are reassuringly normal, the inflammatory profile dominates the risk assessment.

**Recommended Actions:**
• Consider therapy escalation
• Repeat labs in 2-4 weeks
• Monitor for organ involvement
• Assess SLEDAI score clinically

**Confidence Assessment:**
The model is moderately confident (73%) due to:
✅ Strong inflammatory markers
✅ Consistent pattern across multiple features
⚠️ Some normal lab values create uncertainty`;

export default function ModelExplainabilityPage() {
  const [modelName, setModelName] = useState('Stacking Ensemble v1.0');
  const [tab, setTab] = useState('single');
  const [patientId, setPatientId] = useState('Patient P001 (Predicted: High Risk, Actual: High Risk)');
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [llmModel, setLlmModel] = useState('gpt-4');
  const [detailLevel, setDetailLevel] = useState(50);

  const handleAnalyze = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setAnalyzing(false);
      setAnalyzed(true);
    }, 1500);
  };

  const baseValue = 0.45;
  const finalPrediction = 0.73;

  return (
    <DashboardLayout>
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 border-b border-violet-100 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Model Explainability</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-violet-600">SHAP + LLM Explanations</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#f5f3ff] via-[#faf9fc] to-[#f0edff]" style={{ zoom: 0.9 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          <section className="rounded-2xl border border-violet-100 bg-white p-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-semibold text-gray-700">Select Model</label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  <option>Stacking Ensemble v1.0</option>
                  <option>Logistic Regression v2.1</option>
                  <option>Random Forest v1.5</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-700">Explain Prediction For</label>
                <div className="mt-2 space-y-1 text-sm">
                  <label className="flex items-center gap-2">
                    <input type="radio" name="explainType" defaultChecked />
                    Single Patient
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="explainType" />
                    Batch Analysis
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="explainType" />
                    Global Feature Importance
                  </label>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-violet-100 bg-white overflow-hidden">
            <div className="flex border-b border-violet-100">
              {[
                { id: 'single', label: 'SHAP Values - Single' },
                { id: 'llm', label: 'AI Explanation' },
                { id: 'global', label: 'Global Importance' },
                { id: 'batch', label: 'Batch Analysis' },
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
              {tab === 'single' && (
                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">Select Patient to Explain</label>
                    <select
                      value={patientId}
                      onChange={(e) => setPatientId(e.target.value)}
                      className="w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    >
                      <option>Patient P001 (Predicted: High Risk, Actual: High Risk)</option>
                      <option>Patient P002 (Predicted: Low Risk, Actual: Low Risk)</option>
                      <option>Patient P003 (Predicted: High Risk, Actual: Low Risk)</option>
                    </select>
                  </div>

                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-semibold shadow-lg hover:from-violet-700 hover:to-purple-700 transition-all disabled:opacity-50"
                  >
                    <Brain className="w-4 h-4" />
                    {analyzing ? 'Analyzing...' : 'Analyze Prediction'}
                  </button>

                  {analyzed && (
                    <>
                      <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 to-purple-50 p-5">
                        <h3 className="text-base font-bold text-gray-900 mb-3">SHAP FORCE PLOT - Patient P001</h3>
                        <div className="space-y-3 text-sm">
                          <p>
                            Base Value: <span className="font-bold">{baseValue}</span> (Average model prediction)
                          </p>
                          <div className="border-t border-violet-200 pt-3">
                            <p className="font-semibold mb-2">Features Pushing TOWARD High Risk:</p>
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="w-24">CRP_high</span>
                                <div className="flex-1 h-4 bg-rose-200 rounded" style={{ width: '90%' }} />
                                <span className="font-bold text-rose-700">+0.18</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-24">ESR_high</span>
                                <div className="flex-1 h-4 bg-rose-200 rounded" style={{ width: '60%' }} />
                                <span className="font-bold text-rose-700">+0.12</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-24">Low_C3</span>
                                <div className="flex-1 h-4 bg-rose-200 rounded" style={{ width: '40%' }} />
                                <span className="font-bold text-rose-700">+0.08</span>
                              </div>
                            </div>
                          </div>
                          <div className="border-t border-violet-200 pt-3">
                            <p className="font-semibold mb-2">Features Pushing TOWARD Low Risk:</p>
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="w-24">PLT_normal</span>
                                <div className="flex-1 h-4 bg-emerald-200 rounded" style={{ width: '30%' }} />
                                <span className="font-bold text-emerald-700">-0.06</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-24">WBC_normal</span>
                                <div className="flex-1 h-4 bg-emerald-200 rounded" style={{ width: '20%' }} />
                                <span className="font-bold text-emerald-700">-0.04</span>
                              </div>
                            </div>
                          </div>
                          <div className="border-t border-violet-200 pt-3">
                            <p className="text-lg font-bold">
                              Final Prediction: <span className="text-rose-600">{finalPrediction}</span> (High Risk)
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                          <Info className="w-4 h-4 text-blue-600" />
                          What does this mean?
                        </p>
                        <div className="text-sm text-gray-700 space-y-2">
                          <p>
                            SHAP (SHapley Additive exPlanations) values show how much each feature contributed to moving the prediction from the average
                            (base value = {baseValue}) to the final prediction ({finalPrediction}).
                          </p>
                          <ul className="ml-4 space-y-1">
                            <li>• Positive SHAP values push toward HIGH RISK</li>
                            <li>• Negative SHAP values push toward LOW RISK</li>
                            <li>• Larger absolute values = stronger influence</li>
                          </ul>
                          <p>
                            For Patient P001: CRP_high has the strongest effect (+0.18), combined inflammatory markers push risk up by +0.38, final
                            prediction: {baseValue} (base) + 0.28 (net) = {finalPrediction}
                          </p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-gray-200 bg-white p-4">
                        <h3 className="text-sm font-bold text-gray-900 mb-3">FEATURE CONTRIBUTIONS (Ranked by Absolute SHAP Value)</h3>
                        <table className="w-full text-sm">
                          <thead className="bg-gray-800 text-white">
                            <tr>
                              <th className="px-4 py-2 text-left">Feature</th>
                              <th className="px-4 py-2 text-left">Value</th>
                              <th className="px-4 py-2 text-left">SHAP Value</th>
                              <th className="px-4 py-2 text-left">Effect</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white">
                            {SHAP_FEATURE_DATA.map((row) => (
                              <tr key={row.feature} className="border-t hover:bg-violet-50/30">
                                <td className="px-4 py-2">{row.feature}</td>
                                <td className="px-4 py-2 font-mono">{row.value}</td>
                                <td className={`px-4 py-2 font-bold ${row.shap > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                                  {row.shap > 0 ? '+' : ''}
                                  {row.shap}
                                </td>
                                <td className="px-4 py-2 text-xs">
                                  {row.direction === 'high' ? '↑ High Risk' : '↓ Low Risk'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <button className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-semibold hover:bg-gray-50">
                          <Download className="w-4 h-4" />
                          Export Table (CSV)
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {tab === 'llm' && (
                <div className="space-y-5">
                  <div className="rounded-xl border border-violet-100 overflow-hidden">
                    <div className="bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-3 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-white" />
                      <h3 className="text-base font-bold text-white">AI-GENERATED CLINICAL EXPLANATION</h3>
                    </div>
                    <div className="p-5 bg-white">
                      <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line">
                        {LLM_EXPLANATION}
                      </div>
                      <div className="mt-5 pt-4 border-t border-gray-200 text-xs text-gray-500">
                        This explanation was generated using advanced AI (GPT-4) based on SHAP analysis and clinical guidelines.
                      </div>
                      <div className="mt-4 flex gap-2">
                        <button className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700">
                          <Download className="w-4 h-4" />
                          Export Explanation (PDF)
                        </button>
                        <button className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-semibold hover:bg-gray-50">
                          <RefreshCw className="w-4 h-4" />
                          Regenerate
                        </button>
                      </div>
                    </div>
                  </div>

                  <details className="rounded-lg border border-violet-100">
                    <summary className="px-4 py-3 bg-violet-50 cursor-pointer font-semibold text-sm">
                      ▼ AI Explanation Settings
                    </summary>
                    <div className="p-4 space-y-3">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">Model</label>
                        <select
                          value={llmModel}
                          onChange={(e) => setLlmModel(e.target.value)}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        >
                          <option value="gpt-4">GPT-4 (Best Quality)</option>
                          <option value="gpt-3.5">GPT-3.5-Turbo</option>
                          <option value="claude-3">Claude-3</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          Detail Level: {detailLevel < 33 ? 'Brief' : detailLevel < 67 ? 'Moderate' : 'Detailed'}
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={detailLevel}
                          onChange={(e) => setDetailLevel(parseInt(e.target.value))}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-1 text-sm">
                        <label className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked />
                          Include Clinical Context
                        </label>
                        <label className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked />
                          Include Lab Reference Ranges
                        </label>
                        <label className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked />
                          Include Recommended Actions
                        </label>
                      </div>
                      <button className="px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700">
                        Apply Settings
                      </button>
                    </div>
                  </details>
                </div>
              )}

              {tab === 'global' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Global Feature Importance</h3>
                  <div className="rounded-xl border border-gray-200 bg-white p-4">
                    <h3 className="text-sm font-bold text-gray-900 mb-3">SHAP Bar Plot (Mean Absolute SHAP)</h3>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={GLOBAL_IMPORTANCE} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                          <XAxis type="number" tick={{ fontSize: 11 }} />
                          <YAxis type="category" dataKey="feature" width={120} tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="importance" fill="#7c3aed" radius={[0, 6, 6, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-xs text-gray-600 mt-3">
                      Average impact on model output across all patients. Higher values = more important features.
                    </p>
                    <button className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-semibold hover:bg-gray-50">
                      <Download className="w-4 h-4" />
                      Export Global Importance (CSV)
                    </button>
                  </div>
                </div>
              )}

              {tab === 'batch' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-bold text-gray-900">Batch Explainability Analysis</h3>
                  <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-8 text-center">
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-sm text-gray-600 mb-2">Upload CSV with multiple patients</p>
                    <p className="text-xs text-gray-500 mb-4">
                      Expected format: patient_id, WBC, HGB, PLT, CRP, ESR, ...
                    </p>
                    <button className="px-5 py-2.5 rounded-lg bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700">
                      Choose File
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section className="rounded-lg bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-100 p-5">
            <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Info className="w-5 h-5 text-violet-600" />
              Why SHAP + LLM?
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
              <div>
                <p className="font-semibold mb-2">SHAP Values Provide:</p>
                <ul className="ml-4 space-y-1">
                  <li>• Quantitative feature contributions</li>
                  <li>• Mathematically rigorous</li>
                  <li>• Model-agnostic</li>
                  <li>• Local + Global explanations</li>
                </ul>
              </div>
              <div>
                <p className="font-semibold mb-2">LLM Enhancement Adds:</p>
                <ul className="ml-4 space-y-1">
                  <li>• Natural language explanations</li>
                  <li>• Clinical context</li>
                  <li>• Actionable recommendations</li>
                  <li>• Accessible to non-technical users</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </main>
    </DashboardLayout>
  );
}
