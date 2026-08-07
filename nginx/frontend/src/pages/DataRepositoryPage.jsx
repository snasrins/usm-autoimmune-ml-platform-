import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HardDrive,
  Folder,
  File,
  FileText,
  Database,
  Search,
  Filter,
  Upload,
  Download,
  Trash2,
  Share2,
  Lock,
  Unlock,
  Calendar,
  User,
  Tag,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Eye,
  Copy,
  MoreVertical
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function DataRepositoryPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [filterType, setFilterType] = useState('all');
  const [selectedItems, setSelectedItems] = useState([]);

  // Mock repository data
  const repositories = [
    {
      id: 'repo-001',
      name: 'SLE Clinical Dataset v2.1',
      type: 'dataset',
      size: '2.4 GB',
      files: 1204,
      lastModified: '2024-04-08 14:23',
      owner: 'Dr. Sarah Chen',
      description: 'Systemic Lupus Erythematosus patient data with 47 biomarkers',
      tags: ['sle', 'lupus', 'autoimmune', 'validated'],
      access: 'restricted',
      downloads: 847,
      usage: 'training',
      format: 'CSV',
      version: '2.1',
      status: 'active'
    },
    {
      id: 'repo-002',
      name: 'Rheumatoid Arthritis Cohort',
      type: 'dataset',
      size: '1.8 GB',
      files: 856,
      lastModified: '2024-04-07 11:15',
      owner: 'Dr. Michael Torres',
      description: 'RA patient biomarker data with longitudinal follow-up',
      tags: ['ra', 'rheumatoid', 'arthritis'],
      access: 'public',
      downloads: 523,
      usage: 'training',
      format: 'CSV',
      version: '1.8',
      status: 'active'
    },
    {
      id: 'repo-003',
      name: 'Ensemble Model Weights - Production',
      type: 'model',
      size: '847 MB',
      files: 5,
      lastModified: '2024-04-08 16:40',
      owner: 'Dr. Sarah Chen',
      description: 'Trained ensemble model (RF + XGBoost + LightGBM) - 91.8% accuracy',
      tags: ['ensemble', 'production', 'validated'],
      access: 'restricted',
      downloads: 142,
      usage: 'inference',
      format: 'PKL',
      version: '3.2',
      status: 'production'
    },
    {
      id: 'repo-004',
      name: 'Feature Engineering Scripts',
      type: 'code',
      size: '12 MB',
      files: 34,
      lastModified: '2024-04-06 09:30',
      owner: 'Dr. Emily Watson',
      description: 'Python scripts for biomarker feature extraction and transformation',
      tags: ['preprocessing', 'features', 'python'],
      access: 'public',
      downloads: 289,
      usage: 'development',
      format: 'PY',
      version: '1.0',
      status: 'active'
    },
    {
      id: 'repo-005',
      name: 'Sjögren Syndrome Data v2.3',
      type: 'dataset',
      size: '980 MB',
      files: 642,
      lastModified: '2024-04-05 14:20',
      owner: 'Dr. David Kim',
      description: 'Sjögren syndrome patient cohort with autoantibody profiles',
      tags: ['sjogren', 'autoimmune', 'rare-disease'],
      access: 'restricted',
      downloads: 156,
      usage: 'training',
      format: 'CSV',
      version: '2.3',
      status: 'active'
    },
    {
      id: 'repo-006',
      name: 'Training Pipeline Logs - Q1 2024',
      type: 'logs',
      size: '3.2 GB',
      files: 847,
      lastModified: '2024-03-31 23:59',
      owner: 'System',
      description: 'Comprehensive training logs and experiment tracking data',
      tags: ['logs', 'experiments', 'monitoring'],
      access: 'public',
      downloads: 67,
      usage: 'analysis',
      format: 'JSON',
      version: '1.0',
      status: 'archived'
    },
    {
      id: 'repo-007',
      name: 'Multi-Disease Classification Models',
      type: 'model',
      size: '1.4 GB',
      files: 12,
      lastModified: '2024-04-03 10:15',
      owner: 'Dr. Jennifer Lopez',
      description: 'Collection of trained models for multiple autoimmune diseases',
      tags: ['multi-class', 'models', 'research'],
      access: 'restricted',
      downloads: 234,
      usage: 'research',
      format: 'H5',
      version: '2.0',
      status: 'active'
    },
    {
      id: 'repo-008',
      name: 'Data Quality Reports - April 2024',
      type: 'reports',
      size: '45 MB',
      files: 28,
      lastModified: '2024-04-08 08:00',
      owner: 'System',
      description: 'Automated data quality validation reports and metrics',
      tags: ['quality', 'validation', 'reports'],
      access: 'public',
      downloads: 92,
      usage: 'monitoring',
      format: 'PDF',
      version: '1.0',
      status: 'active'
    }
  ];

  const filteredRepositories = repositories.filter(repo => {
    const matchesSearch = repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         repo.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         repo.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = filterType === 'all' || repo.type === filterType;
    return matchesSearch && matchesType;
  });

  const typeIcons = {
    dataset: Database,
    model: BarChart3,
    code: FileText,
    logs: File,
    reports: FileText
  };

  const typeColors = {
    dataset: { bg: 'bg-purple-dim', text: 'text-purple-primary', icon: 'text-purple-primary' },
    model: { bg: 'bg-green-dim', text: 'text-green', icon: 'text-green' },
    code: { bg: 'bg-blue-50', text: 'text-blue-600', icon: 'text-blue-600' },
    logs: { bg: 'bg-amber-dim', text: 'text-amber', icon: 'text-amber' },
    reports: { bg: 'bg-gray-100', text: 'text-gray-muted', icon: 'text-gray-muted' }
  };

  const accessIcons = {
    public: Unlock,
    restricted: Lock
  };

  const accessColors = {
    public: { bg: 'bg-green-dim', text: 'text-green' },
    restricted: { bg: 'bg-amber-dim', text: 'text-amber' }
  };

  const statusColors = {
    active: { bg: 'bg-green-dim', text: 'text-green', border: 'border-green/20' },
    production: { bg: 'bg-purple-dim', text: 'text-purple-primary', border: 'border-purple-primary/20' },
    archived: { bg: 'bg-gray-100', text: 'text-gray-muted', border: 'border-gray-300' }
  };

  const stats = {
    totalSize: repositories.reduce((sum, r) => sum + parseFloat(r.size), 0).toFixed(1),
    totalFiles: repositories.reduce((sum, r) => sum + r.files, 0),
    datasets: repositories.filter(r => r.type === 'dataset').length,
    models: repositories.filter(r => r.type === 'model').length,
    totalDownloads: repositories.reduce((sum, r) => sum + r.downloads, 0)
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <HardDrive className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-syne text-2xl font-bold text-black-text">Data Repository</h1>
                  <p className="text-xs text-gray-muted">Centralized storage for datasets, models, and artifacts</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/40 bg-white/80 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <Download className="w-4 h-4" />
                  Bulk Download
                </button>
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all text-sm font-medium">
                  <Upload className="w-4 h-4" />
                  Upload Files
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-5 gap-4">
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Total Storage</span>
                  <HardDrive className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">{stats.totalSize} GB</div>
                <div className="text-xs text-gray-muted mt-1">{stats.totalFiles.toLocaleString()} files</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Datasets</span>
                  <Database className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-purple-primary">{stats.datasets}</div>
                <div className="text-xs text-gray-muted mt-1">Active repositories</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Models</span>
                  <BarChart3 className="w-4 h-4 text-green" />
                </div>
                <div className="font-syne text-2xl font-bold text-green">{stats.models}</div>
                <div className="text-xs text-gray-muted mt-1">Trained models</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Downloads</span>
                  <Download className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">{stats.totalDownloads}</div>
                <div className="text-xs text-gray-muted mt-1">Total this month</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Access</span>
                  <Lock className="w-4 h-4 text-amber" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">
                  {repositories.filter(r => r.access === 'restricted').length}
                </div>
                <div className="text-xs text-gray-muted mt-1">Restricted access</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Search & Filters */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name, description, or tags..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
                  />
                </div>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary"
                >
                  <option value="all">All Types</option>
                  <option value="dataset">Datasets</option>
                  <option value="model">Models</option>
                  <option value="code">Code</option>
                  <option value="logs">Logs</option>
                  <option value="reports">Reports</option>
                </select>
                <div className="flex items-center gap-2 border border-white/40 rounded-lg p-1 bg-white/90">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-purple-dim text-purple-primary' : 'text-gray-muted'}`}
                  >
                    <BarChart3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-purple-dim text-purple-primary' : 'text-gray-muted'}`}
                  >
                    <FileText className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Repository Grid */}
            <div className="grid grid-cols-2 gap-4">
              {filteredRepositories.map((repo) => {
                const TypeIcon = typeIcons[repo.type];
                const typeStyle = typeColors[repo.type];
                const AccessIcon = accessIcons[repo.access];
                const accessStyle = accessColors[repo.access];
                const statusStyle = statusColors[repo.status];

                return (
                  <div key={repo.id} className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5 hover:shadow-lg transition-all">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={`w-12 h-12 rounded-lg ${typeStyle.bg} flex items-center justify-center flex-shrink-0`}>
                          <TypeIcon className={`w-6 h-6 ${typeStyle.icon}`} />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-sm text-black-text mb-1">{repo.name}</h3>
                          <p className="text-xs text-gray-muted line-clamp-2">{repo.description}</p>
                        </div>
                      </div>
                      <button className="text-gray-muted hover:text-black-text">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Metadata */}
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      <div className="bg-purple-dim/20 rounded-lg p-2">
                        <div className="text-[10px] text-gray-muted uppercase mb-0.5">Size</div>
                        <div className="font-bold text-xs text-black-text">{repo.size}</div>
                      </div>
                      <div className="bg-purple-dim/20 rounded-lg p-2">
                        <div className="text-[10px] text-gray-muted uppercase mb-0.5">Files</div>
                        <div className="font-bold text-xs text-black-text">{repo.files}</div>
                      </div>
                      <div className="bg-purple-dim/20 rounded-lg p-2">
                        <div className="text-[10px] text-gray-muted uppercase mb-0.5">Version</div>
                        <div className="font-bold text-xs text-black-text">v{repo.version}</div>
                      </div>
                      <div className="bg-purple-dim/20 rounded-lg p-2">
                        <div className="text-[10px] text-gray-muted uppercase mb-0.5">Downloads</div>
                        <div className="font-bold text-xs text-black-text">{repo.downloads}</div>
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex items-center gap-2 flex-wrap mb-3">
                      {repo.tags.slice(0, 3).map((tag, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-purple-dim/30 text-purple-primary text-[10px] font-medium">
                          #{tag}
                        </span>
                      ))}
                      {repo.tags.length > 3 && (
                        <span className="text-[10px] text-gray-muted">+{repo.tags.length - 3}</span>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-3 border-t border-white/40">
                      <div className="flex items-center gap-2">
                        <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${accessStyle.bg} ${accessStyle.text}`}>
                          <AccessIcon className="w-3 h-3" />
                          {repo.access}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                          {repo.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button className="p-1.5 rounded hover:bg-purple-dim text-purple-primary transition-colors">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-purple-dim text-purple-primary transition-colors">
                          <Download className="w-3.5 h-3.5" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-purple-dim text-purple-primary transition-colors">
                          <Share2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Owner & Date */}
                    <div className="flex items-center gap-3 mt-3 pt-3 border-t border-white/40 text-xs text-gray-muted">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {repo.owner}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {repo.lastModified}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
