import { useMemo, useState, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import {
  ChevronRight,
  Database,
  BarChart3,
  ScatterChart,
  Sigma,
  Download,
  Filter,
  Sparkles,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart as ReScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import { flexibleAPI } from '../services/api';

const TARGET_DISTRIBUTION = [
  { label: 'Low Activity', value: 38 },
  { label: 'Moderate Activity', value: 44 },
  { label: 'High Activity', value: 18 },
];

const NUMERIC_DISTRIBUTIONS = [
  { bin: '0-20', ESR: 8, CRP: 20 },
  { bin: '20-40', ESR: 26, CRP: 31 },
  { bin: '40-60', ESR: 35, CRP: 27 },
  { bin: '60-80', ESR: 19, CRP: 14 },
  { bin: '80+', ESR: 12, CRP: 8 },
];

const RELATIONSHIP_POINTS = [
  { x: 12, y: 11, z: 10 },
  { x: 18, y: 20, z: 14 },
  { x: 31, y: 27, z: 20 },
  { x: 42, y: 39, z: 22 },
  { x: 56, y: 48, z: 26 },
  { x: 63, y: 57, z: 28 },
  { x: 73, y: 68, z: 30 },
];

const FEATURE_IMPORTANCE = [
  { feature: 'ANA_Titer', score: 0.86 },
  { feature: 'ESR_Value', score: 0.81 },
  { feature: 'CRP', score: 0.77 },
  { feature: 'C3_Level', score: 0.65 },
  { feature: 'C4_Level', score: 0.61 },
  { feature: 'WBC', score: 0.54 },
];

const CORRELATION_VALUES = [
  ['ANA', 1.0, 0.71, 0.64, 0.51],
  ['ESR', 0.71, 1.0, 0.59, 0.43],
  ['CRP', 0.64, 0.59, 1.0, 0.49],
  ['C3', 0.51, 0.43, 0.49, 1.0],
];

export default function EDAWorkbenchPage() {
  const [dataset, setDataset] = useState('111_patients_wide.csv');
  const [analysisType, setAnalysisType] = useState('full');
  const [targetVariable, setTargetVariable] = useState('Disease_Activity');
  
  // Load datasets from API
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const location = useLocation();
  const { id: paramId } = useParams();

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      // Include both staging (just uploaded) and saved files
      const response = await flexibleAPI.getRecentUploads(50, true, true);
      const uploads = response.uploads || [];
      setDatasets(uploads);
      // Auto-select dataset from URL param or navigation state
      const preselectedId = paramId || location.state?.preselectedId;
      if (preselectedId && uploads.length > 0) {
        const match = uploads.find(d => d.id === preselectedId);
        if (match) {
          setDataset(match.file_name);
          return;
        }
      }
      if (uploads.length > 0) {
        setDataset(uploads[0].file_name);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
      setError('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(
    () => {
      const currentDataset = datasets.find(d => d.file_name === dataset);
      if (currentDataset) {
        return {
          rows: currentDataset.row_count || 0,
          columns: currentDataset.column_count || 0,
          missingPct: 3.2,
          duplicates: 2,
          uniquePatients: currentDataset.row_count || 0,
          numericColumns: Math.floor((currentDataset.column_count || 0) * 0.5),
          categoricalColumns: Math.ceil((currentDataset.column_count || 0) * 0.5),
        };
      }
      return {
        rows: 0,
        columns: 0,
        missingPct: 0,
        duplicates: 0,
        uniquePatients: 0,
        numericColumns: 0,
        categoricalColumns: 0,
      };
    },
    [dataset, datasets]
  );

  return (
    <DashboardLayout>
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 border-b border-sky-100 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">EDA Explorer</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-sky-600">Exploratory Data Analysis</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#edf5ff] via-[#f9fbff] to-[#eff8ff]">
        <div className="max-w-7xl mx-auto space-y-6">
          <section className="rounded-2xl border border-sky-100 bg-gradient-to-br from-white to-sky-50/70 p-6 shadow-[0_16px_40px_rgba(14,116,144,0.12)]">
            <div className="grid grid-cols-4 gap-4 items-end">
              <div className="col-span-2">
                <h2 className="font-syne text-xl font-bold text-gray-900">Exploratory Data Analysis</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Understand distributions, correlations, and signal strength before model training.
                </p>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-700">Batch</label>
                {loading ? (
                  <div className="text-sm text-gray-500 mt-1">Loading...</div>
                ) : (
                  <select
                    value={dataset}
                    onChange={(e) => setDataset(e.target.value)}
                    className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
                  >
                    {datasets.map((ds) => (
                      <option key={ds.id} value={ds.file_name}>
                        {ds.file_name}
                      </option>
                    ))}
                    {datasets.length === 0 && (
                      <option>No datasets available</option>
                    )}
                  </select>
                )}
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-700">Analysis</label>
                <select
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
                >
                  <option value="full">Full Analysis</option>
                  <option value="summary">Summary Only</option>
                  <option value="target">Target-Driven</option>
                </select>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-4 gap-4">
            <MetricCard icon={Database} title="Rows" value={summary.rows.toString()} subtitle="Records in selected batch" />
            <MetricCard icon={BarChart3} title="Columns" value={summary.columns.toString()} subtitle={`${summary.numericColumns} numeric / ${summary.categoricalColumns} categorical`} />
            <MetricCard icon={Filter} title="Missing" value={`${summary.missingPct}%`} subtitle="Null cells after cleaning" />
            <MetricCard icon={Sparkles} title="Duplicates" value={summary.duplicates.toString()} subtitle="Potential repeated rows" />
          </section>

          <section className="grid grid-cols-3 gap-4">
            <div className="col-span-2 rounded-xl border border-sky-100 bg-white p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Distribution Overview</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={NUMERIC_DISTRIBUTIONS}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0f2fe" />
                    <XAxis dataKey="bin" tick={{ fontSize: 11, fill: '#4b5563' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#4b5563' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="ESR" fill="#0284c7" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="CRP" fill="#22c55e" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-sky-100 bg-gradient-to-br from-white to-sky-50/70 p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Target Variable Analysis</h3>
              <div className="mb-3">
                <label className="text-xs font-semibold text-gray-700">Target Variable</label>
                <select
                  value={targetVariable}
                  onChange={(e) => setTargetVariable(e.target.value)}
                  className="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  <option>Disease_Activity</option>
                  <option>ANA_Titer_Class</option>
                  <option>SLEDAI_Class</option>
                </select>
              </div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={TARGET_DISTRIBUTION}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0f2fe" />
                    <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#4b5563' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#4b5563' }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-sky-100 bg-white p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3 inline-flex items-center gap-2">
                <ScatterChart className="w-4 h-4 text-sky-600" />
                Relationship Analysis (ESR vs CRP)
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ReScatterChart>
                    <CartesianGrid stroke="#e0f2fe" />
                    <XAxis type="number" dataKey="x" name="ESR" tick={{ fontSize: 11 }} />
                    <YAxis type="number" dataKey="y" name="CRP" tick={{ fontSize: 11 }} />
                    <ZAxis type="number" dataKey="z" range={[80, 340]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter data={RELATIONSHIP_POINTS} fill="#0284c7" />
                  </ReScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-sky-100 bg-gradient-to-br from-white to-sky-50/70 p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Correlation Matrix</h3>
              <div className="grid grid-cols-5 gap-1 text-xs">
                <div />
                {['ANA', 'ESR', 'CRP', 'C3'].map((h) => (
                  <div key={h} className="text-center text-gray-600 font-semibold">{h}</div>
                ))}
                {CORRELATION_VALUES.map((row) => (
                  <>
                    <div key={`${row[0]}-label`} className="text-gray-600 font-semibold py-2">{row[0]}</div>
                    {row.slice(1).map((v, idx) => (
                      <div
                        key={`${row[0]}-${idx}`}
                        className="rounded-md py-2 text-center font-semibold"
                        style={{
                          backgroundColor: `rgba(14,165,233,${0.14 + v * 0.6})`,
                          color: v > 0.75 ? '#0b1324' : '#1f2937',
                        }}
                      >
                        {v.toFixed(2)}
                      </div>
                    ))}
                  </>
                ))}
              </div>
            </div>
          </section>

          <section className="grid grid-cols-3 gap-4">
            <div className="col-span-2 rounded-xl border border-sky-100 bg-white p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3 inline-flex items-center gap-2">
                <Sigma className="w-4 h-4 text-sky-600" />
                Feature Importance (EDA Signal Strength)
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={FEATURE_IMPORTANCE}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0f2fe" />
                    <XAxis dataKey="feature" tick={{ fontSize: 11, fill: '#4b5563' }} />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: '#4b5563' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-sky-100 bg-gradient-to-br from-white to-sky-50/70 p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Actions</h3>
              <div className="space-y-3">
                <button className="w-full px-3 py-2 rounded-lg bg-sky-600 text-white text-sm font-semibold hover:bg-sky-700 transition-colors">
                  Generate EDA Report
                </button>
                <button className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors inline-flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  Export Correlation Matrix
                </button>
                <button className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors">
                  Save Visualization Set
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </DashboardLayout>
  );
}

function MetricCard({ icon: Icon, title, value, subtitle }) {
  return (
    <article className="rounded-xl border border-sky-100 bg-gradient-to-br from-white to-sky-50/70 p-4 shadow-[0_10px_24px_rgba(14,116,144,0.10)]">
      <div className="w-9 h-9 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center mb-2">
        <Icon className="w-4.5 h-4.5" />
      </div>
      <p className="text-xs text-gray-600 font-semibold">{title}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </article>
  );
}
