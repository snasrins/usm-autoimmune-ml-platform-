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
  Info,
  AlertCircle,
  Loader2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import { flexibleAPI } from '../services/api';

export default function EDADetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('statistics');

  const [dataset, setDataset] = useState({ id, name: '—', rowCount: 0, columnCount: 0, lastAnalyzed: '—' });
  const [numericStats, setNumericStats] = useState([]);
  const [categoricalStats, setCategoricalStats] = useState([]);
  const [correlations, setCorrelations] = useState([]);
  const [histograms, setHistograms] = useState({});

  const loadData = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const d = await flexibleAPI.getBatchSummary(id);

      setDataset({
        id,
        name: d.dataset_name || id,
        rowCount: d.row_count || 0,
        columnCount: d.column_count || 0,
        lastAnalyzed: new Date().toLocaleString()
      });

      // Map numeric_summary dict → array
      const ns = d.summary_statistics?.numeric_summary || {};
      const numArr = Object.entries(ns)
        .filter(([, v]) => v && typeof v === 'object' && !v.error)
        .map(([col, v]) => ({
          column: col,
          count: v.count ?? 0,
          mean: v.mean ?? 0,
          std: v.std ?? 0,
          min: v.min ?? 0,
          q25: v.q25 ?? 0,
          median: v.median ?? v.q50 ?? 0,
          q75: v.q75 ?? 0,
          max: v.max ?? 0,
          missing: (d.row_count ?? 0) - (v.count ?? 0)
        }));
      setNumericStats(numArr);

      // Map categorical_summary dict → array
      const cs = d.summary_statistics?.categorical_summary || {};
      const catArr = Object.entries(cs)
        .filter(([, v]) => v && typeof v === 'object' && !v.error)
        .map(([col, v]) => ({
          column: col,
          unique: v.unique_count ?? 0,
          topValue: v.mode ?? '—',
          topFreq: v.mode_frequency ?? 0,
          topPercent: v.mode_percentage ?? 0,
          distribution: Object.entries(v.top_10_values || {}).map(([val, cnt]) => ({
            value: val,
            count: cnt,
            percent: v.count ? parseFloat(((cnt / v.count) * 100).toFixed(1)) : 0
          }))
        }));
      setCategoricalStats(catArr);

      setCorrelations(d.top_correlations || []);
      setHistograms(d.histograms || {});
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load EDA data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [id]);

  const getCorrelationColor = (corr) => {
    const abs = Math.abs(corr);
    if (abs >= 0.7) return 'bg-purple-600';
    if (abs >= 0.5) return 'bg-blue-500';
    if (abs >= 0.3) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  const getCorrelationText = (corr) => (corr > 0 ? 'Positive' : 'Negative');

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-10 h-10 text-purple-600 animate-spin mx-auto mb-3" />
            <p className="text-gray-600">Analysing dataset…</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
            <p className="text-gray-900 font-semibold mb-1">Failed to load EDA</p>
            <p className="text-gray-600 text-sm mb-4">{error}</p>
            <button onClick={() => navigate(-1)} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm">Go Back</button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

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
            onClick={loadData}
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
          <button
            onClick={() => {
              // Build a text report and trigger download
              const lines = [
                `EDA Report — ${dataset.name}`,
                `Generated: ${new Date().toLocaleString()}`,
                `Rows: ${dataset.rowCount}  Columns: ${dataset.columnCount}`,
                '',
                '=== NUMERIC STATISTICS ===',
                'Column,Count,Mean,Std,Min,25%,Median,75%,Max,Missing',
                ...numericStats.map(s =>
                  `${s.column},${s.count},${s.mean.toFixed(3)},${s.std.toFixed(3)},${s.min},${s.q25},${s.median},${s.q75},${s.max},${s.missing}`
                ),
                '',
                '=== TOP CORRELATIONS ===',
                'Variable1,Variable2,Correlation,Strength',
                ...correlations.map(c =>
                  `${c.var1},${c.var2},${c.correlation.toFixed(3)},${c.strength}`
                ),
                '',
                '=== CATEGORICAL SUMMARY ===',
                'Column,UniqueValues,MostCommon,MostCommonPct',
                ...categoricalStats.map(c =>
                  `${c.column},${c.unique},${c.topValue},${c.topPercent}%`
                ),
              ].join('\n');

              const blob = new Blob([lines], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `EDA_Report_${dataset.name.replace(/\s+/g,'_')}_${new Date().toISOString().slice(0,10)}.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium text-black-text hover:border-purple-primary/40 hover:text-purple-600 transition-all"
          >
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
                <h3 className="font-semibold text-gray-900 text-lg mb-1">Data Distributions</h3>
                <p className="text-sm text-gray-500 mb-5">{numericStats.length} numeric columns — histogram bars show frequency across value ranges</p>

                <div className="grid grid-cols-2 gap-5">
                  {numericStats.map((stat, i) => {
                    const hist = histograms[stat.column];
                    // Build chart data: each bin as { range, count }
                    const chartData = hist
                      ? hist.counts.map((count, bi) => ({
                          range: `${hist.bins[bi].toFixed(1)}–${hist.bins[bi + 1].toFixed(1)}`,
                          count,
                        }))
                      : [];
                    const maxCount = hist ? Math.max(...hist.counts, 1) : 1;
                    // Detect skewness hint
                    const skewHint = stat.mean > stat.median ? 'Right-skewed' : stat.mean < stat.median ? 'Left-skewed' : 'Symmetric';
                    const skewColor = stat.mean > stat.median ? 'text-orange-600' : stat.mean < stat.median ? 'text-blue-600' : 'text-green-600';

                    return (
                      <div key={i} className="border border-gray-200 rounded-xl p-4 bg-white hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-semibold text-gray-900 text-sm">{stat.column}</h4>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 ${skewColor}`}>{skewHint}</span>
                            <span className="text-xs text-gray-400">n={stat.count}</span>
                          </div>
                        </div>

                        {hist && chartData.length > 0 ? (
                          <ResponsiveContainer width="100%" height={160}>
                            <BarChart data={chartData} margin={{ top: 6, right: 4, bottom: 22, left: 0 }}
                              barCategoryGap="2%">
                              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                              <XAxis
                                dataKey="range"
                                tick={{ fontSize: 9, fill: '#9ca3af' }}
                                angle={-35}
                                textAnchor="end"
                                interval={0}
                                tickLine={false}
                              />
                              <YAxis tick={{ fontSize: 9, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                              <Tooltip
                                formatter={(value) => [`${value} records`, 'Count']}
                                contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
                              />
                              <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                                {chartData.map((entry, idx) => (
                                  <Cell
                                    key={idx}
                                    fill={entry.count === maxCount
                                      ? '#7c3aed'
                                      : idx < chartData.length / 2
                                        ? `rgba(124,58,237,${0.3 + (entry.count / maxCount) * 0.5})`
                                        : `rgba(99,102,241,${0.3 + (entry.count / maxCount) * 0.5})`}
                                  />
                                ))}
                              </Bar>
                              <ReferenceLine
                                x={chartData.reduce((best, d) => d.count > best.count ? d : best, chartData[0])?.range}
                                stroke="#7c3aed"
                                strokeDasharray="4 2"
                                strokeWidth={1}
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-40 bg-gray-50 rounded flex items-center justify-center">
                            <BarChart3 className="w-8 h-8 text-gray-300" />
                          </div>
                        )}

                        <div className="mt-2 grid grid-cols-4 gap-1 text-[10px]">
                          <div className="bg-purple-50 p-1.5 rounded text-center">
                            <div className="text-gray-400">Mean</div>
                            <div className="font-bold text-purple-700">{stat.mean.toFixed(2)}</div>
                          </div>
                          <div className="bg-blue-50 p-1.5 rounded text-center">
                            <div className="text-gray-400">Median</div>
                            <div className="font-bold text-blue-700">{typeof stat.median === 'number' ? stat.median.toFixed(2) : stat.median}</div>
                          </div>
                          <div className="bg-gray-50 p-1.5 rounded text-center">
                            <div className="text-gray-400">Std Dev</div>
                            <div className="font-bold text-gray-700">{stat.std.toFixed(2)}</div>
                          </div>
                          <div className="bg-amber-50 p-1.5 rounded text-center">
                            <div className="text-gray-400">Missing</div>
                            <div className={`font-bold ${stat.missing > 0 ? 'text-red-600' : 'text-green-600'}`}>{stat.missing}</div>
                          </div>
                        </div>
                        <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                          <span>Min: {typeof stat.min === 'number' ? stat.min.toFixed(2) : stat.min}</span>
                          <span>IQR: {typeof stat.q25 === 'number' && typeof stat.q75 === 'number' ? (stat.q75 - stat.q25).toFixed(2) : '—'}</span>
                          <span>Max: {typeof stat.max === 'number' ? stat.max.toFixed(2) : stat.max}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Correlations Tab */}
            {activeTab === 'correlations' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-1">Feature Correlations</h3>
                <p className="text-sm text-gray-500 mb-5">Pearson correlation coefficient between numeric columns (top 10 pairs by |r|)</p>

                {correlations.length === 0 ? (
                  <div className="text-center py-14 border-2 border-dashed border-gray-200 rounded-xl">
                    <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-600 font-medium text-sm">No significant correlations detected</p>
                    <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                      This can happen when numeric columns have very low variance, too many missing values,
                      or when the dataset has fewer than 2 numeric features.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Horizontal bar chart of |correlation| */}
                    <div className="border border-gray-200 rounded-xl p-4 bg-white mb-5">
                      <p className="text-xs text-gray-500 mb-3 font-medium">Correlation Strength (|r|)</p>
                      <ResponsiveContainer width="100%" height={correlations.length * 36 + 20}>
                        <BarChart
                          data={[...correlations].reverse().map(c => ({
                            pair: `${c.var1} × ${c.var2}`,
                            abs: Math.abs(c.correlation),
                            val: c.correlation,
                          }))}
                          layout="vertical"
                          margin={{ top: 0, right: 60, bottom: 0, left: 140 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                          <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} />
                          <YAxis dataKey="pair" type="category" tick={{ fontSize: 10, fill: '#374151' }} width={130} tickLine={false} axisLine={false} />
                          <Tooltip
                            formatter={(value, name, props) => [
                              `r = ${props.payload.val.toFixed(3)}`,
                              'Pearson r',
                            ]}
                            contentStyle={{ fontSize: 11, borderRadius: 8 }}
                          />
                          <Bar dataKey="abs" radius={[0, 3, 3, 0]}>
                            {[...correlations].reverse().map((c, idx) => (
                              <Cell
                                key={idx}
                                fill={c.correlation >= 0
                                  ? `rgba(124,58,237,${0.3 + Math.abs(c.correlation) * 0.7})`
                                  : `rgba(239,68,68,${0.3 + Math.abs(c.correlation) * 0.7})`}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Correlation table */}
                    <div className="border border-gray-200 rounded-xl overflow-hidden mb-5">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Variable 1</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Variable 2</th>
                            <th className="px-4 py-3 text-right font-semibold text-gray-700">Pearson r</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Direction</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Strength</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Visual</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {correlations.map((corr, i) => (
                            <tr key={i} className="hover:bg-gray-50">
                              <td className="px-4 py-3 font-medium text-gray-900">{corr.var1}</td>
                              <td className="px-4 py-3 font-medium text-gray-900">{corr.var2}</td>
                              <td className="px-4 py-3 text-right">
                                <span className={`font-bold text-base ${corr.correlation > 0 ? 'text-purple-700' : 'text-red-600'}`}>
                                  {corr.correlation.toFixed(3)}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                  corr.correlation > 0
                                    ? 'bg-purple-100 text-purple-700'
                                    : 'bg-red-100 text-red-700'
                                }`}>
                                  {corr.correlation > 0 ? '↑ Positive' : '↓ Negative'}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`capitalize text-xs font-semibold ${
                                  corr.strength === 'strong' ? 'text-green-700' :
                                  corr.strength === 'moderate' ? 'text-amber-600' : 'text-gray-500'
                                }`}>{corr.strength}</span>
                              </td>
                              <td className="px-4 py-3 min-w-[120px]">
                                <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden flex items-center">
                                  <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="w-px h-full bg-gray-300" />
                                  </div>
                                  {corr.correlation >= 0 ? (
                                    <div
                                      className="absolute left-1/2 h-full rounded-r-full"
                                      style={{
                                        width: `${Math.abs(corr.correlation) * 50}%`,
                                        backgroundColor: 'rgba(124,58,237,0.7)',
                                      }}
                                    />
                                  ) : (
                                    <div
                                      className="absolute right-1/2 h-full rounded-l-full"
                                      style={{
                                        width: `${Math.abs(corr.correlation) * 50}%`,
                                        backgroundColor: 'rgba(239,68,68,0.7)',
                                      }}
                                    />
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                {/* Info box */}
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl flex items-start gap-3">
                  <Info className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-purple-900">
                    <strong>Interpretation Guide:</strong> Pearson r ranges from −1 to +1.
                    Purple bars = positive (both variables increase together), Red = negative (inverse).
                    |r| ≥ 0.7 → strong, 0.5–0.7 → moderate, 0.3–0.5 → weak, &lt;0.3 → negligible.
                  </div>
                </div>
              </div>
            )}
            
            {/* Categories Tab */}
            {activeTab === 'categories' && (
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-1">Categorical Variables</h3>
                <p className="text-sm text-gray-500 mb-5">{categoricalStats.length} categorical columns — distribution of each value shown below</p>

                <div className="space-y-6">
                  {categoricalStats.map((cat, i) => {
                    // Determine class balance insight
                    const topPct = cat.topPercent || 0;
                    const isImbalanced = topPct >= 70;
                    const isModerate = topPct >= 50 && topPct < 70;
                    const BAR_COLORS = ['#7c3aed','#6366f1','#3b82f6','#0ea5e9','#10b981','#f59e0b','#ef4444','#ec4899','#8b5cf6','#14b8a6'];

                    // Chart data: top 8 values for readability
                    const chartData = (cat.distribution || []).slice(0, 8).map(d => ({
                      value: String(d.value).length > 18 ? String(d.value).slice(0, 16) + '…' : String(d.value),
                      fullValue: String(d.value),
                      count: d.count,
                      percent: d.percent,
                    }));

                    return (
                      <div key={i} className="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-md transition-shadow">
                        {/* Column header */}
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-bold text-gray-900 text-base">{cat.column}</h4>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {cat.unique} unique values
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {isImbalanced && (
                              <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-semibold">
                                <AlertCircle className="w-3 h-3" /> Class Imbalance
                              </span>
                            )}
                            {isModerate && (
                              <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold">
                                <Info className="w-3 h-3" /> Moderately Skewed
                              </span>
                            )}
                            {!isImbalanced && !isModerate && (
                              <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-50 border border-green-200 text-green-700 text-xs font-semibold">
                                ✓ Balanced
                              </span>
                            )}
                            <span className="px-2.5 py-1 rounded-full bg-purple-50 border border-purple-200 text-purple-700 text-xs font-semibold">
                              Top: {cat.topValue} ({topPct}%)
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-5 gap-4">
                          {/* Bar chart */}
                          <div className="col-span-3">
                            <ResponsiveContainer width="100%" height={Math.max(180, chartData.length * 36)}>
                              <BarChart
                                data={chartData}
                                layout="vertical"
                                margin={{ top: 0, right: 55, bottom: 0, left: 8 }}
                                barSize={18}
                              >
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
                                <XAxis type="number" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                                <YAxis
                                  dataKey="value"
                                  type="category"
                                  tick={{ fontSize: 11, fill: '#374151', fontWeight: 500 }}
                                  width={110}
                                  tickLine={false}
                                  axisLine={false}
                                />
                                <Tooltip
                                  formatter={(val, name, props) => [
                                    `${val} records (${props.payload.percent}%)`,
                                    props.payload.fullValue,
                                  ]}
                                  contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
                                />
                                <Bar dataKey="count" radius={[0, 4, 4, 0]} label={{ position: 'right', fontSize: 10, fill: '#6b7280', formatter: (v) => `${v}` }}>
                                  {chartData.map((_, idx) => (
                                    <Cell key={idx} fill={BAR_COLORS[idx % BAR_COLORS.length]} />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>

                          {/* Percent breakdown table */}
                          <div className="col-span-2 flex flex-col justify-center gap-1">
                            <p className="text-xs text-gray-400 font-semibold mb-1 uppercase tracking-wide">% Breakdown</p>
                            {chartData.map((d, j) => (
                              <div key={j} className="flex items-center gap-2">
                                <div
                                  className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                                  style={{ backgroundColor: BAR_COLORS[j % BAR_COLORS.length] }}
                                />
                                <span className="text-xs text-gray-600 truncate flex-1" title={d.fullValue}>{d.value}</span>
                                <span className="text-xs font-bold text-gray-800 flex-shrink-0">{d.percent}%</span>
                              </div>
                            ))}
                            {(cat.distribution || []).length > 8 && (
                              <p className="text-[10px] text-gray-400 mt-1 italic">+ {cat.distribution.length - 8} more values</p>
                            )}
                          </div>
                        </div>

                        {/* Insight bar */}
                        <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-3 gap-2 text-[11px]">
                          <div className="bg-gray-50 rounded-lg p-2 text-center">
                            <div className="text-gray-400">Unique Values</div>
                            <div className="font-bold text-gray-800 text-sm">{cat.unique}</div>
                          </div>
                          <div className="bg-purple-50 rounded-lg p-2 text-center">
                            <div className="text-gray-400">Dominant Class</div>
                            <div className="font-bold text-purple-700 truncate" title={cat.topValue}>{cat.topValue}</div>
                          </div>
                          <div className={`rounded-lg p-2 text-center ${isImbalanced ? 'bg-red-50' : 'bg-green-50'}`}>
                            <div className="text-gray-400">Dominant %</div>
                            <div className={`font-bold text-sm ${isImbalanced ? 'text-red-600' : 'text-green-600'}`}>{topPct}%</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
          </div>
        </div>
        
      </div>
    </DashboardLayout>
  );
}
