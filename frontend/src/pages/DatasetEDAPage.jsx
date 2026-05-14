/**
 * Dataset EDA (Exploratory Data Analysis) Page
 * ================================================
 * Complete data exploration with interactive visualizations
 * - Data preview and summary statistics
 * - Distribution plots and correlation matrix
 * - Missing values analysis
 * - Categorical analysis
 * - Outlier detection
 */

import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, LineChart, Line, ScatterChart, Scatter,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Area, AreaChart
} from 'recharts';
import {
  ArrowLeft, Download, TrendingUp, TrendingDown, AlertTriangle,
  Database, BarChart3, PieChart as PieChartIcon, Activity,
  FileText, Grid3x3, Filter, Search, ChevronDown, ChevronUp
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { flexibleAPI, preprocessingAPI } from '../services/api';

const COLORS = ['#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444', '#6366F1', '#14B8A6'];

export default function DatasetEDAPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId, datasetName } = location.state || {};
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    distributions: true,
    correlations: true,
    missing: true,
    outliers: true
  });
  
  // Data states
  const [previewData, setPreviewData] = useState(null);
  const [statistics, setStatistics] = useState({});
  const [columnTypes, setColumnTypes] = useState({});
  const [missingValues, setMissingValues] = useState([]);
  const [distributions, setDistributions] = useState({});
  const [categoricalData, setCategoricalData] = useState({});
  const [correlations, setCorrelations] = useState([]);
  const [outliers, setOutliers] = useState({});
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    if (datasetId) {
      loadEDAData();
    } else {
      navigate('/ml-preparation');
    }
  }, [datasetId]);

  const loadEDAData = async () => {
    setLoading(true);
    try {
      // Load preview data (first 100 rows)
      // Use saved dataset API since datasets in ML Queue are saved (status: 'saved')
      console.log('[EDA] Loading saved dataset:', datasetId);
      const preview = await flexibleAPI.getSavedDatasetPreview(datasetId, 1, 100);
      console.log('[EDA] Preview data:', preview);
      console.log('[EDA] Preview keys:', Object.keys(preview));
      console.log('[EDA] Preview.rows:', preview.rows);
      console.log('[EDA] Preview.rows length:', preview.rows?.length);
      if (preview.rows && preview.rows.length > 0) {
        console.log('[EDA] First row:', preview.rows[0]);
        console.log('[EDA] First row.data:', preview.rows[0]?.data);
        console.log('[EDA] First row.data keys:', preview.rows[0]?.data ? Object.keys(preview.rows[0].data) : 'none');
      }
      
      // Normalize preview structure
      const normalizedPreview = {
        rows: preview.rows || [],
        columns: preview.columns || (preview.rows && preview.rows.length > 0 
          ? Object.keys(preview.rows[0].data || {}) 
          : []),
        total_rows: preview.total_rows || preview.rows?.length || 0
      };
      
      console.log('[EDA] Normalized preview:', normalizedPreview);
      console.log('[EDA] Normalized rows length:', normalizedPreview.rows.length);
      console.log('[EDA] Normalized columns:', normalizedPreview.columns);
      
      setPreviewData(normalizedPreview);
      
      // Try to load quality report (optional - graceful fallback)
      let quality = null;
      try {
        quality = await preprocessingAPI.getQualityReport(datasetId);
        console.log('[EDA] Quality report:', quality);
      } catch (qualityError) {
        console.warn('[EDA] Quality report not available:', qualityError.message);
        // Continue without quality report
      }
      
      // Process data for visualizations
      if (normalizedPreview.rows.length > 0) {
        processDataForEDA(normalizedPreview, quality);
      } else {
        setInsights([{
          type: 'warning',
          icon: AlertTriangle,
          title: 'No Data',
          message: 'No data available for analysis. The dataset might be empty.'
        }]);
      }
      
    } catch (error) {
      console.error('Failed to load EDA data:', error);
      setInsights([{
        type: 'error',
        icon: AlertTriangle,
        title: 'Error Loading Data',
        message: error.response?.data?.detail || error.message || 'Failed to load dataset'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const processDataForEDA = (preview, quality) => {
    if (!preview?.rows || preview.rows.length === 0) {
      console.warn('[EDA] No rows to process');
      return;
    }
    
    const rows = preview.rows;
    const columns = preview.columns && preview.columns.length > 0 
      ? preview.columns 
      : Object.keys(rows[0]?.data || {});
    
    if (columns.length === 0) {
      console.warn('[EDA] No columns found');
      setInsights([{
        type: 'warning',
        icon: AlertTriangle,
        title: 'No Columns',
        message: 'Dataset structure could not be determined'
      }]);
      return;
    }
    
    console.log('[EDA] Processing', rows.length, 'rows and', columns.length, 'columns');
    
    // 1. Detect column types and calculate statistics
    const types = {};
    const stats = {};
    const dists = {};
    const catData = {};
    const missing = [];
    const outlierData = {};
    
    columns.forEach(col => {
      const values = rows.map(r => r.data[col]).filter(v => v !== null && v !== undefined && v !== '');
      const nullCount = rows.length - values.length;
      const nullPct = (nullCount / rows.length) * 100;
      
      // Add to missing values tracking
      if (nullCount > 0) {
        missing.push({
          column: col,
          count: nullCount,
          percentage: nullPct
        });
      }
      
      // Detect type
      const isNumeric = values.length > 0 && values.every(v => !isNaN(parseFloat(v)));
      types[col] = isNumeric ? 'numeric' : 'categorical';
      
      if (isNumeric) {
        // Calculate numeric statistics
        const numValues = values.map(v => parseFloat(v));
        const sorted = [...numValues].sort((a, b) => a - b);
        const mean = numValues.reduce((a, b) => a + b, 0) / numValues.length;
        const variance = numValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / numValues.length;
        const std = Math.sqrt(variance);
        
        stats[col] = {
          count: numValues.length,
          mean: mean.toFixed(2),
          std: std.toFixed(2),
          min: Math.min(...numValues).toFixed(2),
          q1: sorted[Math.floor(numValues.length * 0.25)].toFixed(2),
          median: sorted[Math.floor(numValues.length * 0.5)].toFixed(2),
          q3: sorted[Math.floor(numValues.length * 0.75)].toFixed(2),
          max: Math.max(...numValues).toFixed(2)
        };
        
        // Create distribution data (binning)
        const bins = 20;
        const binSize = (stats[col].max - stats[col].min) / bins;
        const binCounts = Array(bins).fill(0);
        numValues.forEach(v => {
          const binIndex = Math.min(Math.floor((v - stats[col].min) / binSize), bins - 1);
          binCounts[binIndex]++;
        });
        
        dists[col] = binCounts.map((count, i) => ({
          bin: ((stats[col].min * 1) + (binSize * i)).toFixed(1),
          count
        }));
        
        // Detect outliers using IQR method
        const iqr = stats[col].q3 - stats[col].q1;
        const lowerBound = stats[col].q1 - 1.5 * iqr;
        const upperBound = stats[col].q3 + 1.5 * iqr;
        const outlierValues = numValues.filter(v => v < lowerBound || v > upperBound);
        outlierData[col] = {
          count: outlierValues.length,
          percentage: (outlierValues.length / numValues.length * 100).toFixed(1),
          lowerBound,
          upperBound
        };
        
      } else {
        // Calculate categorical statistics
        const valueCounts = {};
        values.forEach(v => {
          const key = String(v);
          valueCounts[key] = (valueCounts[key] || 0) + 1;
        });
        
        const uniqueValues = Object.keys(valueCounts).length;
        const topValues = Object.entries(valueCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 10)
          .map(([value, count]) => ({
            value,
            count,
            percentage: (count / values.length * 100).toFixed(1)
          }));
        
        stats[col] = {
          count: values.length,
          unique: uniqueValues,
          top: topValues[0]?.value,
          topFreq: topValues[0]?.count
        };
        
        catData[col] = topValues;
      }
    });
    
    setColumnTypes(types);
    setStatistics(stats);
    setDistributions(dists);
    setCategoricalData(catData);
    setMissingValues(missing.sort((a, b) => b.percentage - a.percentage));
    setOutliers(outlierData);
    
    // Calculate correlations for numeric columns
    const numericCols = columns.filter(c => types[c] === 'numeric');
    if (numericCols.length >= 2) {
      const corrMatrix = [];
      for (let i = 0; i < numericCols.length; i++) {
        for (let j = i + 1; j < numericCols.length; j++) {
          const col1 = numericCols[i];
          const col2 = numericCols[j];
          
          const values1 = rows.map(r => parseFloat(r.data[col1])).filter(v => !isNaN(v));
          const values2 = rows.map(r => parseFloat(r.data[col2])).filter(v => !isNaN(v));
          
          if (values1.length > 0 && values2.length > 0) {
            const corr = calculateCorrelation(values1, values2);
            if (!isNaN(corr)) {
              corrMatrix.push({
                col1,
                col2,
                correlation: corr.toFixed(3),
                absCorr: Math.abs(corr)
              });
            }
          }
        }
      }
      setCorrelations(corrMatrix.sort((a, b) => b.absCorr - a.absCorr).slice(0, 15));
    }
    
    // Generate insights
    generateInsights(types, stats, missing, outlierData, columns.length, rows.length);
  };

  const calculateCorrelation = (x, y) => {
    const n = Math.min(x.length, y.length);
    const meanX = x.reduce((a, b) => a + b, 0) / n;
    const meanY = y.reduce((a, b) => a + b, 0) / n;
    
    let num = 0, denX = 0, denY = 0;
    for (let i = 0; i < n; i++) {
      const dx = x[i] - meanX;
      const dy = y[i] - meanY;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }
    
    return num / Math.sqrt(denX * denY);
  };

  const generateInsights = (types, stats, missing, outlierData, colCount, rowCount) => {
    const insights = [];
    
    // Dataset size insight
    insights.push({
      type: 'info',
      icon: Database,
      title: 'Dataset Size',
      message: `Dataset contains ${rowCount.toLocaleString()} rows and ${colCount} columns`
    });
    
    // Missing values insight
    const totalMissing = missing.reduce((sum, m) => sum + m.count, 0);
    const missingPct = (totalMissing / (rowCount * colCount) * 100).toFixed(1);
    if (totalMissing > 0) {
      insights.push({
        type: missingPct > 5 ? 'warning' : 'info',
        icon: AlertTriangle,
        title: 'Missing Values',
        message: `${missingPct}% of data points are missing (${missing.length} columns affected)`
      });
    }
    
    // Column types insight
    const numericCount = Object.values(types).filter(t => t === 'numeric').length;
    const catCount = colCount - numericCount;
    insights.push({
      type: 'success',
      icon: Grid3x3,
      title: 'Column Types',
      message: `${numericCount} numerical and ${catCount} categorical features`
    });
    
    // Outliers insight
    const colsWithOutliers = Object.entries(outlierData).filter(([, data]) => data.count > 0).length;
    if (colsWithOutliers > 0) {
      insights.push({
        type: 'warning',
        icon: TrendingUp,
        title: 'Outliers Detected',
        message: `${colsWithOutliers} numerical columns contain outliers`
      });
    }
    
    setInsights(insights);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const downloadReport = () => {
    // Create downloadable EDA report
    const report = {
      dataset_name: datasetName,
      timestamp: new Date().toISOString(),
      statistics,
      column_types: columnTypes,
      missing_values: missingValues,
      correlations,
      outliers,
      insights
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eda_report_${datasetId.substring(0, 8)}.json`;
    a.click();
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading EDA...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="h-[70px] flex items-center gap-8 px-6 bg-[#F5F5F7] border-b border-gray-200 flex-shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">
            Exploratory Data Analysis
          </h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>Dataset: {datasetName?.substring(0, 50) || 'Unknown'}</span>
          </div>
        </div>
        
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-semibold"
          >
            <Download className="w-4 h-4" />
            Download Report
          </button>
          <button
            onClick={() => navigate('/ml-preparation')}
            className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Queue
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6" style={{ background: '#FAFBFC', zoom: 0.78 }}>
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Insights Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {insights.map((insight, idx) => {
              const Icon = insight.icon;
              const bgColors = {
                info: 'bg-blue-50 border-blue-200',
                success: 'bg-green-50 border-green-200',
                warning: 'bg-yellow-50 border-yellow-200',
                error: 'bg-red-50 border-red-200'
              };
              const iconColors = {
                info: 'text-blue-600',
                success: 'text-green-600',
                warning: 'text-yellow-600',
                error: 'text-red-600'
              };
              
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className={`p-4 rounded-xl border-2 ${bgColors[insight.type]}`}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={`w-5 h-5 ${iconColors[insight.type]} flex-shrink-0 mt-0.5`} />
                    <div className="flex-1">
                      <h3 className="font-semibold text-sm text-gray-900 mb-1">{insight.title}</h3>
                      <p className="text-xs text-gray-600">{insight.message}</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Data Preview Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
          >
            <div 
              className="px-6 py-4 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
              onClick={() => toggleSection('overview')}
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-purple-600" />
                <h2 className="font-syne text-lg font-bold text-gray-900">Data Preview</h2>
              </div>
              {expandedSections.overview ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
            </div>
            
            {expandedSections.overview && previewData?.rows && previewData.rows.length > 0 && (
              <div className="p-6">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold">#</th>
                        {(previewData.columns || []).slice(0, 10).map(col => (
                          <th key={col} className="px-4 py-3 text-left font-semibold whitespace-nowrap">
                            {col}
                            <span className="ml-2 text-xs opacity-75">
                              ({columnTypes[col] === 'numeric' ? 'num' : 'cat'})
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.rows.slice(0, 10).map((row, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                          <td className="px-4 py-2 font-semibold text-gray-500">{idx + 1}</td>
                          {(previewData.columns || []).slice(0, 10).map(col => (
                            <td key={col} className="px-4 py-2 text-gray-700">
                              {row.data[col] !== null && row.data[col] !== undefined 
                                ? String(row.data[col]).substring(0, 30)
                                : <span className="text-gray-400 italic">null</span>
                              }
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {previewData.columns && previewData.columns.length > 10 && (
                  <p className="mt-4 text-sm text-gray-500 text-center">
                    Showing first 10 of {previewData.columns.length} columns
                  </p>
                )}
              </div>
            )}
          </motion.div>

          {/* Summary Statistics */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
          >
            <div 
              className="px-6 py-4 bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
              onClick={() => toggleSection('statistics')}
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h2 className="font-syne text-lg font-bold text-gray-900">Summary Statistics</h2>
              </div>
              {expandedSections.statistics ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
            </div>
            
            {expandedSections.statistics && (
              <div className="p-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Column</th>
                      <th className="px-4 py-3 text-left font-semibold">Type</th>
                      <th className="px-4 py-3 text-right font-semibold">Count</th>
                      <th className="px-4 py-3 text-right font-semibold">Mean</th>
                      <th className="px-4 py-3 text-right font-semibold">Std</th>
                      <th className="px-4 py-3 text-right font-semibold">Min</th>
                      <th className="px-4 py-3 text-right font-semibold">Q1</th>
                      <th className="px-4 py-3 text-right font-semibold">Median</th>
                      <th className="px-4 py-3 text-right font-semibold">Q3</th>
                      <th className="px-4 py-3 text-right font-semibold">Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(statistics).slice(0, 20).map(([col, stat], idx) => (
                      <tr key={col} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                        <td className="px-4 py-2 font-semibold text-gray-900">{col}</td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            columnTypes[col] === 'numeric' 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {columnTypes[col] === 'numeric' ? 'Numerical' : 'Categorical'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right text-gray-700">{stat.count}</td>
                        {columnTypes[col] === 'numeric' ? (
                          <>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.mean}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.std}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.min}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.q1}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.median}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.q3}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{stat.max}</td>
                          </>
                        ) : (
                          <>
                            <td className="px-4 py-2 text-right text-gray-400" colSpan="7">
                              {stat.unique} unique values
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>

          {/* Distribution Plots */}
          {Object.keys(distributions).length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div 
                className="px-6 py-4 bg-gradient-to-r from-green-50 to-emerald-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
                onClick={() => toggleSection('distributions')}
              >
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-green-600" />
                  <h2 className="font-syne text-lg font-bold text-gray-900">Distribution Plots</h2>
                </div>
                {expandedSections.distributions ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
              </div>
              
              {expandedSections.distributions && (
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {Object.entries(distributions).slice(0, 6).map(([col, data]) => (
                      <div key={col} className="border border-gray-200 rounded-lg p-4">
                        <h3 className="font-semibold text-sm text-gray-900 mb-3">{col}</h3>
                        <ResponsiveContainer width="100%" height={200}>
                          <AreaChart data={data}>
                            <defs>
                              <linearGradient id={`gradient-${col}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                            <XAxis dataKey="bin" tick={{ fontSize: 11 }} stroke="#6B7280" />
                            <YAxis tick={{ fontSize: 11 }} stroke="#6B7280" />
                            <Tooltip 
                              contentStyle={{ 
                                background: 'white', 
                                border: '1px solid #E5E7EB', 
                                borderRadius: '8px',
                                fontSize: '12px'
                              }} 
                            />
                            <Area type="monotone" dataKey="count" stroke="#8B5CF6" fillOpacity={1} fill={`url(#gradient-${col})`} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Categorical Analysis */}
          {Object.keys(categoricalData).length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div className="px-6 py-4 bg-gradient-to-r from-pink-50 to-rose-50 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <PieChartIcon className="w-5 h-5 text-pink-600" />
                  <h2 className="font-syne text-lg font-bold text-gray-900">Categorical Analysis</h2>
                </div>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(categoricalData).slice(0, 4).map(([col, data]) => (
                    <div key={col} className="border border-gray-200 rounded-lg p-4">
                      <h3 className="font-semibold text-sm text-gray-900 mb-3">{col}</h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={data} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                          <XAxis type="number" tick={{ fontSize: 11 }} stroke="#6B7280" />
                          <YAxis dataKey="value" type="category" width={100} tick={{ fontSize: 10 }} stroke="#6B7280" />
                          <Tooltip 
                            contentStyle={{ 
                              background: 'white', 
                              border: '1px solid #E5E7EB', 
                              borderRadius: '8px',
                              fontSize: '12px'
                            }} 
                          />
                          <Bar dataKey="count" fill="#EC4899" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Missing Values */}
          {missingValues.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div 
                className="px-6 py-4 bg-gradient-to-r from-yellow-50 to-orange-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
                onClick={() => toggleSection('missing')}
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <h2 className="font-syne text-lg font-bold text-gray-900">Missing Values Analysis</h2>
                </div>
                {expandedSections.missing ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
              </div>
              
              {expandedSections.missing && (
                <div className="p-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={missingValues.slice(0, 15)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="column" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} stroke="#6B7280" />
                      <YAxis tick={{ fontSize: 11 }} stroke="#6B7280" label={{ value: 'Missing %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} />
                      <Tooltip 
                        contentStyle={{ 
                          background: 'white', 
                          border: '1px solid #E5E7EB', 
                          borderRadius: '8px',
                          fontSize: '12px'
                        }} 
                      />
                      <Bar dataKey="percentage" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>
          )}

          {/* Correlation Matrix */}
          {correlations.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div 
                className="px-6 py-4 bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
                onClick={() => toggleSection('correlations')}
              >
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  <h2 className="font-syne text-lg font-bold text-gray-900">Top Correlations</h2>
                </div>
                {expandedSections.correlations ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
              </div>
              
              {expandedSections.correlations && (
                <div className="p-6">
                  <div className="space-y-3">
                    {correlations.slice(0, 10).map((corr, idx) => (
                      <div key={idx} className="flex items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {corr.col1} ↔ {corr.col2}
                            </span>
                            <span className={`text-sm font-bold ${
                              parseFloat(corr.correlation) > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {corr.correlation}
                            </span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${
                                parseFloat(corr.correlation) > 0 
                                  ? 'bg-gradient-to-r from-green-400 to-green-600' 
                                  : 'bg-gradient-to-r from-red-400 to-red-600'
                              }`}
                              style={{ width: `${corr.absCorr * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Outliers Summary */}
          {Object.keys(outliers).some(k => outliers[k].count > 0) && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div 
                className="px-6 py-4 bg-gradient-to-r from-red-50 to-pink-50 border-b border-gray-200 flex items-center justify-between cursor-pointer"
                onClick={() => toggleSection('outliers')}
              >
                <div className="flex items-center gap-3">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <h2 className="font-syne text-lg font-bold text-gray-900">Outlier Detection</h2>
                </div>
                {expandedSections.outliers ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
              </div>
              
              {expandedSections.outliers && (
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(outliers)
                      .filter(([, data]) => data.count > 0)
                      .slice(0, 9)
                      .map(([col, data]) => (
                        <div key={col} className="border border-gray-200 rounded-lg p-4">
                          <h3 className="font-semibold text-sm text-gray-900 mb-2">{col}</h3>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Outliers:</span>
                              <span className="font-semibold text-red-600">
                                {data.count} ({data.percentage}%)
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Lower Bound:</span>
                              <span className="font-mono text-gray-900">{data.lowerBound}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Upper Bound:</span>
                              <span className="font-mono text-gray-900">{data.upperBound}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

        </div>
      </div>
    </DashboardLayout>
  );
}
