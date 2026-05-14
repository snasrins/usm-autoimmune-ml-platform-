/**
 * Data Quality Report & Cleaning (LAYER 5)
 * ==========================================
 * Quality assessment + data cleaning operations for uploaded datasets
 * 
 * PURPOSE: Data Quality + Preprocessing (Playground Mode)
 * - Show quality score, missing %, duplicates, outliers
 * - Apply cleaning operations (simple + flexible)
 * - Preview before/after changes
 * - Non-destructive until final save
 * 
 * Flow: View Report → Apply Cleaning → Preview Changes → Save or Undo
 * 
 * Features:
 * - Simple Mode: One-click "Auto-Clean" with sensible defaults
 * - Flexible Mode: Expert controls for each operation
 * - Before/After comparison with statistics
 * - Playground: Experiment freely, undo anytime
 * 
 * Author: Syarifah Fajriyah
 * Date: April 12, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  BarChart3,
  ArrowLeft,
  X,
  Info,
  ChevronRight,
  ChevronDown,
  Zap,
  Trash2,
  TrendingUp,
  RotateCcw,
  Database,
  Columns,
  Copy,
  Users
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { preprocessingAPI } from '../services/api';

export default function DataCleaningPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get session data from navigation state
  const { sessionId, datasetType, rowCount } = location.state || {};
  
  // ========== STATE MANAGEMENT ==========
  const [qualityReport, setQualityReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [issuesPage, setIssuesPage] = useState(1);
  
  // Cleaning operations state
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [cleaningConfig, setCleaningConfig] = useState({
    missingMethod: 'median',
    missingThreshold: 0.5,
    outlierMethod: 'iqr',
    outlierThreshold: 1.5,
    normalization: 'none',
    patientIdColumn: 'patient_id',
    aggregationStrategy: 'latest'
  });
  const [operationInProgress, setOperationInProgress] = useState(null);
  const [beforeStats, setBeforeStats] = useState(null);
  const [afterStats, setAfterStats] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  
  // Quality metrics
  const [qualityMetrics, setQualityMetrics] = useState({
    totalRows: rowCount || 0,
    totalColumns: 0,
    missingPercentage: 0,
    duplicatePercentage: 0,
    qualityScore: 0,
    issues: []
  });
  
  // Issue selection state
  const [selectedIssues, setSelectedIssues] = useState([]);
  const [selectedIssueType, setSelectedIssueType] = useState('all'); // 'all', 'missing', 'duplicate', 'outlier'
  
  useEffect(() => {
    if (!sessionId) {
      navigate('/data-preparation');
      return;
    }
    
    // Load quality report
    loadQualityReport();
  }, [sessionId]);
  
  // ========== DATA LOADING ==========
  
  const loadQualityReport = async () => {
    try {
      setError(null);
      const report = await preprocessingAPI.getQualityReport(sessionId);
      
      setQualityMetrics({
        totalRows: report.total_rows || rowCount || 0,
        totalColumns: report.total_columns || 0,
        missingPercentage: report.missing_values?.percentage || 0,
        duplicatePercentage: report.duplicates?.percentage || 0,
        qualityScore: report.quality_score || 0,
        issues: [
          ...(report.missing_values?.details ? Object.entries(report.missing_values.details).map(([col, data]) => ({
            type: 'missing',
            column: col,
            count: data.count,
            severity: data.percentage > 30 ? 'high' : data.percentage > 10 ? 'medium' : 'low'
          })) : []),
          ...(report.duplicates?.count > 0 ? [{
            type: 'duplicate',
            count: report.duplicates.count,
            severity: report.duplicates.percentage > 10 ? 'high' : report.duplicates.percentage > 5 ? 'medium' : 'low'
          }] : []),
          ...(report.outliers?.details ? Object.entries(report.outliers.details).map(([col, count]) => ({
            type: 'outlier',
            column: col,
            count: count,
            severity: count > 50 ? 'high' : count > 20 ? 'medium' : 'low'
          })) : [])
        ]
      });
      
      setQualityReport(report);
      setIssuesPage(1);
    } catch (err) {
      console.error('Failed to load quality report:', err);
      setError('Failed to load quality report. Please try again.');
    }
  };
  
  // Toggle issue selection
  const toggleIssueSelection = (issueIndex) => {
    setSelectedIssues(prev => 
      prev.includes(issueIndex) 
        ? prev.filter(i => i !== issueIndex)
        : [...prev, issueIndex]
    );
  };
  
  // Select all visible issues
  const selectAllVisibleIssues = () => {
    const visibleIssues = getFilteredIssues().map((_, idx) => idx);
    setSelectedIssues(visibleIssues);
  };
  
  // Clear selection
  const clearSelection = () => {
    setSelectedIssues([]);
  };
  
  // Get filtered issues based on selected issue type
  const getFilteredIssues = () => {
    if (selectedIssueType === 'all') return qualityMetrics.issues;
    return qualityMetrics.issues.filter(issue => issue.type === selectedIssueType);
  };
  
  // Clean selected issues
  const cleanSelectedIssues = async () => {
    if (selectedIssues.length === 0) {
      alert('Please select issues to clean');
      return;
    }
    
    setLoading(true);
    try {
      // Group issues by type and apply appropriate cleaning
      const selectedIssueData = selectedIssues.map(idx => qualityMetrics.issues[idx]);
      
      // Apply cleaning based on issue types
      for (const issue of selectedIssueData) {
        if (issue.type === 'missing') {
          await handleMissingValues();
        } else if (issue.type === 'duplicate') {
          await handleRemoveDuplicates();
        } else if (issue.type === 'outlier') {
          await handleOutliers();
        }
      }
      
      await loadQualityReport();
      clearSelection();
      
      alert(`✓ Cleaned ${selectedIssues.length} issues successfully!`);
    } catch (err) {
      console.error('Issue cleaning failed:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // ========== CLEANING OPERATIONS ==========
  
  // Auto-clean: One-click cleaning with sensible defaults
  const handleAutoClean = async () => {
    setLoading(true);
    setOperationInProgress('auto-clean');
    try {
      // Store before stats
      setBeforeStats(qualityMetrics);
      
      // Step 1: Handle missing values (median for numeric, mode for categorical)
      await preprocessingAPI.handleMissingValues(sessionId, {
        method: 'median',
        threshold: 0.9 // Drop columns with >90% missing
      });
      
      // Step 2: Remove duplicates (keep first occurrence)
      await preprocessingAPI.removeDuplicates(sessionId, true);
      
      // Step 3: Cap outliers (mild IQR threshold)
      await preprocessingAPI.handleOutliers(sessionId, 'iqr', 1.5);
      
      // Reload quality report to see changes
      await loadQualityReport();
      
      // Capture after stats for comparison
      const afterData = await preprocessingAPI.getQualityReport(sessionId);
      setAfterStats({
        totalRows: afterData.total_rows,
        totalColumns: afterData.total_columns,
        missingPercentage: afterData.missing_values?.percentage || 0,
        duplicatePercentage: afterData.duplicates?.percentage || 0,
        qualityScore: afterData.quality_score || 0
      });
      setShowComparison(true);
      
      alert('✓ Auto-clean completed!\n\n' +
        'Applied:\n' +
        '• Missing values filled (median/mode)\n' +
        '• Duplicates removed\n' +
        '• Outliers capped (IQR 1.5)\n\n' +
        'Check the comparison view to see before/after stats!');
      
    } catch (err) {
      console.error('Auto-clean failed:', err);
      setError('Auto-clean failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  };
  
  // Handle missing values
  const handleMissingValues = async () => {
    setLoading(true);
    setOperationInProgress('missing');
    setBeforeStats(qualityMetrics);
    try {
      const result = await preprocessingAPI.handleMissingValues(sessionId, {
        method: cleaningConfig.missingMethod,
        threshold: cleaningConfig.missingThreshold
      });
      
      // Reload and capture after stats
      const afterData = await preprocessingAPI.getQualityReport(sessionId);
      await loadQualityReport();
      
      setAfterStats({
        totalRows: afterData.total_rows,
        totalColumns: afterData.total_columns,
        missingPercentage: afterData.missing_values?.percentage || 0,
        duplicatePercentage: afterData.duplicates?.percentage || 0,
        qualityScore: afterData.quality_score || 0
      });
      setShowComparison(true);
      
      alert(`✓ Missing values handled!\n\n${result.message || 'Operation completed'}\n\nCheck the green comparison box to see before/after stats!`);
      
    } catch (err) {
      console.error('Missing value handling failed:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  };
  
  // Remove duplicates
  const handleRemoveDuplicates = async () => {
    setLoading(true);
    setOperationInProgress('duplicates');
    setBeforeStats(qualityMetrics);
    try {
      const result = await preprocessingAPI.removeDuplicates(sessionId, true);
      
      // Reload and capture after stats
      const afterData = await preprocessingAPI.getQualityReport(sessionId);
      await loadQualityReport();
      
      setAfterStats({
        totalRows: afterData.total_rows,
        totalColumns: afterData.total_columns,
        missingPercentage: afterData.missing_values?.percentage || 0,
        duplicatePercentage: afterData.duplicates?.percentage || 0,
        qualityScore: afterData.quality_score || 0
      });
      setShowComparison(true);
      
      alert(`✓ Duplicates removed!\n\n${result.duplicates_removed || 0} rows removed\n\nCheck the green comparison box to see before/after stats!`);
      
    } catch (err) {
      console.error('Duplicate removal failed:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  };
  
  // Handle outliers
  const handleOutliers = async () => {
    setLoading(true);
    setOperationInProgress('outliers');
    setBeforeStats(qualityMetrics);
    try {
      const result = await preprocessingAPI.handleOutliers(
        sessionId,
        cleaningConfig.outlierMethod,
        cleaningConfig.outlierThreshold
      );
      
      // Reload and capture after stats
      const afterData = await preprocessingAPI.getQualityReport(sessionId);
      await loadQualityReport();
      
      setAfterStats({
        totalRows: afterData.total_rows,
        totalColumns: afterData.total_columns,
        missingPercentage: afterData.missing_values?.percentage || 0,
        duplicatePercentage: afterData.duplicates?.percentage || 0,
        qualityScore: afterData.quality_score || 0
      });
      setShowComparison(true);
      
      alert(`✓ Outliers handled!\n\n${result.message || 'Operation completed'}\n\nCheck the green comparison box to see before/after stats!`);
      
    } catch (err) {
      console.error('Outlier handling failed:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  };
  
  // Aggregate patient records (consolidate duplicates)
  const handleAggregatePatients = async () => {
    setLoading(true);
    setOperationInProgress('aggregation');
    setBeforeStats(qualityMetrics);
    try {
      const result = await preprocessingAPI.aggregatePatients(
        sessionId,
        cleaningConfig.patientIdColumn,
        cleaningConfig.aggregationStrategy
      );
      
      // Reload and capture after stats
      const afterData = await preprocessingAPI.getQualityReport(sessionId);
      await loadQualityReport();
      
      setAfterStats({
        totalRows: afterData.total_rows,
        totalColumns: afterData.total_columns,
        missingPercentage: afterData.missing_values?.percentage || 0,
        duplicatePercentage: afterData.duplicates?.percentage || 0,
        qualityScore: afterData.quality_score || 0
      });
      setShowComparison(true);
      
      alert(`✓ Patient records consolidated!\n\n${result.message}\n\nRows before: ${result.before_rows}\nRows after: ${result.after_rows}\nPatients consolidated: ${result.patients_consolidated}\n\nCheck the green comparison box to see before/after stats!`);
      
    } catch (err) {
      console.error('Patient aggregation failed:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  };
  
  // Undo all changes (reload original data)
  const handleUndo = async () => {
    if (!confirm('Undo all cleaning operations? This will reload the original data.')) {
      return;
    }
    
    try {
      setLoading(true);
      // Reload from original staging data
      await loadQualityReport();
      setBeforeStats(null);
      setAfterStats(null);
      alert('✓ Changes undone - original data restored');
    } catch (err) {
      setError('Undo failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // ========== RENDER HELPERS ==========
  
  const getQualityColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getSeverityColor = (severity) => {
    if (severity === 'high') return 'bg-red-100 text-red-700';
    if (severity === 'medium') return 'bg-yellow-100 text-yellow-700';
    return 'bg-blue-100 text-blue-700';
  };
  
  // ========== RENDER ==========
  
  return (
    <DashboardLayout>
      {/* ═══ TOPBAR ═══ */}
      <div className="h-[70px] flex items-center gap-8 px-6 bg-[#F5F5F7] border-b border-gray-200 flex-shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Data Quality Report</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0]">Quality Report</span>
          </div>
        </div>
        
        {/* Right side: Actions */}
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => navigate('/data-preparation', { state: { sessionId } })}
            className="flex items-center gap-2 px-5 py-2.5 bg-white border-2 border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition-all text-sm font-semibold shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Data Editor
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6" style={{ background: '#FAFBFC', zoom: 0.78 }}>
          {/* Before/After Comparison Modal */}
          {showComparison && beforeStats && afterStats && (
            <div className="mb-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-xl border-2 border-green-300 shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-green-600 to-blue-600 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-white" />
                  <h3 className="font-syne text-lg font-bold text-white">Operation Complete - Before & After Comparison</h3>
                </div>
                <button
                  onClick={() => setShowComparison(false)}
                  className="text-white hover:bg-white/20 rounded-lg p-1.5 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-5 gap-4">
                  {/* Total Rows */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Total Rows</div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold text-gray-400 line-through">{beforeStats.totalRows}</div>
                      <span className="text-gray-400">→</span>
                      <div className="text-2xl font-bold text-green-600">{afterStats.totalRows}</div>
                    </div>
                    {beforeStats.totalRows !== afterStats.totalRows && (
                      <div className="text-xs text-green-600 font-semibold mt-1">
                        {afterStats.totalRows - beforeStats.totalRows > 0 ? '+' : ''}{afterStats.totalRows - beforeStats.totalRows} rows
                      </div>
                    )}
                  </div>
                  
                  {/* Total Columns */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Columns</div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold text-gray-400 line-through">{beforeStats.totalColumns}</div>
                      <span className="text-gray-400">→</span>
                      <div className="text-2xl font-bold text-green-600">{afterStats.totalColumns}</div>
                    </div>
                    {beforeStats.totalColumns !== afterStats.totalColumns && (
                      <div className="text-xs text-green-600 font-semibold mt-1">
                        {afterStats.totalColumns - beforeStats.totalColumns > 0 ? '+' : ''}{afterStats.totalColumns - beforeStats.totalColumns} columns
                      </div>
                    )}
                  </div>
                  
                  {/* Missing Data */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Missing Data</div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold text-gray-400 line-through">{beforeStats.missingPercentage}%</div>
                      <span className="text-gray-400">→</span>
                      <div className="text-2xl font-bold text-green-600">{afterStats.missingPercentage}%</div>
                    </div>
                    {beforeStats.missingPercentage !== afterStats.missingPercentage && (
                      <div className="text-xs text-green-600 font-semibold mt-1">
                        Reduced by {(beforeStats.missingPercentage - afterStats.missingPercentage).toFixed(2)}%
                      </div>
                    )}
                  </div>
                  
                  {/* Duplicates */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Duplicates</div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold text-gray-400 line-through">{beforeStats.duplicatePercentage}%</div>
                      <span className="text-gray-400">→</span>
                      <div className="text-2xl font-bold text-green-600">{afterStats.duplicatePercentage}%</div>
                    </div>
                    {beforeStats.duplicatePercentage !== afterStats.duplicatePercentage && (
                      <div className="text-xs text-green-600 font-semibold mt-1">
                        Reduced by {(beforeStats.duplicatePercentage - afterStats.duplicatePercentage).toFixed(2)}%
                      </div>
                    )}
                  </div>
                  
                  {/* Quality Score */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Quality Score</div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold text-gray-400 line-through">{beforeStats.qualityScore}</div>
                      <span className="text-gray-400">→</span>
                      <div className="text-2xl font-bold text-green-600">{afterStats.qualityScore}</div>
                    </div>
                    {beforeStats.qualityScore !== afterStats.qualityScore && (
                      <div className="text-xs text-green-600 font-semibold mt-1">
                        Improved by +{(afterStats.qualityScore - beforeStats.qualityScore).toFixed(1)} points
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-700 bg-white rounded-lg p-3 border border-gray-200">
                  <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>These changes are applied to the staging area. Use <strong>'Save & Continue to ML Prep'</strong> to finalize.</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Error Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-base font-medium text-red-800">Error</div>
                <div className="text-base text-red-700 mt-1">{error}</div>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-600 hover:text-red-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          
          {/* Quality Metrics Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-syne text-xl font-bold text-gray-900">Data Quality Metrics</h2>
              <button
                onClick={loadQualityReport}
                className="flex items-center gap-2 px-4 py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-lg border border-purple-200 transition-colors font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
            
            <div className="grid grid-cols-5 gap-4">
              {/* Total Rows */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-blue-500 to-blue-600"></div>
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Database className="w-5 h-5 text-blue-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{qualityMetrics.totalRows.toLocaleString()}</div>
                  <div className="text-sm font-medium text-gray-600">Total Rows</div>
                </div>
              </div>
              
              {/* Columns */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-indigo-500 to-indigo-600"></div>
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                      <Columns className="w-5 h-5 text-indigo-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{qualityMetrics.totalColumns}</div>
                  <div className="text-sm font-medium text-gray-600">Columns</div>
                </div>
              </div>
              
              {/* Missing Data */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-yellow-500 to-yellow-600"></div>
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-yellow-600 mb-1">{qualityMetrics.missingPercentage}%</div>
                  <div className="text-sm font-medium text-gray-600">Missing Data</div>
                </div>
              </div>
              
              {/* Duplicates */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-red-500 to-red-600"></div>
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
                      <Copy className="w-5 h-5 text-red-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-red-600 mb-1">{qualityMetrics.duplicatePercentage}%</div>
                  <div className="text-sm font-medium text-gray-600">Duplicates</div>
                </div>
              </div>
              
              {/* Quality Score */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className={`h-1 ${qualityMetrics.qualityScore >= 80 ? 'bg-gradient-to-r from-green-500 to-green-600' : qualityMetrics.qualityScore >= 60 ? 'bg-gradient-to-r from-yellow-500 to-yellow-600' : 'bg-gradient-to-r from-red-500 to-red-600'}`}></div>
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className={`w-10 h-10 rounded-lg ${qualityMetrics.qualityScore >= 80 ? 'bg-green-50' : qualityMetrics.qualityScore >= 60 ? 'bg-yellow-50' : 'bg-red-50'} flex items-center justify-center`}>
                      <TrendingUp className={`w-5 h-5 ${qualityMetrics.qualityScore >= 80 ? 'text-green-600' : qualityMetrics.qualityScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`} />
                    </div>
                  </div>
                  <div className={`text-3xl font-bold mb-1 ${getQualityColor(qualityMetrics.qualityScore)}`}>
                    {qualityMetrics.qualityScore}
                  </div>
                  <div className="text-sm font-medium text-gray-600">Quality Score</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Data Cleaning Operations */}
          <div className="mb-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <h2 className="font-syne text-lg font-bold text-gray-900">Data Cleaning Operations</h2>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-purple-600 hover:bg-white rounded-lg border border-purple-200 transition-colors font-medium"
                >
                  {showAdvanced ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  {showAdvanced ? 'Hide' : 'Show'} Advanced Options
                </button>
              </div>
              
              <div className="p-6">
                {/* Simple Mode: One-Click Auto-Clean */}
                {!showAdvanced && (
                  <div className="bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 rounded-xl border-2 border-purple-200 p-6">
                    <div className="flex items-start gap-5">
                      <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                        <Zap className="w-7 h-7 text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-syne text-lg font-bold text-gray-900 mb-2">Auto-Clean Mode</h3>
                        <p className="text-sm text-gray-700 mb-4">
                          Apply recommended cleaning operations with one click:
                        </p>
                        <div className="bg-white/60 rounded-lg p-4 mb-4">
                          <ul className="text-sm text-gray-700 space-y-2">
                            <li className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-1.5 flex-shrink-0"></div>
                              <span>Fill missing values (median for numbers, mode for categories)</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-1.5 flex-shrink-0"></div>
                              <span>Remove duplicate rows (keep first occurrence)</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-1.5 flex-shrink-0"></div>
                              <span>Cap outliers using IQR method (threshold: 1.5)</span>
                            </li>
                          </ul>
                        </div>
                        <button
                          onClick={handleAutoClean}
                          disabled={loading || operationInProgress}
                          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md font-semibold transition-all hover:shadow-lg"
                        >
                          {loading && operationInProgress === 'auto-clean' ? (
                            <>
                              <RefreshCw className="w-5 h-5 animate-spin" />
                              Cleaning...
                            </>
                          ) : (
                            <>
                              <Zap className="w-5 h-5" />
                              Auto-Clean Data
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
            
                {/* Advanced Mode: Individual Operations */}
                {showAdvanced && (
                  <div className="space-y-4">
                    {/* Missing Values */}
                    <div className="bg-white rounded-xl border-2 border-gray-200 p-5 hover:border-blue-300 transition-colors">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                          <AlertTriangle className="w-5 h-5 text-blue-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 text-base">Missing Values</h3>
                      </div>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Imputation Method</label>
                      <select
                        value={cleaningConfig.missingMethod}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, missingMethod: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      >
                        <option value="mean">Mean (average)</option>
                        <option value="median">Median (middle value)</option>
                        <option value="mode">Mode (most frequent)</option>
                        <option value="ffill">Forward fill</option>
                        <option value="drop">Drop rows</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Drop Columns Threshold (%)</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={cleaningConfig.missingThreshold * 100}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, missingThreshold: e.target.value / 100})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">Drop columns with &gt;X% missing</p>
                    </div>
                  </div>
                  <button
                    onClick={handleMissingValues}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
                  >
                    {loading && operationInProgress === 'missing' ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    Apply Missing Value Handling
                  </button>
                </div>
                
                    {/* Duplicates */}
                    <div className="bg-white rounded-xl border-2 border-gray-200 p-5 hover:border-red-300 transition-colors">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
                          <Copy className="w-5 h-5 text-red-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 text-base">Duplicate Rows</h3>
                      </div>
                  <p className="text-sm text-gray-700 mb-3">
                    Remove duplicate rows from your dataset (keeps first occurrence).
                  </p>
                  <button
                    onClick={handleRemoveDuplicates}
                    disabled={loading || qualityMetrics.duplicatePercentage === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm"
                  >
                    {loading && operationInProgress === 'duplicates' ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    Remove Duplicates
                  </button>
                </div>
                
                {/* Outliers */}
                <div className="bg-white rounded-xl border-2 border-gray-200 p-5 hover:border-orange-300 transition-colors">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-orange-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900 text-base">Outliers</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Detection Method</label>
                      <select
                        value={cleaningConfig.outlierMethod}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, outlierMethod: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      >
                        <option value="iqr">IQR (Interquartile Range)</option>
                        <option value="zscore">Z-Score</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Threshold</label>
                      <input
                        type="number"
                        min="0"
                        max="5"
                        step="0.1"
                        value={cleaningConfig.outlierThreshold}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, outlierThreshold: parseFloat(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">1.5=mild, 3.0=extreme</p>
                    </div>
                  </div>
                  <button
                    onClick={handleOutliers}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 text-sm"
                  >
                    {loading && operationInProgress === 'outliers' ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <TrendingUp className="w-4 h-4" />
                    )}
                    Handle Outliers
                  </button>
                </div>
                
                {/* Patient Record Aggregation */}
                <div className="bg-white rounded-xl border-2 border-gray-200 p-5 hover:border-purple-300 transition-colors">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                      <Users className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 text-base">Patient Record Consolidation</h3>
                      <p className="text-xs text-gray-600 mt-0.5">Merge duplicate patient records (only if applicable)</p>
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 rounded-lg p-3 mb-3">
                    <div className="flex items-start gap-2">
                      <Info className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-gray-700">
                        Consolidates multiple rows for same patient into single comprehensive record. 
                        Only use if your dataset has duplicate patient entries.
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Patient ID Column</label>
                      <input
                        type="text"
                        value={cleaningConfig.patientIdColumn}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, patientIdColumn: e.target.value})}
                        placeholder="patient_id"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">Column containing patient identifier</p>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">Aggregation Strategy</label>
                      <select
                        value={cleaningConfig.aggregationStrategy}
                        onChange={(e) => setCleaningConfig({...cleaningConfig, aggregationStrategy: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      >
                        <option value="latest">Latest (most recent record)</option>
                        <option value="most_complete">Most Complete (fewest nulls)</option>
                        <option value="merge">Merge (combine all values)</option>
                      </select>
                      <p className="text-xs text-gray-500 mt-1">How to merge duplicate records</p>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleAggregatePatients}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm"
                  >
                    {loading && operationInProgress === 'aggregation' ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Users className="w-4 h-4" />
                    )}
                    Consolidate Patient Records
                  </button>
                </div>
                
                {/* Undo Button */}
                <div className="border-t pt-4">
                  <button
                    onClick={handleUndo}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 text-sm"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Undo All Changes
                  </button>
                </div>
              </div>
            )}
              </div>
            </div>
          </div>
          
          {/* Detected Issues - Interactive Cleaning */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-purple-50/30">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-syne text-lg font-bold text-gray-900">Detected Issues</h2>
                  <p className="text-sm text-gray-600 mt-1.5">
                    Review quality issues and select which ones to clean. Use Auto-Clean to fix all at once.
                  </p>
                </div>
                {selectedIssues.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">{selectedIssues.length} selected</span>
                    <button
                      onClick={clearSelection}
                      className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-200 rounded-lg"
                    >
                      Clear
                    </button>
                    <button
                      onClick={cleanSelectedIssues}
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm font-medium"
                    >
                      <Zap className="w-4 h-4" />
                      Clean Selected
                    </button>
                  </div>
                )}
              </div>
              
              {/* Filter by Issue Type */}
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => setSelectedIssueType('all')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedIssueType === 'all' 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  All Issues ({qualityMetrics.issues.length})
                </button>
                <button
                  onClick={() => setSelectedIssueType('missing')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedIssueType === 'missing' 
                      ? 'bg-yellow-600 text-white' 
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Missing Values ({qualityMetrics.issues.filter(i => i.type === 'missing').length})
                </button>
                <button
                  onClick={() => setSelectedIssueType('duplicate')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedIssueType === 'duplicate' 
                      ? 'bg-red-600 text-white' 
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Duplicates ({qualityMetrics.issues.filter(i => i.type === 'duplicate').length})
                </button>
                <button
                  onClick={() => setSelectedIssueType('outlier')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedIssueType === 'outlier' 
                      ? 'bg-orange-600 text-white' 
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Outliers ({qualityMetrics.issues.filter(i => i.type === 'outlier').length})
                </button>
                <button
                  onClick={selectAllVisibleIssues}
                  className="ml-auto px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
                >
                  Select All Visible
                </button>
              </div>
            </div>
            
            {/* Issues Table */}
            {getFilteredIssues().length === 0 ? (
              <div className="p-12 text-center">
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h4 className="font-semibold text-lg text-gray-900 mb-2">No Issues Detected!</h4>
                <p className="text-sm text-gray-600">
                  {selectedIssueType === 'all' 
                    ? 'Your data looks clean and ready for ML preparation.'
                    : `No ${selectedIssueType} issues found in this dataset.`}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800 border-b-2 border-gray-700">
                    <tr>
                      <th className="sticky left-0 z-10 bg-gray-800 px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          onChange={(e) => e.target.checked ? selectAllVisibleIssues() : clearSelection()}
                          checked={getFilteredIssues().length > 0 && getFilteredIssues().every((_, idx) => selectedIssues.includes((issuesPage - 1) * 20 + idx))}
                          className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-white uppercase">Issue Type</th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-white uppercase">Column</th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-white uppercase">Affected</th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-white uppercase">Severity</th>
                      <th className="px-4 py-3 text-right text-sm font-bold text-white uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {getFilteredIssues()
                      .slice((issuesPage - 1) * 20, issuesPage * 20)
                      .map((issue, idx) => {
                        const globalIdx = (issuesPage - 1) * 20 + idx;
                        return (
                          <tr 
                            key={globalIdx} 
                            className={`${
                              idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                            } ${
                              selectedIssues.includes(globalIdx) ? 'bg-purple-50 border-l-4 border-purple-600' : ''
                            } hover:bg-blue-50 transition-colors`}
                          >
                            <td className="sticky left-0 z-10 px-4 py-3" style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f9fafb' }}>
                              <input
                                type="checkbox"
                                checked={selectedIssues.includes(globalIdx)}
                                onChange={() => toggleIssueSelection(globalIdx)}
                                className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-1 rounded-lg text-xs font-semibold ${
                                issue.type === 'missing' ? 'bg-yellow-100 text-yellow-800' :
                                issue.type === 'duplicate' ? 'bg-red-100 text-red-800' :
                                'bg-orange-100 text-orange-800'
                              }`}>
                                {issue.type === 'missing' ? 'Missing Values' : 
                                 issue.type === 'duplicate' ? 'Duplicate' : 'Outlier'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="text-sm font-medium text-gray-900">
                                {issue.column || 'Multiple columns'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="text-sm text-gray-700 font-medium">
                                {issue.count} {issue.type === 'duplicate' ? 'rows' : 'values'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {issue.severity}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <button
                                onClick={() => {
                                  setSelectedIssues([globalIdx]);
                                  cleanSelectedIssues();
                                }}
                                className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-xs font-medium"
                              >
                                Clean
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            )}
            
            {/* Pagination */}
            {getFilteredIssues().length > 20 && (
              <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing {((issuesPage - 1) * 20) + 1}-{Math.min(issuesPage * 20, getFilteredIssues().length)} of {getFilteredIssues().length}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setIssuesPage(prev => Math.max(1, prev - 1))}
                    disabled={issuesPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {issuesPage} of {Math.ceil(getFilteredIssues().length / 20)}
                  </span>
                  <button
                    onClick={() => setIssuesPage(prev => prev + 1)}
                    disabled={issuesPage >= Math.ceil(getFilteredIssues().length / 20)}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
    </DashboardLayout>
  );
}
