/**
 * ML Preparation Queue Page
 * ================================================
 * Shows all datasets ready for ML training
 * Replaces the redundant "Validation" tab
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload, Search, Filter, Eye, Edit3, Trash2, Play, Database,
  CheckCircle, Loader2, RefreshCw, BarChart3, ChevronRight,
  Clock, FolderOpen, List, Grid3x3, SortAsc
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { flexibleAPI } from '../services/api';
import { authAPI } from '../services/api';

export default function MLPreparationQueuePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  // Load user data
  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await authAPI.getCurrentUser();
        console.log('[ML Queue] Current user:', userData);
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
      }
    };
    loadUser();
  }, []);
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewMode, setViewMode] = useState('table');
  
  useEffect(() => {
    fetchDatasets();
  }, []);
  
  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const response = await flexibleAPI.getRecentUploads(100, true, true);
      console.log('[ML Queue] Datasets loaded:', response.uploads?.length, 'datasets');
      console.log('[ML Queue] Sample dataset:', response.uploads?.[0]);
      setDatasets(response.uploads || []);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  };
  
  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.file_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         dataset.uploaded_by?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || dataset.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  
  const stats = {
    total: datasets.length,
    ready: datasets.filter(d => d.status === 'saved' || d.ml_prep_status === 'ready').length,
    preview: datasets.filter(d => d.status === 'preview').length,
    totalRecords: datasets.reduce((sum, d) => sum + (d.row_count || 0), 0)
  };
  
  const handleDelete = async (datasetId) => {
    if (!window.confirm('Delete this dataset? This cannot be undone.')) return;
    try {
      setDatasets(prev => prev.filter(d => d.id !== datasetId));
      await flexibleAPI.deleteUploadSession(datasetId);
    } catch (error) {
      console.error('Failed to delete:', error);
      await fetchDatasets();
    }
  };
  
  const handleMLPrep = (dataset) => {
    // Navigate directly to workflow mode with dataset pre-selected
    navigate('/ml-prep-workflow', { 
      state: { 
        fromDataCatalog: true,  // Triggers workflow mode (skips queue view)
        startTab: 'labeling',   // Start at labeling tab
        preselectedBatch: {
          id: dataset.id,
          name: dataset.file_name || 'Unnamed Dataset',
          uploadedAt: dataset.uploaded_at,
          totalRecords: dataset.row_count || 0,
          labeledRecords: dataset.labeled_count || 0,
          features: dataset.column_count || 0,
          status: dataset.status,
          owner: dataset.uploaded_by || 'Unknown'
        }
      } 
    });
  };
  
  const handleTrain = (datasetId) => navigate('/training', { state: { datasetId } });
  
  const handleView = (datasetId, status) => {
    // Find the dataset to pass full info
    const dataset = datasets.find(d => d.id === datasetId);
    
    // Navigate to data-preparation page with proper state
    navigate('/data-preparation', { 
      state: { 
        fromDataCatalog: true,
        preselectedBatch: {
          id: dataset?.id || datasetId,
          name: dataset?.file_name || 'Dataset',
          uploadedAt: dataset?.uploaded_at || new Date().toISOString(),
          totalRecords: dataset?.row_count || 0,
          labeledRecords: 0,
          features: dataset?.column_count || 0,
          status: dataset?.status || 'unknown',
          owner: dataset?.uploaded_by || 'Unknown'
        }
      } 
    });
  };
  
  const getStatusBadge = (dataset) => {
    if (dataset.status === 'preview') 
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">Preview</span>;
    if (dataset.status === 'saved' || dataset.ml_prep_status === 'ready')
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">Ready</span>;
    return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700">Unknown</span>;
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
  };

  return (
    <DashboardLayout>
      <PageHeader title="ML Preparation Queue" subtitle="ML Queue" user={user} />
      
      {/* CONTENT */}
      <main className="flex-1 overflow-y-auto p-6 transition-colors relative" style={{ zoom: 0.78, background: '#FAFBFC' }}>
        {/* Ambient glow orbs */}
        <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden" style={{ zIndex: 0 }}>
          <div style={{
            position: 'absolute', top: '-120px', right: '-100px', width: '520px', height: '520px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%, rgba(139,92,246,0.03) 45%, transparent 70%)', filter: 'blur(40px)'
          }} />
          <div style={{
            position: 'absolute', bottom: '80px', left: '-80px', width: '420px', height: '420px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.055) 0%, rgba(99,102,241,0.02) 50%, transparent 70%)', filter: 'blur(50px)'
          }} />
        </div>
        
        <div className="relative" style={{ zIndex: 1 }}>
          {/* Statistics Cards */}
          <motion.div className="grid grid-cols-4 gap-5 mb-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <div className="bg-white rounded-2xl p-6 border border-gray-200/60 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-md">
                  <Database className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
                  <div className="text-xs text-green-600 font-medium mt-1">↑ 3 product</div>
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-700">Total Uploads</div>
              <div className="text-xs text-gray-500 mt-0.5">vs last month</div>
            </div>
            
            <div className="bg-white rounded-2xl p-6 border border-gray-200/60 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-md">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-gray-900">{stats.ready}</div>
                  <div className="text-xs text-green-600 font-medium mt-1">↑ 7%</div>
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-700">Ready for ML</div>
              <div className="text-xs text-gray-500 mt-0.5">vs last month</div>
            </div>
            
            <div className="bg-white rounded-2xl p-6 border border-gray-200/60 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-md">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-gray-900">{stats.preview}</div>
                  <div className="text-xs text-green-600 font-medium mt-1">↑ 5%</div>
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-700">In Processing</div>
              <div className="text-xs text-gray-500 mt-0.5">vs last month</div>
            </div>
            
            <div className="bg-white rounded-2xl p-6 border border-gray-200/60 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-md">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-gray-900">{(stats.totalRecords / 1000).toFixed(1)}K</div>
                  <div className="text-xs text-green-600 font-medium mt-1">↑ 12%</div>
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-700">Total Records</div>
              <div className="text-xs text-gray-500 mt-0.5">vs last month</div>
            </div>
          </motion.div>
          
          {/* Controls Bar */}
          <motion.div className="bg-white rounded-2xl p-5 border border-gray-200/60 shadow-sm mb-5" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }}>
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 flex-1">
                {/* View Mode Toggle */}
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                  <button onClick={() => setViewMode('table')} className={`px-3 py-1.5 rounded-md transition-colors ${viewMode === 'table' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>
                    <List size={16} />
                  </button>
                  <button onClick={() => setViewMode('grid')} className={`px-3 py-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>
                    <Grid3x3 size={16} />
                  </button>
                </div>
                
                {/* Search */}
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input
                    type="text"
                    placeholder="Search datasets by name, type, or owner..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {/* Status Filter */}
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                  <button onClick={() => setStatusFilter('all')} className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors whitespace-nowrap ${statusFilter === 'all' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-600'}`}>
                    All ({stats.total})
                  </button>
                  <button onClick={() => setStatusFilter('saved')} className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors whitespace-nowrap ${statusFilter === 'saved' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-600'}`}>
                    Ready ({stats.ready})
                  </button>
                  <button onClick={() => setStatusFilter('preview')} className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors whitespace-nowrap ${statusFilter === 'preview' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-600'}`}>
                    Processing ({stats.preview})
                  </button>
                </div>
                
                <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" title="Sort">
                  <SortAsc size={18} />
                </button>
                
                <button onClick={fetchDatasets} disabled={loading} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50" title="Refresh">
                  <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                </button>
              </div>
            </div>
          </motion.div>
          
          {/* Table */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.2 }}>
            {loading ? (
              <div className="flex items-center justify-center h-96 bg-white rounded-2xl shadow-sm border border-gray-200/60">
                <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
              </div>
            ) : filteredDatasets.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-96 bg-white rounded-2xl shadow-sm border border-gray-200/60 text-gray-500">
                <FolderOpen className="w-20 h-20 mb-4 text-gray-300" />
                <p className="text-lg font-semibold">No datasets found</p>
                <p className="text-sm mt-1 mb-4">Upload data to get started</p>
                <button onClick={() => navigate('/data-preparation')} className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium">
                  Upload New Data
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200/60 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Dataset Name</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Records</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Owner</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Uploaded</th>
                      <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3.5 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredDatasets.map((dataset, idx) => (
                      <motion.tr key={dataset.id} className="hover:bg-gray-50 transition-colors" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2, delay: idx * 0.03 }}>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
                              <Database className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <div className="font-semibold text-gray-900 text-sm max-w-md truncate">{dataset.file_name || 'Unnamed Dataset'}</div>
                              <div className="text-xs text-gray-500 mt-0.5">{dataset.dataset_type || 'General'}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                            {dataset.file_type || 'CSV/Excel'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm font-semibold text-gray-900">{(dataset.row_count || 0).toLocaleString()}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                              {(dataset.uploaded_by || 'U')[0].toUpperCase()}
                            </div>
                            <span>{dataset.uploaded_by || 'Unknown'}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">{formatDate(dataset.uploaded_at)}</td>
                        <td className="px-6 py-4">{getStatusBadge(dataset)}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => handleView(dataset.id, dataset.status)} className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors" title="View Details">
                              <Eye size={16} />
                            </button>
                            
                            {/* ML Prep Button - only for own datasets */}
                            {(user && dataset && (String(user.id) === String(dataset.user_id) || String(user.id) === String(dataset.uploaded_by_id) || user.username === dataset.uploaded_by)) && (
                              <button onClick={() => handleMLPrep(dataset)} className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Start ML Preparation">
                                <Play size={16} className="fill-blue-600" />
                              </button>
                            )}
                            
                            {/* Train Button - only for ready datasets + own datasets */}
                            {(dataset.status === 'saved' || dataset.ml_prep_status === 'ready') && (user && dataset && (String(user.id) === String(dataset.user_id) || String(user.id) === String(dataset.uploaded_by_id) || user.username === dataset.uploaded_by)) && (
                              <button onClick={() => handleTrain(dataset.id)} className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors" title="Start ML Training">
                                <Play size={16} />
                              </button>
                            )}
                            
                            {/* Delete Button - only for own datasets */}
                            {(user && dataset && (String(user.id) === String(dataset.user_id) || String(user.id) === String(dataset.uploaded_by_id) || user.username === dataset.uploaded_by)) && (
                              <button onClick={() => handleDelete(dataset.id)} className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete Dataset">
                                <Trash2 size={16} />
                              </button>
                            )}
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>
        </div>
      </main>
    </DashboardLayout>
  );
}
