import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Database,
  BarChart3,
  TrendingUp,
  FileText,
  CheckCircle,
  AlertCircle,
  Eye,
  Download,
  Trash2,
  Calendar,
  HardDrive,
  Sparkles,
  ChevronRight,
  Search,
  Filter,
  Plus
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function EDAExplorerPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState([
    {
      id: 1,
      name: 'AAM-SLE-E (real data)',
      description: 'Primary patient cohort from HUSM',
      originalFilename: 'AAM-SLE-E (real data).xlsx',
      rowCount: 1204,
      columnCount: 18,
      fileSize: '0.05 MB',
      qualityScore: 94.2,
      uploadedAt: '2024-03-28 14:23',
      status: 'validated',
      hasReport: true
    },
    {
      id: 2,
      name: 'HUSM_batch3',
      description: 'Batch 3 clinical data',
      originalFilename: 'HUSM_batch3.csv',
      rowCount: 856,
      columnCount: 22,
      fileSize: '0.12 MB',
      qualityScore: 87.5,
      uploadedAt: '2024-03-27 09:15',
      status: 'validated',
      hasReport: true
    },
    {
      id: 3,
      name: 'Lab_values_cleaned',
      description: 'Preprocessed laboratory results',
      originalFilename: 'lab_values_cleaned.csv',
      rowCount: 2341,
      columnCount: 15,
      fileSize: '0.18 MB',
      qualityScore: 98.1,
      uploadedAt: '2024-03-26 16:42',
      status: 'validated',
      hasReport: true
    }
  ]);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         dataset.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || dataset.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white/60 backdrop-blur-sm border-b border-white/20">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-syne text-lg font-bold text-black-text">EDA Explorer</h1>
              <span className="px-2 py-0.5 rounded-md bg-purple-dim text-purple-primary text-[10px] font-semibold">
                {datasets.length} datasets
              </span>
            </div>
            <p className="text-xs text-gray-muted mt-0.5">Explore and analyze your datasets</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Upload Dataset
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            {/* Search & Filter Bar */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search datasets..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-white/40 bg-white/80 backdrop-blur-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 text-sm"
                />
              </div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/80 backdrop-blur-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 text-sm"
              >
                <option value="all">All Status</option>
                <option value="validated">Validated</option>
                <option value="processing">Processing</option>
                <option value="error">Error</option>
              </select>
            </div>

            {/* Dataset Grid */}
            <div className="grid grid-cols-1 gap-4">
              {filteredDatasets.map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>

            {filteredDatasets.length === 0 && (
              <div className="text-center py-16">
                <Database className="w-16 h-16 text-gray-muted/30 mx-auto mb-4" />
                <p className="text-gray-muted mb-2">No datasets found</p>
                <button
                  onClick={() => navigate('/')}
                  className="text-sm text-purple-primary hover:underline"
                >
                  Upload your first dataset
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function DatasetCard({ dataset }) {
  const getStatusConfig = (status) => {
    const configs = {
      validated: { color: 'text-green', bg: 'bg-green-dim', icon: CheckCircle, label: 'Validated' },
      processing: { color: 'text-amber', bg: 'bg-amber-dim', icon: TrendingUp, label: 'Processing' },
      error: { color: 'text-red', bg: 'bg-red-dim', icon: AlertCircle, label: 'Error' }
    };
    return configs[status] || configs.validated;
  };

  const statusConfig = getStatusConfig(dataset.status);
  const StatusIcon = statusConfig.icon;

  return (
    <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5 hover:shadow-lg hover:border-purple-primary/30 transition-all group">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="w-12 h-12 rounded-xl bg-purple-dim flex items-center justify-center flex-shrink-0 group-hover:bg-purple-primary/20 transition-colors">
          <Database className="w-6 h-6 text-purple-primary" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-syne text-base font-bold text-black-text mb-1 truncate">
                {dataset.name}
              </h3>
              <p className="text-xs text-gray-muted mb-2">{dataset.description}</p>
              <div className="flex items-center gap-4 text-xs text-gray-muted">
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {dataset.originalFilename}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {dataset.uploadedAt}
                </span>
                <span className="flex items-center gap-1">
                  <HardDrive className="w-3.5 h-3.5" />
                  {dataset.fileSize}
                </span>
              </div>
            </div>

            {/* Status Badge */}
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${statusConfig.bg} ${statusConfig.color} flex-shrink-0 ml-3`}>
              <StatusIcon className="w-3.5 h-3.5" />
              <span className="text-xs font-medium">{statusConfig.label}</span>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-4 gap-3 mt-4 pt-4 border-t border-white/40">
            <div>
              <div className="text-xs text-gray-muted mb-1">Records</div>
              <div className="font-syne text-lg font-bold text-black-text">
                {dataset.rowCount.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-muted mb-1">Columns</div>
              <div className="font-syne text-lg font-bold text-black-text">
                {dataset.columnCount}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-muted mb-1">Quality Score</div>
              <div className="font-syne text-lg font-bold text-purple-primary">
                {dataset.qualityScore}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-muted mb-1">EDA Report</div>
              <div className="flex items-center gap-1">
                {dataset.hasReport ? (
                  <>
                    <Sparkles className="w-4 h-4 text-green" />
                    <span className="text-xs font-medium text-green">Available</span>
                  </>
                ) : (
                  <span className="text-xs text-gray-muted">Not generated</span>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 mt-4">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-dim hover:bg-purple-primary/20 border border-purple-primary/20 hover:border-purple-primary/40 text-purple-primary text-xs font-medium transition-all">
              <Eye className="w-3.5 h-3.5" />
              View Preview
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-primary hover:bg-purple-primary/90 text-white text-xs font-medium transition-colors">
              <BarChart3 className="w-3.5 h-3.5" />
              Generate Report
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/40 hover:border-gray-border hover:bg-white/60 text-gray-muted hover:text-black-text text-xs font-medium transition-all">
              <Download className="w-3.5 h-3.5" />
              Export
            </button>
            <button className="ml-auto p-1.5 rounded-lg hover:bg-red-dim text-gray-muted hover:text-red transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
