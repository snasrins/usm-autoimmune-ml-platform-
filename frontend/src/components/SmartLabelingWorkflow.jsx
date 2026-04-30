import { useState, useEffect } from 'react';
import {
  Tag,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Play,
  RefreshCw,
  Eye,
  Save,
  Upload,
  Settings,
  BarChart3,
  HelpCircle,
  Zap,
  FileText,
  Target,
  Database
} from 'lucide-react';
import { labelingAPI } from '../services/api';

// ========== AUTO-LABELING PRESETS ==========
const LABELING_PRESETS = {
  severity_sledai: {
    id: 'severity_sledai',
    name: 'Disease Severity (SLEDAI-Based)',
    description: 'Automatically assign severity labels based on SLEDAI score',
    icon: '🎯',
    sourceColumn: 'SLEDAI',
    targetColumn: 'labels_disease_severity',
    labelType: 'severity',
    rules: [
      { condition: 'SLEDAI ≤ 4', label: 'Mild', color: 'bg-green-100 text-green-700', count: 0 },
      { condition: 'SLEDAI 5-12', label: 'Moderate', color: 'bg-amber-100 text-amber-700', count: 0 },
      { condition: 'SLEDAI > 12', label: 'Severe', color: 'bg-red-100 text-red-700', count: 0 }
    ],
    recommended: true
  },
  kidney_protein: {
    id: 'kidney_protein',
    name: 'Kidney Involvement (Protein-Based)',
    description: 'Assign organ involvement based on urinary protein levels',
    icon: '🩺',
    sourceColumn: 'Urine_protein_quantification',
    targetColumn: 'labels_organ_involvement',
    labelType: 'kidney',
    rules: [
      { condition: '- or 无', label: 'No Kidney Involvement', color: 'bg-green-100 text-green-700', count: 0 },
      { condition: '±', label: 'Trace Proteinuria', color: 'bg-amber-100 text-amber-700', count: 0 },
      { condition: '+, 2+, 3+, 4+', label: 'Lupus Nephritis', color: 'bg-red-100 text-red-700', count: 0 }
    ],
    recommended: true
  },
  activity_sledai: {
    id: 'activity_sledai',
    name: 'Disease Activity (SLEDAI-Based)',
    description: 'Classify disease activity status from SLEDAI',
    icon: '📊',
    sourceColumn: 'SLEDAI',
    targetColumn: 'labels_disease_activity',
    labelType: 'activity',
    rules: [
      { condition: 'SLEDAI = 0', label: 'Remission', color: 'bg-green-100 text-green-700', count: 0 },
      { condition: 'SLEDAI 1-10', label: 'Active', color: 'bg-amber-100 text-amber-700', count: 0 },
      { condition: 'SLEDAI > 10', label: 'Flare', color: 'bg-red-100 text-red-700', count: 0 }
    ]
  }
};

