/**
 * Data Quality Detail Page
 * =========================
 * Dedicated page for comprehensive data quality analysis of a single dataset
 * 
 * Features:
 * - Overall quality score with breakdown
 * - Missing values analysis by column
 * - Duplicate detection
 * - Outlier identification
 * - Data type validation
 * - Value range checks
 * - Quality history timeline
 * 
 * Author: Syarifah Fajriyah
 * Date: April 11, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  XCircle,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Download,
  RefreshCw,
  ChevronRight,
  Info,
  BarChart3,
  FileSpreadsheet
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function DataQualityDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // overview, missing, duplicates, outliers, validation
  
  // Mock dataset data (replace with API call)
  const [dataset] = useState({
    id: id,
    name: 'AAM-SLE-E (real data)',
    filename: 'AAM-SLE-E (real data).xlsx',
    rowCount: 1204,
    columnCount: 18,
    qualityScore: 94.2,
    uploadedAt: '2026-04-08 14:23',
    lastChecked: '2026-04-11 09:30'
  });
  
  // Quality metrics
  const [qualityMetrics] = useState({
    completeness: 96.8,
    consistency: 92.5,
    accuracy: 94.1,
    validity: 95.3,
    uniqueness: 98.7,
    timeliness: 91.2
  });
  
  // Missing values by column
  const [missingValues] = useState([
    { column: 'ANA_titer', missing: 15, percent: 1.2, severity: 'low' },
    { column: 'Anti_dsDNA', missing: 8, percent: 0.7, severity: 'low' },
    { column: 'C3_level', missing: 22, percent: 1.8, severity: 'medium' },
    { column: 'Diagnosis_date', missing: 3, percent: 0.2, severity: 'low' },
    { column: 'Treatment_response', missing: 45, percent: 3.7, severity: 'high' }
  ]);
  
  // Duplicate records
  const [duplicates] = useState([
    { primaryKey: 'PT1045', count: 2, columns: ['patient_id', 'visit_date'] },
    { primaryKey: 'PT2103', count: 2, columns: ['patient_id', 'lab_test'] }
  ]);
  
  // Outliers
  const [outliers] = useState([
    { column: 'Age', value: 92, zScore: 3.8, severity: 'high' },
    { column: 'SLEDAI_score', value: 28, zScore: 3.2, severity: 'medium' },
    { column: 'C3_level', value: 12, zScore: -2.9, severity: 'medium' }
  ]);
  
  // Data type validation
  const [validationIssues] = useState([
    { column: 'Birth_date', issue: 'Invalid date format', count: 2, example: '32/13/1990' },
    { column: 'Phone_number', issue: 'Non-numeric characters', count: 5, example: '012-345-ABCD' }
  ]);
  
  const getSeverityBadge = (severity) => {
    if (severity === 'high') return <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-700 font-medium">High</span>;
    if (severity === 'medium') return <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-700 font-medium">Medium</span>;
    return <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700 font-medium">Low</span>;
  };
  
  const getMetricColor = (score) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 85) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getMetricBg = (score) => {
    if (score >= 95) return 'bg-green-100';
    if (score >= 85) return 'bg-blue-100';
    if (score >= 70) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <DashboardLayout>
      {/* ═══ TOPBAR ═══ */}
      <div className="h-[70px] flex items-center gap-8 px-6 bg-[#F5F5F7] border-b border-gray-200 flex-shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Data Quality Analysis</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0]">Data Quality</span>
          </div>
        </div>
        
        {/* Right side: Actions */}
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => navigate('/data-catalog')}
            className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-black-text hover:border-purple-primary/40 transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Catalog
          </button>
          <button
            onClick={() => setLoading(true)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#7B5CF0] text-white hover:bg-[#6B4CE0] transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Re-check Quality
              </>
            )}
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-black-text hover:border-purple-primary/40 transition-all">
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)', zoom: 0.80 }}>
        
        {/* Dataset Info Card */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <FileSpreadsheet className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="font-syne text-xl font-bold text-gray-900 mb-1">{dataset.name}</h2>
                <p className="text-sm text-gray-600 mb-2">{dataset.filename}</p>
                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <span><strong>{dataset.rowCount.toLocaleString()}</strong> rows</span>
                  <span><strong>{dataset.columnCount}</strong> columns</span>
                  <span>Last checked: {dataset.lastChecked}</span>
                </div>
              </div>
            </div>
            
            {/* Overall Quality Score */}
            <div className="text-center">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center mb-2">
                <div className="text-3xl font-bold text-purple-600">{dataset.qualityScore}%</div>
              </div>
              <div className="text-sm text-gray-600 font-medium">Quality Score</div>
            </div>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex gap-8 px-6">
              {[
                { key: 'overview', label: 'Overview', icon: BarChart3 },
                { key: 'missing', label: 'Missing Values', icon: AlertTriangle },
                { key: 'duplicates', label: 'Duplicates', icon: XCircle },
                { key: 'outliers', label: 'Outliers', icon: TrendingUp },
                { key: 'validation', label: 'Validation', icon: CheckCircle }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-2 py-4 border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="p-6">
            
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 text-lg">Quality Metrics Breakdown</h3>
                
                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(qualityMetrics).map(([key, value]) => (
                    <div key={key} className={`${getMetricBg(value)} rounded-lg p-4`}>
                      <div className="text-sm text-gray-600 capitalize mb-1">{key.replace('_', ' ')}</div>
                      <div className={`text-3xl font-bold ${getMetricColor(value)}`}>{value}%</div>
                      <div className="mt-2 h-2 bg-white rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${getMetricColor(value).replace('text', 'bg')}`}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm font-medium text-gray-700">Missing Values</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{missingValues.reduce((sum, m) => sum + m.missing, 0)}</div>
                    <div className="text-xs text-gray-500 mt-1">Across {missingValues.length} columns</div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <XCircle className="w-4 h-4 text-red-600" />
                      <span className="text-sm font-medium text-gray-700">Duplicates</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{duplicates.length}</div>
                    <div className="text-xs text-gray-500 mt-1">Records affected</div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-orange-600" />
                      <span className="text-sm font-medium text-gray-700">Outliers</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{outliers.length}</div>
                    <div className="text-xs text-gray-500 mt-1">Detected anomalies</div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Validation Issues</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{validationIssues.reduce((sum, v) => sum + v.count, 0)}</div>
                    <div className="text-xs text-gray-500 mt-1">Invalid entries</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Missing Values Tab */}
            {activeTab === 'missing' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Missing Values by Column</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Column</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Missing Count</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Percentage</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Severity</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Visualization</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {missingValues.map((item, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{item.column}</td>
                          <td className="px-4 py-3 text-gray-700">{item.missing}</td>
                          <td className="px-4 py-3 text-gray-700">{item.percent}%</td>
                          <td className="px-4 py-3">{getSeverityBadge(item.severity)}</td>
                          <td className="px-4 py-3">
                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${
                                  item.severity === 'high' ? 'bg-red-500' :
                                  item.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${item.percent * 10}%` }}
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Duplicates Tab */}
            {activeTab === 'duplicates' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Duplicate Records</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Primary Key</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Duplicate Count</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Affected Columns</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {duplicates.map((item, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{item.primaryKey}</td>
                          <td className="px-4 py-3 text-gray-700">{item.count} copies</td>
                          <td className="px-4 py-3 text-gray-700">
                            {item.columns.map(col => (
                              <span key={col} className="inline-block px-2 py-1 rounded text-xs bg-gray-100 text-gray-700 mr-1">
                                {col}
                              </span>
                            ))}
                          </td>
                          <td className="px-4 py-3">
                            <button className="text-sm text-purple-600 hover:text-purple-800 font-medium">
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Outliers Tab */}
            {activeTab === 'outliers' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Detected Outliers</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Column</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Value</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Z-Score</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Severity</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {outliers.map((item, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{item.column}</td>
                          <td className="px-4 py-3 text-gray-700">{item.value}</td>
                          <td className="px-4 py-3 text-gray-700">{item.zScore.toFixed(2)}</td>
                          <td className="px-4 py-3">{getSeverityBadge(item.severity)}</td>
                          <td className="px-4 py-3">
                            <button className="text-sm text-purple-600 hover:text-purple-800 font-medium">
                              Flag for Review
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Validation Tab */}
            {activeTab === 'validation' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Data Type Validation Issues</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Column</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Issue Type</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Count</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Example</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {validationIssues.map((item, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{item.column}</td>
                          <td className="px-4 py-3 text-gray-700">{item.issue}</td>
                          <td className="px-4 py-3 text-gray-700">{item.count} entries</td>
                          <td className="px-4 py-3">
                            <code className="px-2 py-1 rounded text-xs bg-red-50 text-red-700">
                              {item.example}
                            </code>
                          </td>
                          <td className="px-4 py-3">
                            <button className="text-sm text-purple-600 hover:text-purple-800 font-medium">
                              View All
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
          </div>
        </div>
        
      </div>
    </DashboardLayout>
  );
}
