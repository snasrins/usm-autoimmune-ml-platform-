import { useState, useEffect } from 'react';
import {
  Tag,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Play,
  RefreshCw,
  Trash2,
  Plus,
  Eye,
  HelpCircle,
  BarChart3,
  Lightbulb,
  ArrowRight,
  X,
  Database,
  Settings,
  Target
} from 'lucide-react';
import { labelingAPI, mlAPI } from '../services/api';

export default function RuleBasedLabelingWorkflow({ batchId, targetColumn: propTargetColumn, onComplete, onBack }) {
  console.log('[RuleBasedLabeling] Component render - batchId:', batchId, 'targetColumn:', propTargetColumn);
  
  // Core state
  const [loading, setLoading] = useState(false);
  const [fetchingStats, setFetchingStats] = useState(true);
  const [sourceColumn, setSourceColumn] = useState('SLEDAI');
  const [targetColumn, setTargetColumn] = useState(propTargetColumn || 'labels_disease_classification');
  const [rules, setRules] = useState([
    { condition: '< 4', label: 'Mild', description: 'Low disease activity' },
    { condition: '>= 4 and <= 12', label: 'Moderate', description: 'Moderate disease activity' },
    { condition: '> 12', label: 'Severe', description: 'High disease activity' }
  ]);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  
  // Results & Statistics
  const [labelingResults, setLabelingResults] = useState(null);
  const [labelStats, setLabelStats] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // Available columns (fetch from API)
  const [availableColumns, setAvailableColumns] = useState([]);
  const [fetchingColumns, setFetchingColumns] = useState(false);

  // Fetch available columns on mount
  useEffect(() => {
    if (batchId) {
      console.log('[RuleBasedLabeling] Component mounted with batchId:', batchId);
      fetchAvailableColumns();
      fetchLabelStatistics();
    } else {
      console.warn('[RuleBasedLabeling] Component mounted without batchId');
    }
  }, [batchId]);

  const fetchAvailableColumns = async () => {
    setFetchingColumns(true);
    console.log('[RuleBasedLabeling] Fetching columns for batchId:', batchId);
    try {
      // Fetch a sample record from this batch to extract actual Excel column names
      // getUnlabeledRecords(datasetType, batchId, limit, offset, targetColumn)
      const unlabeledResponse = await labelingAPI.getUnlabeledRecords(null, batchId, 1, 0, 'labels_disease_classification');
      console.log('[RuleBasedLabeling] Sample record response:', unlabeledResponse);
      console.log('[RuleBasedLabeling] Total records available:', unlabeledResponse.total);
      
      if (unlabeledResponse.unlabeled_records && unlabeledResponse.unlabeled_records.length > 0) {
        const sampleRecord = unlabeledResponse.unlabeled_records[0];
        console.log('[RuleBasedLabeling] Sample record structure:', sampleRecord);
        
        const sampleData = sampleRecord.data || {};
        console.log('[RuleBasedLabeling] Sample data object:', sampleData);
        console.log('[RuleBasedLabeling] Sample data type:', typeof sampleData);
        console.log('[RuleBasedLabeling] Top-level keys:', Object.keys(sampleData));
        
        // Recursively extract all column paths (including nested ones)
        const allColumns = [];
        
        const extractColumns = (obj, prefix = '') => {
          if (!obj || typeof obj !== 'object') return;
          
          Object.keys(obj).forEach(key => {
            if (key.startsWith('_')) return; // Skip metadata
            
            const fullPath = prefix ? `${prefix}.${key}` : key;
            const value = obj[key];
            
            if (value && typeof value === 'object' && !Array.isArray(value)) {
              // It's a nested object - recurse into it
              extractColumns(value, fullPath);
            } else {
              // It's a leaf value (string, number, etc.) - this is an actual column
              allColumns.push(fullPath);
            }
          });
        };
        
        extractColumns(sampleData);
        
        console.log('[RuleBasedLabeling] All columns found (including nested):', allColumns);
        console.log('[RuleBasedLabeling] Number of columns:', allColumns.length);
        
        if (allColumns.length > 0) {
          // Sort with common lab values first
          const priorityColumns = ['C3', 'C4', 'SLEDAI', 'CRP', 'ESR'];
          const sorted = [
            ...allColumns.filter(col => priorityColumns.some(p => col.includes(p))),
            ...allColumns.filter(col => !priorityColumns.some(p => col.includes(p)))
          ].sort();
          
          setAvailableColumns(sorted);
          console.log('[RuleBasedLabeling] ✓ Set availableColumns state to:', sorted);
          
          // Set first column as default if current sourceColumn isn't in the list
          if (!sorted.includes(sourceColumn) && sorted.length > 0) {
            setSourceColumn(sorted[0]);
          }
        } else {
          console.warn('[RuleBasedLabeling] ⚠ No columns found in data, using fallback');
          setAvailableColumns(['SLEDAI', 'CRP', 'ESR', 'Age', 'Gender']);
        }
      } else {
        console.warn('[RuleBasedLabeling] ⚠ No records found in batch, using fallback');
        setAvailableColumns(['SLEDAI', 'CRP', 'ESR', 'Age', 'Gender']);
      }
    } catch (error) {
      console.error('[RuleBasedLabeling] ❌ Failed to fetch columns:', error);
      setAvailableColumns(['SLEDAI', 'CRP', 'ESR', 'Age', 'Gender']);
    } finally {
      setFetchingColumns(false);
    }
  };

  const fetchLabelStatistics = async () => {
    setFetchingStats(true);
    try {
      const stats = await labelingAPI.getLabelStatistics(null, batchId, targetColumn);
      console.log('[RuleBasedLabeling] Statistics fetched:', stats);
      setLabelStats(stats);
    } catch (error) {
      console.error('Failed to fetch label statistics:', error);
      // Set default empty stats to prevent undefined errors
      setLabelStats({
        total_records: 0,
        labeled_records: 0,
        unlabeled_records: 0,
        labeling_progress: 0,
        labels: {},
        confidence_distribution: {}
      });
    } finally {
      setFetchingStats(false);
    }
  };

  const addRule = () => {
    setRules([...rules, { condition: '', label: '', description: '' }]);
  };

  const updateRule = (index, field, value) => {
    const newRules = [...rules];
    newRules[index][field] = value;
    setRules(newRules);
  };

  const deleteRule = (index) => {
    if (rules.length > 1) {
      setRules(rules.filter((_, i) => i !== index));
    }
  };

  const handleRunLabeling = async () => {
    // Validate inputs
    if (!sourceColumn) {
      alert('Please select a source column');
      return;
    }
    
    if (rules.length === 0 || rules.some(r => !r.condition || !r.label)) {
      alert('Please define at least one complete rule (condition + label)');
      return;
    }

    setLoading(true);
    try {
      const result = await labelingAPI.ruleBasedLabel(
        batchId,
        sourceColumn,
        rules.filter(r => r.condition && r.label), // Only send complete rules
        targetColumn,
        overwriteExisting
      );
      
      setLabelingResults(result);
      
      // Refresh statistics
      await fetchLabelStatistics();
      
      setLoading(false);
      
      // Show success message
      alert(`Labeling Complete!\n\n` +
            `${result.labeled_count} records labeled\n` +
            `${result.skipped_count} records skipped\n` +
            `${result.error_count} errors`);
      
      // Notify parent component to refresh its statistics
      // Pass the targetColumn that was actually used for labeling
      if (onComplete) {
        onComplete(targetColumn);
      }
    } catch (error) {
      console.error('Rule-based labeling failed:', error);
      setLoading(false);
      alert('Labeling failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const loadPreset = (presetName) => {
    const presets = {
      disease_classification: {
        sourceColumn: 'SLEDAI',
        targetColumn: 'labels_disease_classification',
        rules: [
          { condition: '<= 4', label: 'Inactive', description: 'Inactive or minimal disease activity' },
          { condition: '> 4 and <= 10', label: 'Mild', description: 'Mild disease activity' },
          { condition: '> 10 and <= 20', label: 'Moderate', description: 'Moderate disease activity' },
          { condition: '> 20', label: 'Severe', description: 'Severe disease activity' }
        ]
      },
      severity_sledai: {
        sourceColumn: 'SLEDAI',
        targetColumn: 'labels_disease_severity',
        rules: [
          { condition: '< 4', label: 'Mild', description: 'Low disease activity (SLEDAI ≤4)' },
          { condition: '>= 4 and <= 12', label: 'Moderate', description: 'Moderate disease activity (SLEDAI 5-12)' },
          { condition: '> 12', label: 'Severe', description: 'High disease activity (SLEDAI >12)' }
        ]
      },
      activity_status: {
        sourceColumn: 'SLEDAI',
        targetColumn: 'labels_disease_activity',
        rules: [
          { condition: '== 0', label: 'Remission', description: 'No disease activity' },
          { condition: '> 0 and <= 10', label: 'Active', description: 'Active disease' },
          { condition: '> 10', label: 'Flare', description: 'Disease flare' }
        ]
      },
      crp_inflammation: {
        sourceColumn: 'CRP',
        targetColumn: 'labels_inflammation',
        rules: [
          { condition: '<= 10', label: 'Normal', description: 'Normal CRP levels' },
          { condition: '> 10 and <= 50', label: 'Elevated', description: 'Mild inflammation' },
          { condition: '> 50', label: 'High', description: 'Significant inflammation' }
        ]
      }
    };

    const preset = presets[presetName];
    if (preset) {
      setSourceColumn(preset.sourceColumn);
      setTargetColumn(preset.targetColumn);
      setRules(preset.rules);
    }
  };

  // Guard clause: if no batchId, show message
  if (!batchId) {
    return (
      <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-12 text-center">
        <AlertCircle className="w-12 h-12 text-amber-600 mx-auto mb-4" />
        <h3 className="font-syne text-lg font-bold text-gray-900 mb-2">No Batch Selected</h3>
        <p className="text-sm text-gray-600">Please select a dataset batch to begin labeling.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-syne text-2xl font-bold text-black-text">Rule-Based Labeling</h2>
                <p className="text-sm text-gray-600">Define flexible rules to automatically label your dataset</p>
              </div>
            </div>
          </div>
          <button
            onClick={onBack}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Info Banner */}
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold text-sm text-blue-900 mb-1">How it works</h4>
            <ol className="text-xs text-blue-700 leading-relaxed space-y-1">
              <li><strong>1. Select source column:</strong> Choose which column to evaluate (e.g., SLEDAI, CRP)</li>
              <li><strong>2. Define rules:</strong> Create conditions and assign labels (e.g., &lt; 4 = Mild)</li>
              <li><strong>3. Run labeling:</strong> Apply rules to all records automatically</li>
              <li><strong>4. Review results:</strong> Check statistics and proceed to next step</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Quick Preset Templates */}
      <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-amber-600" />
          <h3 className="font-syne text-lg font-bold text-black-text">Quick Start Templates</h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => loadPreset('severity_sledai')}
            className="p-4 rounded-xl border-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50 transition-all text-left"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center mb-2">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
            <div className="font-semibold text-sm text-gray-900">Disease Severity</div>
            <div className="text-xs text-gray-600 mt-1">SLEDAI-based (Mild/Moderate/Severe)</div>
          </button>
          <button
            onClick={() => loadPreset('activity_status')}
            className="p-4 rounded-xl border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 transition-all text-left"
          >
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mb-2">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <div className="font-semibold text-sm text-gray-900">Disease Activity</div>
            <div className="text-xs text-gray-600 mt-1">Remission/Active/Flare status</div>
          </button>
          <button
            onClick={() => loadPreset('crp_inflammation')}
            className="p-4 rounded-xl border-2 border-amber-200 hover:border-amber-400 hover:bg-amber-50 transition-all text-left"
          >
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center mb-2">
              <Sparkles className="w-6 h-6 text-amber-600" />
            </div>
            <div className="font-semibold text-sm text-gray-900">Inflammation Level</div>
            <div className="text-xs text-gray-600 mt-1">CRP-based classification</div>
          </button>
        </div>
      </div>

      {/* Rule Configuration */}
      <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
        <h3 className="font-syne text-lg font-bold text-black-text mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5 text-purple-600" />
          Configure Labeling Rules
        </h3>

        {/* Source & Target Columns */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Source Column <span className="text-red-500">*</span>
            </label>
            <select
              value={sourceColumn}
              onChange={(e) => setSourceColumn(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={fetchingColumns}
            >
              {fetchingColumns ? (
                <option>Loading columns...</option>
              ) : availableColumns.length === 0 ? (
                <option>No columns available</option>
              ) : (
                availableColumns.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))
              )}
            </select>
            <p className="text-xs text-gray-500 mt-1.5">Column to evaluate for rules</p>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Target Column <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="labels_disease_severity"
            />
            <p className="text-xs text-gray-500 mt-1.5">Where to store the label</p>
          </div>
        </div>

        {/* Rules */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-gray-700">Labeling Rules</h4>
            <button
              onClick={addRule}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors text-xs font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Rule
            </button>
          </div>

          {rules.map((rule, index) => (
            <div key={index} className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center font-bold text-purple-700 text-sm">
                {index + 1}
              </div>
              <div className="flex-1 grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Condition</label>
                  <input
                    type="text"
                    value={rule.condition}
                    onChange={(e) => updateRule(index, 'condition', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="< 4"
                  />
                  <p className="text-xs text-gray-500 mt-1">e.g., &lt; 4, &gt;= 4 and &lt;= 12</p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
                  <input
                    type="text"
                    value={rule.label}
                    onChange={(e) => updateRule(index, 'label', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="Mild"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Description (optional)</label>
                  <input
                    type="text"
                    value={rule.description}
                    onChange={(e) => updateRule(index, 'description', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="Low disease activity"
                  />
                </div>
              </div>
              <button
                onClick={() => deleteRule(index)}
                disabled={rules.length === 1}
                className="flex-shrink-0 p-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title="Delete rule"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Operator Reference */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-4">
          <div className="flex items-start gap-2">
            <HelpCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-700">
              <strong>Supported operators:</strong> &lt; &gt; &lt;= &gt;= == != 
              <strong className="ml-2">Logical:</strong> and, or
              <strong className="ml-2">Examples:</strong> "&lt; 4", "&gt;= 4 and &lt;= 12", "== 'Positive'", "!= 0"
            </div>
          </div>
        </div>

        {/* Options */}
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            id="overwrite"
            checked={overwriteExisting}
            onChange={(e) => setOverwriteExisting(e.target.checked)}
            className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
          />
          <label htmlFor="overwrite" className="text-sm text-gray-700">
            Overwrite existing labels (re-label already labeled records)
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunLabeling}
            disabled={loading || !sourceColumn || rules.length === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:shadow-lg transition-all text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Labeling
              </>
            )}
          </button>
          
          {labelingResults && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-50 border border-green-200">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700 font-medium">
                {labelingResults.labeled_count} records labeled
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Statistics */}
      {fetchingStats ? (
        <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-12 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 animate-spin text-purple-600 mr-3" />
          <span className="text-gray-600">Loading statistics...</span>
        </div>
      ) : labelStats && (
        <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
          <h3 className="font-syne text-lg font-bold text-black-text mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
            Labeling Statistics
          </h3>

          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-white/80 rounded-xl p-4 border border-white/40">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-muted uppercase">Total</span>
                <Database className="w-4 h-4 text-purple-primary" />
              </div>
              <div className="font-syne text-2xl font-bold text-black-text">{labelStats.total_records || 0}</div>
            </div>
            <div className="bg-green-50 rounded-xl p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-muted uppercase">Labeled</span>
                <CheckCircle className="w-4 h-4 text-green-600" />
              </div>
              <div className="font-syne text-2xl font-bold text-green-600">{labelStats.labeled_records || 0}</div>
              <div className="text-xs text-gray-muted mt-1">{(labelStats.labeling_progress || 0).toFixed(1)}%</div>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-muted uppercase">Unlabeled</span>
                <AlertCircle className="w-4 h-4 text-amber-600" />
              </div>
              <div className="font-syne text-2xl font-bold text-amber-600">{labelStats.unlabeled_records || 0}</div>
            </div>
            <div className={`rounded-xl p-4 border ${
              (labelStats.labeling_progress || 0) >= 80 ? 'bg-green-50 border-green-200' : 'bg-purple-50 border-purple-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-muted uppercase">Progress</span>
                {(labelStats.labeling_progress || 0) >= 80 ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <Target className="w-4 h-4 text-purple-primary" />
                )}
              </div>
              <div className={`font-syne text-2xl font-bold ${
                (labelStats.labeling_progress || 0) >= 80 ? 'text-green-600' : 'text-purple-primary'
              }`}>
                {(labelStats.labeling_progress || 0).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-muted mt-1">
                {(labelStats.labeling_progress || 0) >= 80 ? 'Ready' : 'Target: 80%'}
              </div>
            </div>
          </div>

          {/* Label Distribution */}
          {labelStats.labels && Object.keys(labelStats.labels).length > 0 && (
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-3">Label Distribution</h4>
              <div className="space-y-2">
                {Object.entries(labelStats.labels)
                  .sort(([, a], [, b]) => b - a)
                  .map(([label, count]) => {
                    const labeledRecords = labelStats.labeled_records || 1; // Avoid division by zero
                    const percentage = ((count / labeledRecords) * 100).toFixed(1);
                    return (
                      <div key={label}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="font-medium text-black-text">{label}</span>
                          <span className="font-bold text-purple-primary">{count} ({percentage}%)</span>
                        </div>
                        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="absolute inset-y-0 left-0 bg-purple-primary rounded-full transition-all"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Action Button */}
          {(labelStats.labeling_progress || 0) >= 80 && (
            <button
              onClick={onComplete}
              className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:shadow-lg transition-all text-sm font-semibold"
            >
              <CheckCircle className="w-4 h-4" />
              Complete Labeling & Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Results Detail */}
      {labelingResults && (
        <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
          <h3 className="font-syne text-lg font-bold text-black-text mb-4">Rule Match Statistics</h3>
          <div className="space-y-2">
            {labelingResults.rule_statistics.map((stat, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-xs font-bold text-purple-700">
                    {stat.rule_index + 1}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {stat.condition} → <span className="text-purple-600">{stat.label}</span>
                    </div>
                  </div>
                </div>
                <div className="text-sm font-bold text-gray-700">
                  {stat.matches} matches
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