export default function SmartLabelingWorkflow({ batchId, onComplete, onBack }) {
  const [activeTab, setActiveTab] = useState('auto'); // 'auto', 'manual', 'import', 'stats'
  const [loading, setLoading] = useState(false);
  
  // Auto-labeling state
  const [selectedPreset, setSelectedPreset] = useState('severity_sledai');
  const [customSourceColumn, setCustomSourceColumn] = useState('');
  const [customTargetColumn, setCustomTargetColumn] = useState('labels_disease_severity');
  const [customLabelType, setCustomLabelType] = useState('severity');
  const [useCustom, setUseCustom] = useState(false);
  const [autoLabelResults, setAutoLabelResults] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // Statistics state
  const [labelStats, setLabelStats] = useState(null);
  const [unlabeledRecords, setUnlabeledRecords] = useState([]);
  
  // Manual labeling state
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [manualLabel, setManualLabel] = useState('');
  
  // Available columns (would be fetched from API)
  const [availableColumns, setAvailableColumns] = useState([
    'SLEDAI', 'BILAG', 'Disease_Activity', 
    'Urine_protein_quantification', 'CRP', 'ESR',
    'Anti_dsDNA', 'C3', 'C4'
  ]);

  const currentPreset = LABELING_PRESETS[selectedPreset];

  // Fetch label statistics
  useEffect(() => {
    if (batchId) {
      fetchLabelStatistics();
      fetchUnlabeledRecords();
    }
  }, [batchId, activeTab]);

  const fetchLabelStatistics = async () => {
    try {
      const stats = await labelingAPI.getLabelStatistics(batchId, customTargetColumn);
      setLabelStats(stats);
    } catch (error) {
      console.error('Failed to fetch label statistics:', error);
    }
  };

  const fetchUnlabeledRecords = async () => {
    try {
      const response = await labelingAPI.getUnlabeledRecords(batchId, customTargetColumn, 50);
      setUnlabeledRecords(response.records || []);
    } catch (error) {
      console.error('Failed to fetch unlabeled records:', error);
    }
  };

  const handleAutoLabel = async () => {
    setLoading(true);
    try {
      const sourceCol = useCustom ? customSourceColumn : currentPreset.sourceColumn;
      const targetCol = useCustom ? customTargetColumn : currentPreset.targetColumn;
      const labelType = useCustom ? customLabelType : currentPreset.labelType;

      const result = await labelingAPI.autoLabel(batchId, sourceCol, targetCol, labelType);
      
      setAutoLabelResults(result);
      
      // Refresh statistics
      await fetchLabelStatistics();
      await fetchUnlabeledRecords();
      
      setLoading(false);
    } catch (error) {
      console.error('Auto-labeling failed:', error);
      setLoading(false);
      alert('Auto-labeling failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleManualBulkLabel = async () => {
    if (selectedRecords.length === 0 || !manualLabel) {
      alert('Please select records and choose a label');
      return;
    }

    setLoading(true);
    try {
      await labelingAPI.bulkAssignLabels(selectedRecords, manualLabel, 1.0, customTargetColumn);
      
      // Refresh
      await fetchLabelStatistics();
      await fetchUnlabeledRecords();
      setSelectedRecords([]);
      setLoading(false);
    } catch (error) {
      console.error('Manual labeling failed:', error);
      setLoading(false);
      alert('Manual labeling failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-8 h-8" />
              <h2 className="font-syne text-2xl font-bold">Smart Labeling Workflow</h2>
            </div>
            <p className="text-purple-100 text-sm">
              Flexible column-level labeling with preset strategies or custom rules
            </p>
          </div>
          {labelStats && (
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 text-center">
              <div className="text-3xl font-bold">{labelStats.progress_percentage || 0}%</div>
              <div className="text-xs text-purple-100 mt-1">
                {labelStats.labeled_count || 0}/{labelStats.total_records || 0} Labeled
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('auto')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'auto'
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Auto-Label
          </div>
        </button>
        <button
          onClick={() => setActiveTab('manual')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'manual'
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4" />
            Manual Label
          </div>
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'stats'
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Statistics
            {labelStats && (
              <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
                {labelStats.labeled_count || 0}
              </span>
            )}
          </div>
        </button>
      </div>

      {/* TAB 1: AUTO-LABEL */}
      {activeTab === 'auto' && (
        <div className="space-y-6">
          {/* Mode Selection */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg text-gray-900">Labeling Mode</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setUseCustom(false)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    !useCustom
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Preset Strategies
                </button>
                <button
                  onClick={() => setUseCustom(true)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    useCustom
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Custom Rules
                </button>
              </div>
            </div>

            {/* PRESET MODE */}
            {!useCustom && (
              <div className="grid grid-cols-1 gap-4">
                {Object.values(LABELING_PRESETS).map((preset) => (
                  <div
                    key={preset.id}
                    onClick={() => setSelectedPreset(preset.id)}
                    className={`cursor-pointer rounded-xl border-2 p-4 transition-all ${
                      selectedPreset === preset.id
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="text-3xl">{preset.icon}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-gray-900">{preset.name}</h4>
                          {preset.recommended && (
                            <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-bold">
                              Recommended
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{preset.description}</p>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-500">Source Column:</span>
                            <div className="font-mono font-semibold text-purple-600">{preset.sourceColumn}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Target Column:</span>
                            <div className="font-mono font-semibold text-purple-600">{preset.targetColumn}</div>
                          </div>
                        </div>

                        <div className="mt-3 flex flex-wrap gap-2">
                          {preset.rules.map((rule, idx) => (
                            <div
                              key={idx}
                              className={`px-3 py-1.5 rounded-lg ${rule.color} text-xs font-medium`}
                            >
                              <div className="font-bold">{rule.label}</div>
                              <div className="text-[10px] opacity-75">{rule.condition}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* CUSTOM MODE */}
            {useCustom && (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <HelpCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-blue-700">
                      <strong>Custom Labeling:</strong> Choose any column from your dataset as the source,
                      and define custom rules for how values should be converted to labels.
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Source Column (Clinical Data)
                    </label>
                    <select
                      value={customSourceColumn}
                      onChange={(e) => setCustomSourceColumn(e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    >
                      <option value="">Select column...</option>
                      {availableColumns.map((col) => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Which column contains the clinical data to base labels on?
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Column (Where to Store Label)
                    </label>
                    <select
                      value={customTargetColumn}
                      onChange={(e) => setCustomTargetColumn(e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    >
                      <option value="labels_disease_severity">labels_disease_severity</option>
                      <option value="labels_disease_activity">labels_disease_activity</option>
                      <option value="labels_organ_involvement">labels_organ_involvement</option>
                      <option value="labels_disease_classification">labels_disease_classification</option>
                      <option value="labels_treatment_response">labels_treatment_response</option>
                      <option value="labels_flare_risk">labels_flare_risk</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Which label column should be populated?
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Label Strategy
                  </label>
                  <select
                    value={customLabelType}
                    onChange={(e) => setCustomLabelType(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  >
                    <option value="severity">Severity (≤4=Mild, 5-12=Moderate, >12=Severe)</option>
                    <option value="kidney">Kidney Involvement (-/无=No, ±=Trace, +=Nephritis)</option>
                    <option value="activity">Activity (0=Remission, 1-10=Active, >10=Flare)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    How should values be converted to labels?
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Preview & Execute */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-lg text-gray-900 mb-4">Execute Auto-Labeling</h3>
            
            {autoLabelResults && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">
                    Auto-labeling completed successfully!
                  </span>
                </div>
                <div className="text-sm text-green-700 space-y-1">
                  <div>✓ <strong>{autoLabelResults.labeled_count || 0}</strong> records labeled</div>
                  <div>⊘ <strong>{autoLabelResults.skipped_count || 0}</strong> records skipped (missing source data)</div>
                  <div>❌ <strong>{autoLabelResults.error_count || 0}</strong> errors</div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={handleAutoLabel}
                disabled={loading || (useCustom && !customSourceColumn)}
                className="flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Labeling...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Run Auto-Labeling
                  </>
                )}
              </button>

              {!useCustom && (
                <div className="flex-1 text-sm text-gray-600">
                  <strong>Will label using:</strong> {currentPreset?.name}
                  <br />
                  <span className="text-xs">
                    Source: <code className="bg-gray-100 px-1 rounded">{currentPreset?.sourceColumn}</code>
                    {' → '}
                    Target: <code className="bg-gray-100 px-1 rounded">{currentPreset?.targetColumn}</code>
                  </span>
                </div>
              )}

              {useCustom && customSourceColumn && (
                <div className="flex-1 text-sm text-gray-600">
                  <strong>Will label using:</strong> Custom rules
                  <br />
                  <span className="text-xs">
                    Source: <code className="bg-gray-100 px-1 rounded">{customSourceColumn}</code>
                    {' → '}
                    Target: <code className="bg-gray-100 px-1 rounded">{customTargetColumn}</code>
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: MANUAL LABEL */}
      {activeTab === 'manual' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-lg text-gray-900 mb-4">
              Manual Labeling ({unlabeledRecords.length} unlabeled records)
            </h3>

            {unlabeledRecords.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
                <h4 className="font-semibold text-gray-900 mb-2">All records are labeled!</h4>
                <p className="text-sm text-gray-600">No unlabeled records found in this batch.</p>
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center gap-3">
                  <select
                    value={manualLabel}
                    onChange={(e) => setManualLabel(e.target.value)}
                    className="px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600"
                  >
                    <option value="">Select label...</option>
                    <option value="Mild">Mild</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Severe">Severe</option>
                  </select>

                  <button
                    onClick={handleManualBulkLabel}
                    disabled={loading || selectedRecords.length === 0 || !manualLabel}
                    className="px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Label {selectedRecords.length} Selected
                  </button>

                  <span className="text-sm text-gray-600">
                    {selectedRecords.length} of {unlabeledRecords.length} selected
                  </span>
                </div>

                <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
                  <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                          <input
                            type="checkbox"
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedRecords(unlabeledRecords.map(r => r.record_id));
                              } else {
                                setSelectedRecords([]);
                              }
                            }}
                            checked={selectedRecords.length === unlabeledRecords.length && unlabeledRecords.length > 0}
                          />
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Record ID</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Preview</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {unlabeledRecords.map((record) => (
                        <tr key={record.record_id} className="hover:bg-gray-50">
                          <td className="px-4 py-2">
                            <input
                              type="checkbox"
                              checked={selectedRecords.includes(record.record_id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedRecords([...selectedRecords, record.record_id]);
                                } else {
                                  setSelectedRecords(selectedRecords.filter(id => id !== record.record_id));
                                }
                              }}
                            />
                          </td>
                          <td className="px-4 py-2 text-sm font-mono text-gray-900">{record.record_id}</td>
                          <td className="px-4 py-2 text-xs text-gray-600">
                            {record.data && Object.keys(record.data).slice(0, 3).map(key => 
                              `${key}: ${record.data[key]}`
                            ).join(', ')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: STATISTICS */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          {labelStats && (
            <>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-500 mb-1">Total Records</div>
                  <div className="text-2xl font-bold text-gray-900">{labelStats.total_records}</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-500 mb-1">Labeled</div>
                  <div className="text-2xl font-bold text-green-600">{labelStats.labeled_count}</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-500 mb-1">Unlabeled</div>
                  <div className="text-2xl font-bold text-amber-600">{labelStats.unlabeled_count}</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-500 mb-1">Progress</div>
                  <div className="text-2xl font-bold text-purple-600">{labelStats.progress_percentage}%</div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-semibold text-lg text-gray-900 mb-4">Label Distribution</h3>
                <div className="space-y-3">
                  {labelStats.label_distribution && Object.entries(labelStats.label_distribution).map(([label, count]) => (
                    <div key={label}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="font-medium text-gray-900">{label}</span>
                        <span className="text-gray-600">{count} records</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${(count / labelStats.total_records) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Footer Actions */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-6 py-3 rounded-lg border-2 border-gray-300 text-gray-700 hover:bg-gray-50 transition-all font-medium"
        >
          Back to Dataset Selection
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchLabelStatistics}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onComplete}
            disabled={!labelStats || labelStats.progress_percentage < 80}
            className="px-6 py-3 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continue to ML Prep
          </button>
        </div>
      </div>
    </div>
  );
}
