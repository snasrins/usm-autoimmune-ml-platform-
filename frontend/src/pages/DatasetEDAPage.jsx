/**
 * Dataset EDA (Exploratory Data Analysis) Page
 * Professional data exploration with interactive visualizations
 */

import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart, Cell
} from 'recharts';
import {
  ArrowLeft, Download, TrendingUp, AlertTriangle,
  Database, BarChart3, Activity, FileText, Hash,
  Tag, Percent, Table2, GitBranch, Layers
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { flexibleAPI } from '../services/api';

const CHART_COLORS = ['#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444', '#6366F1', '#14B8A6'];

const TABS = [
  { id: 'overview',      label: 'Overview',      icon: Table2   },
  { id: 'statistics',    label: 'Statistics',     icon: BarChart3 },
  { id: 'distributions', label: 'Distributions',  icon: Activity  },
  { id: 'categorical',   label: 'Categorical',    icon: Tag       },
  { id: 'correlations',  label: 'Correlations',   icon: GitBranch },
  { id: 'quality',       label: 'Data Quality',   icon: Layers    },
];

export default function DatasetEDAPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId, datasetName } = location.state || {};

  const [loading, setLoading]             = useState(true);
  const [activeTab, setActiveTab]         = useState('overview');
  const [previewData, setPreviewData]     = useState(null);
  const [statistics,  setStatistics]      = useState({});
  const [columnTypes, setColumnTypes]     = useState({});
  const [missingValues, setMissingValues] = useState([]);
  const [distributions, setDistributions] = useState({});
  const [categoricalData, setCategoricalData] = useState({});
  const [correlations, setCorrelations]   = useState([]);
  const [outliers, setOutliers]           = useState({});
  const [summaryStats, setSummaryStats]   = useState({});

  useEffect(() => {
    if (datasetId) loadEDAData();
    else navigate('/ml-preparation');
  }, [datasetId]);

  const loadEDAData = async () => {
    setLoading(true);
    try {
      const preview = await flexibleAPI.getSavedDatasetPreview(datasetId, 1, 100);
      const normalizedPreview = {
        rows: preview.rows || [],
        columns: preview.columns || (preview.rows?.length > 0
          ? Object.keys(preview.rows[0].data || {}) : []),
        total_rows: preview.total_rows || preview.rows?.length || 0
      };
      setPreviewData(normalizedPreview);
      if (normalizedPreview.rows.length > 0) processDataForEDA(normalizedPreview);
    } catch (error) {
      console.error('Failed to load EDA data:', error);
    } finally {
      setLoading(false);
    }
  };

  const processDataForEDA = (preview) => {
    const { rows, columns, total_rows } = preview;
    if (!rows.length || !columns.length) return;

    const types = {}, stats = {}, dists = {}, catData = {}, outlierData = {};
    const missingArr = [];

    columns.forEach(col => {
      const allValues = rows.map(r => r.data?.[col]);
      const values    = allValues.filter(v => v !== null && v !== undefined && v !== '');
      const nullCount = rows.length - values.length;
      const nullPct   = (nullCount / rows.length) * 100;
      if (nullCount > 0) missingArr.push({ column: col, count: nullCount, percentage: parseFloat(nullPct.toFixed(1)) });

      const numericVals = values.map(v => parseFloat(v)).filter(v => !isNaN(v));
      const isNumeric   = numericVals.length > 0 && numericVals.length >= values.length * 0.8;
      types[col] = isNumeric ? 'numeric' : 'categorical';

      if (isNumeric) {
        const sorted = [...numericVals].sort((a, b) => a - b);
        const n = numericVals.length;
        const mean = numericVals.reduce((a, b) => a + b, 0) / n;
        const std  = Math.sqrt(numericVals.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / n);
        const q1   = sorted[Math.floor(n * 0.25)];
        const med  = sorted[Math.floor(n * 0.5)];
        const q3   = sorted[Math.floor(n * 0.75)];
        const min  = sorted[0], max = sorted[n - 1];

        stats[col] = {
          count: n, mean: mean.toFixed(3), std: std.toFixed(3),
          min: min.toFixed(3), q1: q1.toFixed(3), median: med.toFixed(3),
          q3: q3.toFixed(3), max: max.toFixed(3)
        };

        const bins = 15, range = max - min;
        if (range > 0) {
          const binSize = range / bins;
          const counts  = Array(bins).fill(0);
          numericVals.forEach(v => { const idx = Math.min(Math.floor((v - min) / binSize), bins - 1); counts[idx]++; });
          dists[col] = counts.map((count, i) => ({ bin: (min + binSize * i).toFixed(2), count }));
        }

        const iqr = q3 - q1, lo = q1 - 1.5 * iqr, hi = q3 + 1.5 * iqr;
        const outs = numericVals.filter(v => v < lo || v > hi);
        outlierData[col] = { count: outs.length, percentage: (outs.length / n * 100).toFixed(1), lowerBound: lo.toFixed(3), upperBound: hi.toFixed(3) };
      } else {
        const freq = {};
        values.forEach(v => { const k = String(v); freq[k] = (freq[k] || 0) + 1; });
        const unique  = Object.keys(freq).length;
        const topVals = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 8)
          .map(([value, count]) => ({ value, count, percentage: +(count / values.length * 100).toFixed(1) }));
        stats[col]   = { count: values.length, unique, top: topVals[0]?.value, topFreq: topVals[0]?.count };
        catData[col] = topVals;
      }
    });

    setColumnTypes(types);
    setStatistics(stats);
    setDistributions(dists);
    setCategoricalData(catData);
    setMissingValues(missingArr.sort((a, b) => b.percentage - a.percentage));
    setOutliers(outlierData);

    const numCols = columns.filter(c => types[c] === 'numeric');
    if (numCols.length >= 2) {
      const corrArr = [];
      for (let i = 0; i < numCols.length; i++) {
        for (let j = i + 1; j < numCols.length; j++) {
          const c1 = numCols[i], c2 = numCols[j];
          const v1 = rows.map(r => parseFloat(r.data?.[c1])).filter(v => !isNaN(v));
          const v2 = rows.map(r => parseFloat(r.data?.[c2])).filter(v => !isNaN(v));
          if (v1.length > 1 && v2.length > 1) {
            const n = Math.min(v1.length, v2.length);
            const mx = v1.slice(0,n).reduce((a,b)=>a+b,0)/n, my = v2.slice(0,n).reduce((a,b)=>a+b,0)/n;
            let num=0,dx2=0,dy2=0;
            for (let k=0;k<n;k++){const dx=v1[k]-mx,dy=v2[k]-my;num+=dx*dy;dx2+=dx*dx;dy2+=dy*dy;}
            const r = num/Math.sqrt(dx2*dy2);
            if (!isNaN(r)) corrArr.push({ col1: c1, col2: c2, correlation: +r.toFixed(3), absCorr: Math.abs(r) });
          }
        }
      }
      setCorrelations(corrArr.sort((a,b)=>b.absCorr-a.absCorr).slice(0,15));
    }

    const numericCount = Object.values(types).filter(t=>t==='numeric').length;
    const totalMissing = missingArr.reduce((s,m)=>s+m.count,0);
    const missingPct   = columns.length>0 ? (totalMissing/(rows.length*columns.length)*100).toFixed(1) : '0.0';
    setSummaryStats({
      rows: total_rows, cols: columns.length,
      numericCols: numericCount, categoricalCols: columns.length-numericCount,
      missingPct, colsWithOutliers: Object.values(outlierData).filter(o=>o.count>0).length
    });
  };

  const downloadReport = () => {
    const blob = new Blob([JSON.stringify({ dataset_name: datasetName, generated_at: new Date().toISOString(), summaryStats, statistics, column_types: columnTypes, missing_values: missingValues, correlations, outliers }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download=`eda_${datasetId?.substring(0,8)}.json`; a.click();
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen bg-[#FAFBFC]">
          <div className="text-center">
            <div className="w-14 h-14 rounded-full border-4 border-purple-100 border-t-purple-600 animate-spin mx-auto mb-5" />
            <p className="text-[15px] font-medium text-gray-700">Analysing dataset…</p>
            <p className="text-[13px] text-gray-400 mt-1">Computing statistics and visualisations</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const numericCols     = Object.keys(columnTypes).filter(c => columnTypes[c] === 'numeric');
  const categoricalCols = Object.keys(columnTypes).filter(c => columnTypes[c] === 'categorical');

  return (
    <DashboardLayout>
      {/* Top Bar */}
      <div className="h-[62px] flex items-center gap-4 px-6 bg-white border-b border-gray-200 flex-shrink-0">
        <button onClick={() => navigate('/ml-preparation')} className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors text-[13px] font-medium">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="w-px h-5 bg-gray-200" />
        <div>
          <h1 className="font-syne text-[15px] font-bold text-[#0F0F11] leading-none">Exploratory Data Analysis</h1>
          <p className="text-[11px] text-gray-400 mt-0.5 truncate max-w-[380px]">{datasetName}</p>
        </div>
        <div className="ml-auto">
          <button onClick={downloadReport} className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold text-white" style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)' }}>
            <Download className="w-3.5 h-3.5" /> Export Report
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 overflow-y-auto" style={{ background: '#FAFBFC', zoom: 0.78 }}>
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-5">

          {/* Summary Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Total Rows',   value: summaryStats.rows?.toLocaleString() ?? '—',                                icon: Database,      color: 'bg-purple-50 text-purple-700 border-purple-100' },
              { label: 'Columns',      value: summaryStats.cols ?? '—',                                                  icon: Table2,        color: 'bg-blue-50 text-blue-700 border-blue-100' },
              { label: 'Numerical',    value: summaryStats.numericCols ?? '—',                                           icon: Hash,          color: 'bg-green-50 text-green-700 border-green-100' },
              { label: 'Categorical',  value: summaryStats.categoricalCols ?? '—',                                       icon: Tag,           color: 'bg-pink-50 text-pink-700 border-pink-100' },
              { label: 'Missing Data', value: summaryStats.missingPct != null ? `${summaryStats.missingPct}%` : '—',     icon: Percent,       color: 'bg-yellow-50 text-yellow-700 border-yellow-100' },
              { label: 'Outlier Cols', value: summaryStats.colsWithOutliers ?? '—',                                      icon: AlertTriangle, color: 'bg-red-50 text-red-700 border-red-100' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className={`rounded-xl border p-4 flex items-center gap-3 ${color}`}>
                <Icon className="w-5 h-5 flex-shrink-0" />
                <div><p className="text-[11px] font-medium opacity-70">{label}</p><p className="text-[20px] font-bold leading-tight">{value}</p></div>
              </div>
            ))}
          </div>

          {/* Tabs Card */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Tab Bar */}
            <div className="flex border-b border-gray-200 overflow-x-auto">
              {TABS.map(tab => {
                const Icon = tab.icon;
                const active = activeTab === tab.id;
                return (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-5 py-3.5 text-[13px] font-semibold whitespace-nowrap border-b-2 transition-colors ${
                      active ? 'border-purple-600 text-purple-700 bg-purple-50/50' : 'border-transparent text-gray-500 hover:text-gray-800 hover:bg-gray-50'
                    }`}>
                    <Icon className="w-4 h-4" />{tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
              <motion.div key={activeTab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.15 }} className="p-6">

                {/* OVERVIEW */}
                {activeTab === 'overview' && (
                  <div className="space-y-4">
                    <p className="text-[13px] text-gray-500">
                      Showing first <span className="font-semibold text-gray-800">{Math.min(previewData?.rows?.length ?? 0, 15)}</span> of{' '}
                      <span className="font-semibold text-gray-800">{summaryStats.rows?.toLocaleString()}</span> rows ·{' '}
                      <span className="font-semibold text-gray-800">{Math.min(previewData?.columns?.length ?? 0, 12)}</span> of{' '}
                      <span className="font-semibold text-gray-800">{summaryStats.cols}</span> columns
                    </p>
                    {previewData?.rows?.length > 0 ? (
                      <div className="overflow-x-auto rounded-lg border border-gray-200">
                        <table className="w-full text-[12.5px]">
                          <thead>
                            <tr style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)' }}>
                              <th className="px-3 py-2.5 text-left text-white font-semibold w-10">#</th>
                              {(previewData.columns || []).slice(0, 12).map(col => (
                                <th key={col} className="px-3 py-2.5 text-left text-white font-semibold whitespace-nowrap">
                                  {col}<span className="ml-1.5 font-normal opacity-70 text-[10px]">{columnTypes[col]==='numeric'?'(num)':'(cat)'}</span>
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {previewData.rows.slice(0, 15).map((row, idx) => (
                              <tr key={idx} className={idx%2===0?'bg-white':'bg-gray-50/70'}>
                                <td className="px-3 py-2 text-gray-400 font-mono text-[11px]">{idx+1}</td>
                                {(previewData.columns || []).slice(0, 12).map(col => {
                                  const val = row.data?.[col];
                                  const empty = val===null||val===undefined||val==='';
                                  return (
                                    <td key={col} className="px-3 py-2 text-gray-700 max-w-[150px] truncate">
                                      {empty ? <span className="text-gray-300 italic text-[11px]">null</span>
                                             : <span title={String(val)}>{String(val).substring(0,25)}{String(val).length>25?'…':''}</span>}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : <EmptyState message="No preview data available" />}

                    <div className="grid grid-cols-2 gap-4 mt-2">
                      {[
                        { label: 'Numerical Columns', cols: numericCols,     color: 'border-purple-100 bg-purple-50/40', hdr: 'text-purple-700', tag: 'bg-purple-100 text-purple-800' },
                        { label: 'Categorical Columns', cols: categoricalCols, color: 'border-pink-100 bg-pink-50/40',   hdr: 'text-pink-700',   tag: 'bg-pink-100 text-pink-800' },
                      ].map(({ label, cols, color, hdr, tag }) => (
                        <div key={label} className={`rounded-lg border p-4 ${color}`}>
                          <h4 className={`text-[12px] font-semibold mb-2 uppercase tracking-wide ${hdr}`}>{label} ({cols.length})</h4>
                          <div className="flex flex-wrap gap-1.5">
                            {cols.map(c => <span key={c} className={`px-2 py-0.5 rounded text-[11px] font-medium ${tag}`}>{c}</span>)}
                            {cols.length===0 && <span className="text-[12px] text-gray-400 italic">None detected</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* STATISTICS */}
                {activeTab === 'statistics' && (
                  <div className="space-y-5">
                    {numericCols.length > 0 && (
                      <div>
                        <h3 className="text-[13px] font-bold text-gray-800 mb-3 flex items-center gap-2"><Hash className="w-4 h-4 text-purple-600" /> Numerical Statistics</h3>
                        <div className="overflow-x-auto rounded-lg border border-gray-200">
                          <table className="w-full text-[12.5px]">
                            <thead><tr className="bg-gray-50 border-b border-gray-200">{['Column','Count','Mean','Std Dev','Min','Q1','Median','Q3','Max'].map(h=><th key={h} className="px-3 py-2.5 text-left font-semibold text-gray-600">{h}</th>)}</tr></thead>
                            <tbody>
                              {numericCols.map((col,idx)=>{
                                const s=statistics[col]; if(!s) return null;
                                return (<tr key={col} className={idx%2===0?'bg-white':'bg-gray-50/60'}>
                                  <td className="px-3 py-2 font-semibold text-gray-900">{col}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.count}</td>
                                  <td className="px-3 py-2 text-purple-700 font-mono font-medium">{s.mean}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.std}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.min}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.q1}</td>
                                  <td className="px-3 py-2 text-blue-700 font-mono font-medium">{s.median}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.q3}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.max}</td>
                                </tr>);
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    {categoricalCols.length > 0 && (
                      <div>
                        <h3 className="text-[13px] font-bold text-gray-800 mb-3 flex items-center gap-2"><Tag className="w-4 h-4 text-pink-600" /> Categorical Statistics</h3>
                        <div className="overflow-x-auto rounded-lg border border-gray-200">
                          <table className="w-full text-[12.5px]">
                            <thead><tr className="bg-gray-50 border-b border-gray-200">{['Column','Count','Unique Values','Most Frequent','Frequency'].map(h=><th key={h} className="px-3 py-2.5 text-left font-semibold text-gray-600">{h}</th>)}</tr></thead>
                            <tbody>
                              {categoricalCols.map((col,idx)=>{
                                const s=statistics[col]; if(!s) return null;
                                return (<tr key={col} className={idx%2===0?'bg-white':'bg-gray-50/60'}>
                                  <td className="px-3 py-2 font-semibold text-gray-900">{col}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.count}</td>
                                  <td className="px-3 py-2"><span className="px-2 py-0.5 bg-pink-100 text-pink-700 rounded text-[11px] font-semibold">{s.unique}</span></td>
                                  <td className="px-3 py-2 text-gray-700 max-w-[200px] truncate" title={s.top}>{s.top??'—'}</td>
                                  <td className="px-3 py-2 text-gray-600 font-mono">{s.topFreq??'—'}</td>
                                </tr>);
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    {numericCols.length===0&&categoricalCols.length===0&&<EmptyState message="No statistics computed" />}
                  </div>
                )}

                {/* DISTRIBUTIONS */}
                {activeTab === 'distributions' && (
                  Object.keys(distributions).length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                      {Object.entries(distributions).map(([col, data], i) => (
                        <div key={col} className="rounded-xl border border-gray-200 bg-white p-4 hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="text-[13px] font-semibold text-gray-800 truncate">{col}</h4>
                            <span className="text-[10px] font-medium text-purple-600 bg-purple-50 px-2 py-0.5 rounded">numerical</span>
                          </div>
                          <ResponsiveContainer width="100%" height={180}>
                            <AreaChart data={data} margin={{ top:4,right:4,bottom:4,left:-20 }}>
                              <defs>
                                <linearGradient id={`g${i}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%"  stopColor="#8B5CF6" stopOpacity={0.7}/>
                                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.05}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6"/>
                              <XAxis dataKey="bin" tick={{fontSize:9}} stroke="#D1D5DB" tickLine={false}/>
                              <YAxis tick={{fontSize:9}} stroke="#D1D5DB" tickLine={false} axisLine={false}/>
                              <Tooltip contentStyle={{background:'white',border:'1px solid #E5E7EB',borderRadius:8,fontSize:11}} labelFormatter={v=>`Value: ${v}`}/>
                              <Area type="monotone" dataKey="count" stroke="#8B5CF6" strokeWidth={2} fill={`url(#g${i})`}/>
                            </AreaChart>
                          </ResponsiveContainer>
                          {statistics[col] && (
                            <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                              {[['Mean',statistics[col].mean],['Median',statistics[col].median],['Std',statistics[col].std]].map(([lbl,val])=>(
                                <div key={lbl} className="bg-gray-50 rounded-lg py-1.5">
                                  <p className="text-[9px] text-gray-400 font-medium uppercase">{lbl}</p>
                                  <p className="text-[12px] font-bold text-gray-800 font-mono">{val}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : <EmptyState message="No numerical columns found for distribution analysis" />
                )}

                {/* CATEGORICAL */}
                {activeTab === 'categorical' && (
                  Object.keys(categoricalData).length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      {Object.entries(categoricalData).slice(0, 8).map(([col, data]) => (
                        <div key={col} className="rounded-xl border border-gray-200 bg-white p-4 hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="text-[13px] font-semibold text-gray-800 truncate">{col}</h4>
                            <span className="text-[10px] font-medium text-pink-600 bg-pink-50 px-2 py-0.5 rounded">{statistics[col]?.unique??'?'} unique</span>
                          </div>
                          <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={data} layout="vertical" margin={{left:8,right:8}}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" horizontal={false}/>
                              <XAxis type="number" tick={{fontSize:10}} stroke="#D1D5DB" tickLine={false}/>
                              <YAxis dataKey="value" type="category" width={90} tick={{fontSize:10}} stroke="#D1D5DB" tickLine={false} axisLine={false}/>
                              <Tooltip contentStyle={{background:'white',border:'1px solid #E5E7EB',borderRadius:8,fontSize:11}} formatter={(v,n,p)=>[`${v} (${p.payload.percentage}%)`,'Count']}/>
                              <Bar dataKey="count" radius={[0,5,5,0]}>
                                {data.map((_,i)=><Cell key={i} fill={CHART_COLORS[i%CHART_COLORS.length]}/>)}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      ))}
                    </div>
                  ) : <EmptyState message="No categorical columns found" />
                )}

                {/* CORRELATIONS */}
                {activeTab === 'correlations' && (
                  <div className="space-y-4">
                    {correlations.length > 0 ? (
                      <>
                        <p className="text-[13px] text-gray-500">Top {correlations.length} feature correlations by absolute Pearson r</p>
                        <div className="space-y-2">
                          {correlations.map((corr, idx) => {
                            const pos = corr.correlation >= 0;
                            const pct = (corr.absCorr * 100).toFixed(0);
                            const strength = corr.absCorr>=0.8?'Very Strong':corr.absCorr>=0.6?'Strong':corr.absCorr>=0.4?'Moderate':'Weak';
                            return (
                              <div key={idx} className="flex items-center gap-4 p-3 rounded-lg bg-gray-50/70 hover:bg-gray-100/60 transition-colors">
                                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-gray-500 bg-white border border-gray-200">{idx+1}</div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-[12.5px] font-semibold text-gray-800 truncate">{corr.col1} <span className="text-gray-400">↔</span> {corr.col2}</span>
                                    <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                                      <span className={`text-[11px] px-2 py-0.5 rounded font-medium ${corr.absCorr>=0.6?'bg-purple-100 text-purple-700':'bg-gray-100 text-gray-600'}`}>{strength}</span>
                                      <span className={`text-[13px] font-bold font-mono ${pos?'text-green-600':'text-red-600'}`}>{corr.correlation>0?'+':''}{corr.correlation}</span>
                                    </div>
                                  </div>
                                  <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div className={`h-full rounded-full ${pos?'bg-gradient-to-r from-green-400 to-emerald-500':'bg-gradient-to-r from-red-400 to-rose-500'}`} style={{width:`${pct}%`}}/>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </>
                    ) : <EmptyState message={numericCols.length<2?'Need at least 2 numerical columns to compute correlations':'No significant correlations found'} />}
                  </div>
                )}

                {/* QUALITY */}
                {activeTab === 'quality' && (
                  <div className="space-y-6">
                    {/* Missing Values */}
                    <div>
                      <h3 className="text-[13px] font-bold text-gray-800 mb-3 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-yellow-500"/> Missing Values</h3>
                      {missingValues.length > 0 ? (
                        <>
                          <div className="mb-4 rounded-lg border border-gray-200 overflow-hidden">
                            <table className="w-full text-[12.5px]">
                              <thead><tr className="bg-gray-50 border-b border-gray-200">{['Column','Missing Count','Missing %','Severity'].map(h=><th key={h} className="px-3 py-2.5 text-left font-semibold text-gray-600">{h}</th>)}</tr></thead>
                              <tbody>
                                {missingValues.map((m,idx)=>{
                                  const sev=m.percentage>=30?{label:'High',cls:'bg-red-100 text-red-700'}:m.percentage>=10?{label:'Medium',cls:'bg-yellow-100 text-yellow-700'}:{label:'Low',cls:'bg-green-100 text-green-700'};
                                  return (<tr key={m.column} className={idx%2===0?'bg-white':'bg-gray-50/60'}>
                                    <td className="px-3 py-2 font-semibold text-gray-900">{m.column}</td>
                                    <td className="px-3 py-2 font-mono text-gray-600">{m.count}</td>
                                    <td className="px-3 py-2">
                                      <div className="flex items-center gap-2">
                                        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-[80px]"><div className="h-full bg-yellow-400 rounded-full" style={{width:`${Math.min(m.percentage,100)}%`}}/></div>
                                        <span className="font-mono text-gray-700">{m.percentage}%</span>
                                      </div>
                                    </td>
                                    <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${sev.cls}`}>{sev.label}</span></td>
                                  </tr>);
                                })}
                              </tbody>
                            </table>
                          </div>
                          <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={missingValues.slice(0,12)} margin={{bottom:40}}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6"/>
                              <XAxis dataKey="column" angle={-40} textAnchor="end" height={70} tick={{fontSize:10}} stroke="#D1D5DB"/>
                              <YAxis tick={{fontSize:10}} stroke="#D1D5DB" tickLine={false} unit="%"/>
                              <Tooltip contentStyle={{background:'white',border:'1px solid #E5E7EB',borderRadius:8,fontSize:11}} formatter={v=>[`${v}%`,'Missing']}/>
                              <Bar dataKey="percentage" fill="#F59E0B" radius={[4,4,0,0]}/>
                            </BarChart>
                          </ResponsiveContainer>
                        </>
                      ) : (
                        <div className="rounded-lg border border-green-200 bg-green-50 p-4 flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold text-lg">✓</div>
                          <div><p className="font-semibold text-green-800 text-[13px]">No Missing Values</p><p className="text-green-600 text-[12px]">All columns are complete — great data quality!</p></div>
                        </div>
                      )}
                    </div>

                    {/* Outliers */}
                    <div>
                      <h3 className="text-[13px] font-bold text-gray-800 mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-red-500"/> Outlier Detection (IQR Method)</h3>
                      {Object.entries(outliers).some(([,o])=>o.count>0) ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                          {Object.entries(outliers).filter(([,o])=>o.count>0).slice(0,9).map(([col,data])=>(
                            <div key={col} className="rounded-xl border border-red-100 bg-red-50/40 p-4">
                              <h4 className="font-semibold text-[13px] text-gray-800 truncate mb-3">{col}</h4>
                              <div className="space-y-1.5 text-[12px]">
                                <div className="flex justify-between"><span className="text-gray-500">Outliers</span><span className="font-bold text-red-600">{data.count} ({data.percentage}%)</span></div>
                                <div className="flex justify-between"><span className="text-gray-500">Lower fence</span><span className="font-mono text-gray-700">{data.lowerBound}</span></div>
                                <div className="flex justify-between"><span className="text-gray-500">Upper fence</span><span className="font-mono text-gray-700">{data.upperBound}</span></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-lg border border-green-200 bg-green-50 p-4 flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold text-lg">✓</div>
                          <div><p className="font-semibold text-green-800 text-[13px]">No Outliers Detected</p><p className="text-green-600 text-[12px]">All numerical columns are within expected bounds.</p></div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function EmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <BarChart3 className="w-7 h-7 text-gray-300" />
      </div>
      <p className="text-[14px] font-medium text-gray-500">{message}</p>
    </div>
  );
}
