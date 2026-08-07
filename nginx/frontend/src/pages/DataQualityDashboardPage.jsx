import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import {
  ChevronLeft,
  ChevronRight,
  Database,
  CheckCircle,
  AlertTriangle,
  XCircle,
  TrendingUp,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

export default function DataQualityDashboardPage() {
  const navigate = useNavigate();
  const [selectedDataset, setSelectedDataset] = useState('all');
  const [timeRange, setTimeRange] = useState('7d');

  const qualityMetrics = {
    overall: 92.4,
    completeness: 94.2,
    consistency: 88.7,
    uniqueness: 99.1,
    validity: 91.5,
    timeliness: 87.3,
    accuracy: 93.8
  };

  const datasets = [
    {
      id: 1,
      name: 'HUSM_batch3.csv',
      records: 4284,
      quality: 98.2,
      status: 'excellent',
      issues: 12,
      validated: '2h ago'
    },
    {
      id: 2,
      name: 'combined_v2.csv',
      records: 8547,
      quality: 94.5,
      status: 'good',
      issues: 45,
      validated: '1d ago'
    },
    {
      id: 3,
      name: 'lab_tests_v4.csv',
      records: 12034,
      quality: 91.2,
      status: 'good',
      issues: 89,
      validated: '2d ago'
    },
    {
      id: 4,
      name: 'biomarkers_pilot.csv',
      records: 1523,
      quality: 78.4,
      status: 'warning',
      issues: 234,
      validated: '3d ago'
    },
    {
      id: 5,
      name: 'patient_cohort_v5.csv',
      records: 6891,
      quality: 85.7,
      status: 'fair',
      issues: 156,
      validated: '5d ago'
    }
  ];

  const qualityIssues = [
    {
      type: 'Missing Values',
      severity: 'high',
      count: 342,
      dataset: 'biomarkers_pilot.csv',
      column: 'ANA_titer',
      percentage: '22.4%'
    },
    {
      type: 'Duplicate Records',
      severity: 'medium',
      count: 45,
      dataset: 'combined_v2.csv',
      column: 'patient_id',
      percentage: '0.5%'
    },
    {
      type: 'Outliers',
      severity: 'low',
      count: 89,
      dataset: 'lab_tests_v4.csv',
      column: 'ESR_value',
      percentage: '0.7%'
    },
    {
      type: 'Invalid Format',
      severity: 'high',
      count: 156,
      dataset: 'patient_cohort_v5.csv',
      column: 'diagnosis_date',
      percentage: '2.3%'
    },
    {
      type: 'Inconsistent Values',
      severity: 'medium',
      count: 67,
      dataset: 'HUSM_batch3.csv',
      column: 'disease_activity',
      percentage: '1.6%'
    }
  ];

  return (
    <DashboardLayout>
      {/* ═══ TOPBAR ═══ */}
      <div className="h-[70px] flex items-center gap-8 px-12 bg-[#F5F5F7] border-b border-gray-200 flex-shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[20px] font-bold text-[#0F0F11] leading-none">Data Quality Dashboard</h1>
          <div className="flex items-center gap-3 text-[14px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0]">Data Quality</span>
          </div>
        </div>
        
        {/* Right side: Actions */}
        <div className="ml-auto flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-[#0F0F11] rounded-lg hover:bg-gray-50 transition-colors text-[12px] font-medium">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-[#0F0F11] hover:bg-[#0F0F11]/90 text-white rounded-lg transition-all text-[12px] font-medium">
            <Download className="w-3.5 h-3.5" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* ═══ CONTENT ═══ */}
      <main className="flex-1 overflow-y-auto p-6" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>

        {/* Filters */}
        <div className="flex gap-3 mb-6">
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-[12px] text-[#0F0F11] focus:outline-none focus:border-[#7B5CF0] focus:ring-3 focus:ring-[rgba(123,92,240,0.12)]"
          >
            <option value="all">All Datasets</option>
            {datasets.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-[12px] text-[#0F0F11] focus:outline-none focus:border-[#7B5CF0] focus:ring-3 focus:ring-[rgba(123,92,240,0.12)]"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="all">All time</option>
          </select>
        </div>

        {/* Quality Metrics Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <QualityMetricCard label="Overall Quality" value={qualityMetrics.overall} status="excellent" />
          <QualityMetricCard label="Completeness" value={qualityMetrics.completeness} status="excellent" />
          <QualityMetricCard label="Consistency" value={qualityMetrics.consistency} status="good" />
          <QualityMetricCard label="Validity" value={qualityMetrics.validity} status="good" />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {/* Quality Dimensions */}
          <div className="col-span-2 bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Quality Dimensions</h2>
            </div>
            <div className="p-6 space-y-4">
              <QualityDimension label="Completeness" value={qualityMetrics.completeness} description="% of non-null values" />
              <QualityDimension label="Consistency" value={qualityMetrics.consistency} description="Data format adherence" />
              <QualityDimension label="Uniqueness" value={qualityMetrics.uniqueness} description="Duplicate detection" />
              <QualityDimension label="Validity" value={qualityMetrics.validity} description="Schema compliance" />
              <QualityDimension label="Timeliness" value={qualityMetrics.timeliness} description="Data freshness" />
              <QualityDimension label="Accuracy" value={qualityMetrics.accuracy} description="Value correctness" />
            </div>
          </div>

          {/* Quality Trends */}
          <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="font-syne text-[13px] font-bold text-[#0F0F11]">Quality Trends</h2>
            </div>
            <div className="p-4 space-y-3">
              <TrendItem label="This Week" value="92.4%" change="+2.1%" positive />
              <TrendItem label="Last Week" value="90.3%" change="-1.5%" />
              <TrendItem label="Last Month" value="91.8%" change="+3.2%" positive />
              <div className="pt-3 mt-3 border-t border-gray-200">
                <div className="text-[10px] text-[#8585A0] mb-2">Quality Score History</div>
                <div className="h-24 flex items-end justify-between gap-1">
                  {[85, 88, 90, 87, 92, 94, 92, 91, 90, 93, 95, 92].map((val, idx) => (
                    <div key={idx} className="flex-1 bg-[#7B5CF0]/20 rounded-t" style={{ height: `${val}%` }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dataset Quality Table */}
        <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md mb-6">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Dataset Quality Overview</h2>
            <span className="text-[11px] text-[#8585A0] font-mono">{datasets.length} datasets</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead className="bg-white/50">
                <tr>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Dataset</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Records</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Quality Score</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Issues</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Status</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Last Validated</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {datasets.map((dataset) => (
                  <DatasetRow key={dataset.id} dataset={dataset} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quality Issues */}
        <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Quality Issues</h2>
            <span className="text-[11px] text-[#8585A0] font-mono">{qualityIssues.length} active issues</span>
          </div>
          <div className="p-6 space-y-3">
            {qualityIssues.map((issue, idx) => (
              <IssueCard key={idx} issue={issue} />
            ))}
          </div>
        </div>
      </main>
    </DashboardLayout>
  );
}

// Components
function QualityMetricCard({ label, value, status }) {
  const statusColors = {
    excellent: { bg: 'bg-[#10B981]/10', text: 'text-[#10B981]', icon: CheckCircle },
    good: { bg: 'bg-[#7B5CF0]/10', text: 'text-[#7B5CF0]', icon: CheckCircle },
    fair: { bg: 'bg-[#F59E0B]/10', text: 'text-[#F59E0B]', icon: AlertTriangle },
    warning: { bg: 'bg-[#EF4444]/10', text: 'text-[#EF4444]', icon: XCircle }
  };
  
  const s = statusColors[status];
  const Icon = s.icon;
  
  return (
    <div className={`${s.bg} rounded-2xl border border-gray-200 p-4`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-[11px] text-[#8585A0] font-medium">{label}</span>
        <Icon className={`w-4 h-4 ${s.text}`} />
      </div>
      <div className={`font-syne text-[32px] font-bold ${s.text} leading-none`}>{value}%</div>
    </div>
  );
}

function QualityDimension({ label, value, description }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-[12px] text-[#0F0F11] font-medium">{label}</div>
          <div className="text-[10px] text-[#8585A0] mt-0.5">{description}</div>
        </div>
        <span className="text-[13px] text-[#0F0F11] font-bold">{value}%</span>
      </div>
      <div className="h-2 bg-[#EFEFF2] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{
            width: `${value}%`,
            backgroundColor: value >= 95 ? '#10B981' : value >= 85 ? '#7B5CF0' : '#F59E0B'
          }}
        />
      </div>
    </div>
  );
}

function TrendItem({ label, value, change, positive }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-[#8585A0]">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-[12px] text-[#0F0F11] font-bold">{value}</span>
        <span className={`text-[10px] font-semibold ${positive ? 'text-[#10B981]' : 'text-[#8585A0]'}`}>
          {change}
        </span>
      </div>
    </div>
  );
}

function DatasetRow({ dataset }) {
  const statusColors = {
    excellent: { bg: 'bg-[#10B981]/10', text: 'text-[#10B981]', label: 'Excellent' },
    good: { bg: 'bg-[#7B5CF0]/10', text: 'text-[#7B5CF0]', label: 'Good' },
    fair: { bg: 'bg-[#F59E0B]/10', text: 'text-[#F59E0B]', label: 'Fair' },
    warning: { bg: 'bg-[#EF4444]/10', text: 'text-[#EF4444]', label: 'Warning' }
  };
  
  const s = statusColors[dataset.status];
  
  return (
    <tr className="hover:bg-white/50 transition-colors border-b border-gray-200 last:border-0">
      <td className="px-4 py-3 text-[#7B5CF0] font-semibold">{dataset.name}</td>
      <td className="px-4 py-3 text-[#0F0F11]">{dataset.records.toLocaleString()}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-[#EFEFF2] rounded-full overflow-hidden max-w-[80px]">
            <div
              className="h-full bg-[#7B5CF0]"
              style={{ width: `${dataset.quality}%` }}
            />
          </div>
          <span className="text-[#0F0F11] font-bold">{dataset.quality}%</span>
        </div>
      </td>
      <td className="px-4 py-3 text-[#0F0F11]">{dataset.issues}</td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full ${s.bg} ${s.text} text-[10px] font-bold`}>
          {s.label}
        </span>
      </td>
      <td className="px-4 py-3 text-[#8585A0]">{dataset.validated}</td>
    </tr>
  );
}

function IssueCard({ issue }) {
  const severityColors = {
    high: { bg: 'bg-[#EF4444]/10', text: 'text-[#EF4444]', border: 'border-[#EF4444]/20' },
    medium: { bg: 'bg-[#F59E0B]/10', text: 'text-[#F59E0B]', border: 'border-[#F59E0B]/20' },
    low: { bg: 'bg-[#3B82F6]/10', text: 'text-[#3B82F6]', border: 'border-[#3B82F6]/20' }
  };
  
  const s = severityColors[issue.severity];
  
  return (
    <div className={`flex items-start gap-4 p-4 rounded-xl border ${s.border} ${s.bg}`}>
      <AlertTriangle className={`w-5 h-5 ${s.text} flex-shrink-0 mt-0.5`} />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[13px] text-[#0F0F11] font-semibold">{issue.type}</span>
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${s.bg} ${s.text} font-bold uppercase`}>
            {issue.severity}
          </span>
        </div>
        <div className="text-[11px] text-[#8585A0] mb-2">
          {issue.count} occurrences in <span className="font-mono text-[#7B5CF0]">{issue.dataset}</span> · Column: <span className="font-mono">{issue.column}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-white/50 rounded-full overflow-hidden">
            <div className={`h-full ${s.text.replace('text-', 'bg-')}`} style={{ width: issue.percentage }} />
          </div>
          <span className={`text-[11px] font-bold ${s.text}`}>{issue.percentage}</span>
        </div>
      </div>
      <button className="text-[11px] text-[#7B5CF0] hover:underline font-medium flex-shrink-0">
        Fix Now
      </button>
    </div>
  );
}
