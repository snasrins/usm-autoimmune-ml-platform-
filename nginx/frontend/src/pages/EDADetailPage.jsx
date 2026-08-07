/**
 * EDA (Exploratory Data Analysis) Detail Page
 * ============================================
 * Dedicated page for comprehensive statistical analysis of a single dataset
 * 
 * Features:
 * - Statistical summary (mean, median, std, min, max)
 * - Distribution visualizations
 * - Correlation matrix
 * - Category breakdowns
 * - Time series analysis (if applicable)
 * - Feature relationships
 * 
 * Author: Syarifah Fajriyah
 * Date: April 11, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  Download,
  RefreshCw,
  ChevronRight,
  PieChart,
  Activity,
  FileSpreadsheet,
  Info
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function EDADetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('statistics'); // statistics, distributions, correlations, categories
  
  // Mock dataset data (replace with API call)
  const [dataset] = useState({
    id: id,
    name: 'AAM-SLE-E (real data)',
    filename: 'AAM-SLE-E (real data).xlsx',
    rowCount: 1204,
    columnCount: 18,
    uploadedAt: '2026-04-08 14:23',
    lastAnalyzed: '2026-04-11 10:15'
  });
  
  // Statistical summary for numeric columns
  const [numericStats] = useState([
    { column: 'Age', count: 1204, mean: 38.5, std: 12.3, min: 18, q25: 29, median: 37, q75: 47, max: 75, missing: 0 },
    { column: 'SLEDAI_score', count: 1204, mean: 8.2, std: 4.1, min: 0, q25: 5, median: 8, q75: 11, max: 24, missing: 15 },
    { column: 'C3_level', count: 1182, mean: 92.5, std: 18.7, min: 45, q25: 78, median: 91, q75: 105, max: 135, missing: 22 },
    { column: 'C4_level', count: 1195, mean: 18.3, std: 6.2, min: 5, q25: 14, median: 18, q75: 22, max: 38, missing: 9 },
    { column: 'Anti_dsDNA', count: 1196, mean: 125.4, std: 89.3, min: 0, q25: 52, median: 98, q75: 165, max: 420, missing: 8 }
  ]);
  
  // Categorical columns summary
  const [categoricalStats] = useState([
    { 
      column: 'Gender', 
      unique: 2, 
      topValue: 'Female', 
      topFreq: 1089, 
      topPercent: 90.4,
      distribution: [
        { value: 'Female', count: 1089, percent: 90.4 },
        { value: 'Male', count: 115, percent: 9.6 }
      ]
    },
    { 
      column: 'Disease_activity', 
      unique: 4, 
      topValue: 'Moderate', 
      topFreq: 542, 
      topPercent: 45.0,
      distribution: [
        { value: 'Moderate', count: 542, percent: 45.0 },
        { value: 'Low', count: 385, percent: 32.0 },
        { value: 'High', count: 201, percent: 16.7 },
        { value: 'Remission', count: 76, percent: 6.3 }
      ]
    },
    { 
      column: 'Treatment_type', 
      unique: 5, 
      topValue: 'Hydroxychloroquine', 
      topFreq: 892, 
      topPercent: 74.1,
      distribution: [
        { value: 'Hydroxychloroquine', count: 892, percent: 74.1 },
        { value: 'Corticosteroids', count: 645, percent: 53.6 },
        { value: 'Azathioprine', count: 287, percent: 23.8 },
        { value: 'Mycophenolate', count: 156, percent: 13.0 },
        { value: 'Cyclophosphamide', count: 89, percent: 7.4 }
      ]
    }
  ]);
  
  // Correlation data (mock)
  const [correlations] = useState([
    { var1: 'SLEDAI_score', var2: 'Anti_dsDNA', correlation: 0.67, strength: 'strong' },
    { var1: 'Age', var2: 'Disease_duration', correlation: 0.82, strength: 'strong' },
    { var1: 'C3_level', var2: 'C4_level', correlation: 0.74, strength: 'strong' },
    { var1: 'SLEDAI_score', var2: 'C3_level', correlation: -0.58, strength: 'moderate' },
    { var1: 'Age', var2: 'SLEDAI_score', correlation: 0.23, strength: 'weak' }
  ]);
  
  const getCorrelationColor = (corr) => {
    const abs = Math.abs(corr);
    if (abs >= 0.7) return 'bg-purple-600';
    if (abs >= 0.5) return 'bg-blue-500';
    if (abs >= 0.3) return 'bg-yellow-500';
    return 'bg-gray-400';
  };
  
  const getCorrelationText = (corr) => {
    if (corr > 0) return 'Positive';
    return 'Negative';
  };

  return (
    <DashboardLayout>
      {/* ═══ TOPBAR ═══ */}
      <div className="h-[70px] flex items-center gap-8 px-6 bg-[#F5F5F7] border-b border-gray-200 flex-shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Exploratory Data Analysis</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0]">EDA</span>
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
                Analyzing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Re-run Analysis
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
              <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <FileSpreadsheet className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="font-syne text-xl font-bold text-gray-900 mb-1">{dataset.name}</h2>
                <p className="text-sm text-gray-600 mb-2">{dataset.filename}</p>
                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <span><strong>{dataset.rowCount.toLocaleString()}</strong> rows</span>
                  <span><strong>{dataset.columnCount}</strong> columns</span>
                  <span>Last analyzed: {dataset.lastAnalyzed}</span>
                </div>
              </div>
            </div>
            
            {/* Quick Stats */}
            <div className="flex gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{numericStats.length}</div>
                <div className="text-xs text-gray-600">Numeric</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{categoricalStats.length}</div>
                <div className="text-xs text-gray-600">Categorical</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{correlations.length}</div>
                <div className="text-xs text-gray-600">Correlations</div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex gap-8 px-6">
              {[
                { key: 'statistics', label: 'Statistics', icon: BarChart3 },
                { key: 'distributions', label: 'Distributions', icon: PieChart },
                { key: 'correlations', label: 'Correlations', icon: Activity },
                { key: 'categories', label: 'Categories', icon: TrendingUp }
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
            
            {/* Statistics Tab */}
            {activeTab === 'statistics' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Statistical Summary - Numeric Columns</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700 sticky left-0 bg-gray-50">Column</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Count</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Mean</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Std Dev</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Min</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">25%</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Median</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">75%</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Max</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Missing</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {numericStats.map((stat, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">{stat.column}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.count}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.mean.toFixed(2)}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.std.toFixed(2)}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.min}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.q25}</td>
                            <td className="px-4 py-3 text-right text-gray-700 font-semibold">{stat.median}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.q75}</td>
                            <td className="px-4 py-3 text-right text-gray-700">{stat.max}</td>
                            <td className="px-4 py-3 text-right text-gray-700">
                              {stat.missing > 0 ? (
                                <span className="text-red-600 font-medium">{stat.missing}</span>
                              ) : (
                                <span className="text-green-600">0</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                {/* Info box */}
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-900">
                    <strong>Statistical Measures:</strong> The table shows descriptive statistics for numeric columns. 
                    Mean and median indicate central tendency, while standard deviation measures spread. 
                    Quartiles (25%, 50%, 75%) divide the data into four equal parts.
                  </div>
                </div>
              </div>
            )}
            
            {/* Distributions Tab */}
            {activeTab === 'distributions' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Data Distributions</h3>
                
                {/* Placeholder for distribution charts */}
                <div className="grid grid-cols-2 gap-6">
                  {numericStats.slice(0, 4).map((stat, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-6">
                      <h4 className="font-medium text-gray-900 mb-4">{stat.column}</h4>
                      <div className="h-48 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg flex items-center justify-center">
                        <div className="text-center text-gray-400">
                          <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                          <p className="text-sm">Distribution Histogram</p>
                          <p className="text-xs mt-1">Mean: {stat.mean.toFixed(1)} | Median: {stat.median}</p>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-gray-500">Range</div>
                          <div className="font-semibold text-gray-900">{stat.min} - {stat.max}</div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-gray-500">Std Dev</div>
                          <div className="font-semibold text-gray-900">{stat.std.toFixed(2)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Correlations Tab */}
            {activeTab === 'correlations' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Feature Correlations</h3>
                
                {/* Correlation table */}
                <div className="border border-gray-200 rounded-lg overflow-hidden mb-6">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Variable 1</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Variable 2</th>
                        <th className="px-4 py-3 text-right font-semibold text-gray-700">Correlation</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Strength</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Visualization</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {correlations.map((corr, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{corr.var1}</td>
                          <td className="px-4 py-3 font-medium text-gray-900">{corr.var2}</td>
                          <td className="px-4 py-3 text-right">
                            <span className={`font-semibold ${corr.correlation > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {corr.correlation.toFixed(2)}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              corr.correlation > 0 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {getCorrelationText(corr.correlation)}
                            </span>
                          </td>
                          <td className="px-4 py-3 capitalize text-gray-700">{corr.strength}</td>
                          <td className="px-4 py-3">
                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={getCorrelationColor(corr.correlation)}
                                style={{ width: `${Math.abs(corr.correlation) * 100}%` }}
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Info box */}
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg flex items-start gap-3">
                  <Info className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-purple-900">
                    <strong>Correlation Interpretation:</strong> Values range from -1 to +1. 
                    Positive values indicate variables increase together, negative values indicate inverse relationships. 
                    |Correlation| ≥ 0.7 is strong, 0.5-0.7 is moderate, 0.3-0.5 is weak, &lt;0.3 is negligible.
                  </div>
                </div>
              </div>
            )}
            
            {/* Categories Tab */}
            {activeTab === 'categories' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-4">Categorical Variables Summary</h3>
                
                <div className="space-y-6">
                  {categoricalStats.map((cat, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h4 className="font-medium text-gray-900 text-lg">{cat.column}</h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {cat.unique} unique values • Most common: <strong>{cat.topValue}</strong> ({cat.topPercent}%)
                          </p>
                        </div>
                      </div>
                      
                      {/* Distribution bars */}
                      <div className="space-y-3">
                        {cat.distribution.map((item, j) => (
                          <div key={j}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-gray-700">{item.value}</span>
                              <span className="text-sm text-gray-600">{item.count} ({item.percent}%)</span>
                            </div>
                            <div className="w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-end px-2"
                                style={{ width: `${item.percent}%` }}
                              >
                                {item.percent > 10 && (
                                  <span className="text-xs text-white font-medium">{item.percent}%</span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
          </div>
        </div>
        
      </div>
    </DashboardLayout>
  );
}
