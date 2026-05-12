/**
 * Enhanced Data Preparation Page
 * ============================
 * Unified workflow for both structured (CSV/Excel) and unstructured (PDF/IMG/TXT) data
 * 
 * Flow: Upload â†’ Process/OCR â†’ Preview â†’ Edit â†’ Save
 * - Uses new flexible API (/api/v1/flexible/*)
 * - 100% flexible schema (no hardcoded fields)
 * - Real-time editing with cell-level changes
 * - OCR progress tracking with page count
 * - Entity extraction preview
 * 
 * Author: Syarifah Fajriyah
 * Date: April 7, 2026
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { flexibleAPI } from '../services/api';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Eye,
  Save,
  RotateCcw,
  Loader2,
  FileSpreadsheet,
  Image as ImageIcon,
  FileIcon,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  Clock,
  FileCheck,
  Zap,
  Settings,
  Bell,
  Search,
  Lock,
  Shield,
  BarChart3,
  Filter,
  ArrowDownUp
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import PageHeader from '../components/PageHeader';
import { authAPI } from '../services/api';

export default function DataPipelinePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  const [user, setUser] = useState(null);
  
  // Load user data
  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
      }
    };
    loadUser();
  }, []);
  
  // Get current user from localStorage
  const [currentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
      return {};
    }
  });
  
  // Recent uploads state
  const [recentUploads, setRecentUploads] = useState([]);
  const [uploadsLoading, setUploadsLoading] = useState(false);
  
  // Search and filter state (upload page only)
  const [uploadSearchQuery, setUploadSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest'); // 'newest' or 'oldest'
  const [fileTypeFilter, setFileTypeFilter] = useState('all');
  
  // ========== STATE MANAGEMENT ==========
  const [stage, setStage] = useState('upload'); // upload â†’ processing â†’ preview â†’ saving
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileType, setFileType] = useState(null); // 'structured' or 'unstructured'
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // OCR-specific state
  const [ocrResult, setOcrResult] = useState(null); // {validation_id, extracted_text, page_count, etc}
  const [ocrProgress, setOcrProgress] = useState({ current: 0, total: 0, status: '' });
  const [processingLogs, setProcessingLogs] = useState([]); // NEW: Real-time logs
  
  // Preview state
const [sessionId, setSessionId] = useState(null);
  const [previewData, setPreviewData] = useState(null); // {rows, columns, total_rows}
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [editingCell, setEditingCell] = useState(null); // {rowIndex, columnName, value}
  
  // Dataset config
  const [datasetConfig, setDatasetConfig] = useState({
    datasetType: 'General',
    datasetName: '',
    conversionMode: 'grouped' // for unstructured: 'grouped' or 'individual'
  });
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // ========== DELETE UPLOAD ==========
  const handleDeleteUpload = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this upload? This action cannot be undone.')) {
      return;
    }
    
    try {
      // Optimistically remove from UI immediately
      setRecentUploads(prev => prev.filter(upload => upload.id !== sessionId));
      
      // Call API to delete the upload session from database
      await flexibleAPI.deleteUploadSession(sessionId);
      
      console.log(`✓ Upload session ${sessionId} deleted successfully`);
    } catch (error) {
      console.error('Failed to delete upload:', error);
      // Refresh to restore if delete failed
      await fetchRecentUploads();
      setError(`Failed to delete upload: ${error.message}`);
    }
  };

  // ========== FETCH RECENT UPLOADS ==========
  const fetchRecentUploads = async () => {
    setUploadsLoading(true);
    try {
      console.log('[Data Pipeline] Fetching recent uploads...');
      // Include BOTH staging and saved datasets (staging = just uploaded, saved = after save button)
      const response = await flexibleAPI.getRecentUploads(10, true, true);
      console.log('[Data Pipeline] API Response:', response);
      console.log('[Data Pipeline] Uploads array:', response.uploads);
      console.log('[Data Pipeline] Upload count:', response.uploads?.length || 0);
      setRecentUploads(response.uploads || []);
    } catch (error) {
      console.error('[Data Pipeline] Failed to fetch recent uploads:', error);
      console.error('[Data Pipeline] Error details:', error.response?.data);
      setRecentUploads([]);
    } finally {
      setUploadsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecentUploads();
    
    // Handle navigation from Data Catalog or quality report with sessionId
    if (location.state?.sessionId && !sessionId) {
      const incomingSessionId = location.state.sessionId;
      const incomingStage = location.state.stage || 'preview';
      const datasetName = location.state.datasetName || '';
      
      console.log('[Data Pipeline] Loading from navigation:', {
        sessionId: incomingSessionId,
        stage: incomingStage,
        datasetName,
        fromDataCatalog: location.state.fromDataCatalog
      });
      
      setSessionId(incomingSessionId);
      setStage(incomingStage);
      
      if (datasetName) {
        setDatasetConfig(prev => ({ ...prev, datasetName }));
      }
      
      if (incomingStage === 'preview') {
        loadPreview(incomingSessionId, 1);
      }
    }
  }, []); // Fetch on mount

  // ========== FILE UPLOAD HANDLERS ==========
  
  const addLog = (message, type = 'info', icon = 'Info') => {
    const timestamp = new Date().toLocaleTimeString();
    setProcessingLogs(prev => [...prev, { timestamp, message, type, icon }]);
  };

  const getIconComponent = (iconName) => {
    const iconMap = {
      'Zap': Zap,
      'Upload': Upload,
      'Loader': Loader2,
      'FileText': FileText,
      'Clock': Clock,
      'Table': FileSpreadsheet,
      'Hash': FileIcon,
      'Tag': FileCheck,
      'User': Eye,
      'Building': FileIcon,
      'Calendar': Clock,
      'RefreshCw': RotateCcw,
      'CheckCircle': CheckCircle,
      'Eye': Eye,
      'Info': AlertCircle
    };
    const IconComponent = iconMap[iconName] || AlertCircle;
    return <IconComponent className="w-3 h-3" />;
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) processFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const processFile = async (file) => {
    setUploadedFile(file);
    setError(null);
    setIsProcessing(true);
    setStage('processing');
    setProcessingLogs([]); // Clear previous logs
    
    const ext = file.name.split('.').pop().toLowerCase();
    const isUnstructured = ['pdf', 'txt', 'png', 'jpg', 'jpeg'].includes(ext);
    const isStructured = ['csv', 'xlsx', 'xls'].includes(ext);
    
    if (!isUnstructured && !isStructured) {
      setError('Unsupported file type. Please upload CSV, Excel, PDF, TXT, or images.');
      setIsProcessing(false);
      setStage('upload');
      return;
    }
    
    setFileType(isUnstructured ? 'unstructured' : 'structured');
    
    addLog(` File uploaded: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
    
    try {
      if (isUnstructured) {
        await processUnstructuredFile(file);
      } else {
        await processStructuredFile(file);
      }
    } catch (err) {
      console.error('Processing error:', err);
      addLog(`Error: ${err.message}`, 'error', 'AlertCircle');
      setError(err.response?.data?.detail || err.message || 'Processing failed');
      setIsProcessing(false);
      setStage('upload');
    }
  };

  // ========== STRUCTURED DATA WORKFLOW ==========
  
  const processStructuredFile = async (file) => {
    addLog('Analyzing CSV/Excel structure...', 'info', 'FileSpreadsheet');
    setOcrProgress({ current: 1, total: 1, status: 'Analyzing structure...' });
    
    // Step 1: Upload for preview
    addLog('Uploading to server...', 'info', 'Upload');
    console.log('[Data Pipeline] Uploading structured file:', file.name);
    const uploadResult = await flexibleAPI.uploadStructured(file, datasetConfig.datasetType);
    console.log('[Data Pipeline] Upload result:', uploadResult);
    
    addLog(`Detected ${uploadResult.row_count} rows, ${uploadResult.columns?.length || 0} columns`, 'success', 'CheckCircle');
    setSessionId(uploadResult.session_id);
    setOcrProgress({ current: 1, total: 1, status: `Detected ${uploadResult.row_count} rows` });
    
    // Step 2: Fetch preview
    addLog('Loading preview...', 'info', 'Eye');
    await loadPreview(uploadResult.session_id, 1);
    
    addLog('Preview ready for editing', 'success', 'CheckCircle');
    setIsProcessing(false);
    setStage('preview');
    
    // Refresh recent uploads list
    console.log('[Data Pipeline] Refreshing recent uploads after upload...');
    await fetchRecentUploads();
  };

  // ========== UNSTRUCTURED DATA WORKFLOW ==========
  
  const processUnstructuredFile = async (file) => {
    // Step 1: Upload for OCR with simulated progress
    addLog('Starting OCR pipeline...', 'info', 'Zap');
    addLog('Uploading to GPU server...', 'info', 'Upload');
    setOcrProgress({ current: 0, total: 1, status: 'Uploading...' });
    
    // Start simulated progress updates (backend doesn't stream real-time yet)
    let progressInterval;
    let simulatedProgress = 0;
    
    // Estimate: ~20s per page (optimized), show progress every 3 seconds
    const estimatedPagesPerFile = file.name.toLowerCase().endsWith('.pdf') ? 6 : 1;
    const totalEstimatedTime = estimatedPagesPerFile * 20; // 20s per page target
    const updateInterval = 3; // Update every 3 seconds
    const totalUpdates = Math.floor(totalEstimatedTime / updateInterval);
    
    progressInterval = setInterval(() => {
      simulatedProgress += 1;
      const currentPage = Math.ceil((simulatedProgress / totalUpdates) * estimatedPagesPerFile);
      
      if (simulatedProgress < totalUpdates) {
        setOcrProgress({ 
          current: currentPage, 
          total: estimatedPagesPerFile, 
          status: `Processing page ${currentPage}/${estimatedPagesPerFile}...` 
        });
        
        // Add log every few updates
        if (simulatedProgress % 3 === 0) {
          addLog(`OCR in progress... (page ${currentPage}/${estimatedPagesPerFile})`, 'info', 'Loader');
        }
      }
    }, updateInterval * 1000);
    
    const ocrResult = await flexibleAPI.uploadUnstructured(file);
    
    // Stop simulated progress
    clearInterval(progressInterval);
    
    setOcrResult(ocrResult);
    
    const pageCount = ocrResult.page_count || 1;
    const entityCount = ocrResult.medical_entities?.length || 0;
    const structuredTestCount = ocrResult.structured_tests?.length || 0;
    const processingTime = ocrResult.processing_time || 0;
    const timePerPage = pageCount > 0 ? (processingTime / pageCount) : 0;
    
    addLog(`PDF converted to ${pageCount} page(s)`, 'info', 'FileText');
    addLog(`OCR completed: ${processingTime.toFixed(1)}s total (${timePerPage.toFixed(1)}s/page)`, 'success', 'Clock');
    
    if (structuredTestCount > 0) {
      addLog(`Extracted ${structuredTestCount} structured test rows (table preserved!)`, 'success', 'Table');
    } else {
      addLog(`Extracted ${entityCount} medical entities`, 'info', 'Hash');
    }
    
    if (ocrResult.metadata) {
      const meta = ocrResult.metadata;
      if (meta.lab_no) addLog(`Lab No: ${meta.lab_no}`, 'info', 'Tag');
      if (meta.mrn) addLog(`MRN: ${meta.mrn}`, 'info', 'User');
      if (meta.facility) addLog(`Facility: ${meta.facility}`, 'info', 'Building');
      if (meta.collected_date) addLog(`Collected: ${meta.collected_date}`, 'info', 'Calendar');
    }
    
    setOcrProgress({ 
      current: pageCount, 
      total: pageCount, 
      status: ocrResult.status === 'success' ? `OCR completed (${structuredTestCount || entityCount} items)` : 'OCR failed' 
    });
    
    if (ocrResult.status !== 'success') {
      throw new Error(ocrResult.error || 'OCR processing failed');
    }
    
    // Step 2: Convert to tabular
    addLog('Converting OCR result to tabular format...', 'info', 'RefreshCw');
    setOcrProgress({ current: pageCount, total: pageCount + 1, status: 'Converting to tabular...' });
    
    const convertResult = await flexibleAPI.convertUnstructuredToTabular(
      ocrResult.validation_id,
      datasetConfig.datasetType,
      datasetConfig.conversionMode
    );
    
    addLog(`Converted to ${convertResult.row_count} tabular row(s)`, 'success', 'CheckCircle');
    
    setSessionId(convertResult.session_id);
    setOcrProgress({ current: pageCount + 1, total: pageCount + 1, status: `Converted to ${convertResult.row_count} rows` });
    
    // Step 3: Fetch preview
    addLog('Loading preview for editing...', 'info', 'Eye');
    await loadPreview(convertResult.session_id, 1);
    
    addLog('Ready for review and save!', 'success', 'CheckCircle');
    setIsProcessing(false);
    setStage('preview');
    
    // Refresh recent uploads list
    fetchRecentUploads();
  };

  // ========== PREVIEW MANAGEMENT ==========
  
  const loadPreview = async (sessionId, page = 1) => {
    try {
      const preview = await flexibleAPI.getPreview(sessionId, page, pageSize);
      console.log('Preview data received:', preview); // Debug log
      
      // Validate preview data structure
      if (!preview || !preview.rows || !Array.isArray(preview.rows)) {
        console.error('Invalid preview data structure:', preview);
        setError('Failed to load preview: Invalid data structure');
        return;
      }
      
      if (preview.rows.length === 0) {
        console.warn('Preview has no rows');
        setError('No data to display. The uploaded file may be empty.');
        return;
      }
      
      setPreviewData(preview);
      setCurrentPage(page);
    } catch (err) {
      console.error('Failed to load preview:', err);
      setError(err.response?.data?.detail || 'Failed to load preview');
      throw err;
    }
  };

  const handlePageChange = async (newPage) => {
    if (!sessionId) return;
    setIsProcessing(true);
    try {
      await loadPreview(sessionId, newPage);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // ========== TABLE EDITING ==========
  
  const handleCellEdit = (rowIndex, columnName, currentValue) => {
    setEditingCell({ rowIndex, columnName, value: currentValue });
  };

  const handleCellSave = async () => {
    if (!editingCell || !sessionId) return;
    
    const row = previewData.rows[editingCell.rowIndex];
    const stagingId = row.staging_id;
    
    try {
      await flexibleAPI.editCell(
        sessionId,
        stagingId,
        editingCell.columnName,
        editingCell.value
      );
      
      // Update local state
      const updatedRows = [...previewData.rows];
      updatedRows[editingCell.rowIndex].data[editingCell.columnName] = editingCell.value;
      updatedRows[editingCell.rowIndex].is_edited = true;
      setPreviewData({ ...previewData, rows: updatedRows });
      
      setEditingCell(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update cell');
    }
  };

  const handleRowDelete = async (rowIndex) => {
    if (!sessionId || !confirm('Delete this row?')) return;
    
    const row = previewData.rows[rowIndex];
    const stagingId = row.staging_id;
    
    try {
      await flexibleAPI.deleteRow(sessionId, stagingId);
      
      // Reload preview
      await loadPreview(sessionId, currentPage);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete row');
    }
  };

  // ========== SAVE TO DATABASE ==========
  
  const handleSaveDataset = async () => {
    if (!sessionId) return;
    
    setIsProcessing(true);
    setStage('saving');
    setError(null);
    
    try {
      const result = await flexibleAPI.saveToDatabase(
        sessionId,
        datasetConfig.datasetName || null
      );
      
      // Show success message
      const stats = result.statistics;
      alert(`âœ… Dataset saved successfully!\n\n` +
        `Batch ID: ${result.batch_id}\n` +
        `Records saved: ${stats.imported || stats.total_rows}\n` +
        `Duplicates skipped: ${stats.duplicates_skipped || 0}\n` +
        `Errors: ${stats.errors || 0}`
      );
      
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save dataset');
      setIsProcessing(false);
      setStage('preview');
    }
  };

  // ========== SAVE & CONTINUE TO ML PREP ==========
  
  const handleContinueToMLPrep = async () => {
    if (!sessionId) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Step 1: Save to database (permanent storage)
      const result = await flexibleAPI.saveToDatabase(
        sessionId,
        datasetConfig.datasetName || `ML Dataset ${new Date().toLocaleDateString()}`
      );
      
      const batchId = result.batch_id;
      const stats = result.statistics;
      
      // Step 2: Show success message (briefly)
      alert(`âœ… Dataset Saved Successfully!\n\n` +
        `Batch ID: ${batchId}\n` +
        `Records saved: ${stats.imported || stats.total_rows}\n` +
        `Duplicates skipped: ${stats.duplicates_skipped || 0}\n\n` +
        `Opening ML Preparation...`
      );
      
      // Step 3: Navigate to ML Prep with saved batch ID
      navigate('/ml-preparation', { 
        state: { 
          batchId: batchId,
          datasetName: datasetConfig.datasetName || result.batch_id,
          datasetType: datasetConfig.datasetType,
          rowCount: result.statistics?.imported || previewData?.total_rows,
          saved: true // Flag to indicate data is already saved
        }
      });
      
      // Refresh recent uploads
      fetchRecentUploads();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save dataset for ML prep');
      setIsProcessing(false);
    }
  };

  // ========== RESET ==========
  
  const handleReset = () => {
    setStage('upload');
    setUploadedFile(null);
    setFileType(null);
    setError(null);
    setOcrResult(null);
    setOcrProgress({ current: 0, total: 0, status: '' });
    setProcessingLogs([]); // Clear logs
    setSessionId(null);
    setPreviewData(null);
    setCurrentPage(1);
    setEditingCell(null);
    setDatasetConfig({
      datasetType: 'General',
      datasetName: '',
      conversionMode: 'grouped'
    });
  };

  // ========== RENDER HELPERS ==========
  
  const getFileIcon = () => {
    if (!uploadedFile) return <FileIcon className="w-12 h-12" />;
    
    const ext = uploadedFile.name.split('.').pop().toLowerCase();
    if (['csv', 'xlsx', 'xls'].includes(ext)) return <FileSpreadsheet className="w-12 h-12 text-[#7B5CF0]" />;
    if (['pdf'].includes(ext)) return <FileText className="w-12 h-12 text-[#7B5CF0]" />;
    if (['png', 'jpg', 'jpeg'].includes(ext)) return <ImageIcon className="w-12 h-12 text-[#7B5CF0]" />;
    return <FileIcon className="w-12 h-12 text-[#7B5CF0]" />;
  };

  const totalPages = previewData ? Math.ceil(previewData.total_rows / pageSize) : 0;

  // ========== RENDER ==========
  // ========== RENDER ==========
  
  return (
    <DashboardLayout>
      <PageHeader title="Data Preparation" user={user} />
      <style>{`
        @keyframes gradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .animate-gradient {
          animation: gradient 4s ease infinite;
        }
      `}</style>
      
      {/* ═══ CONTENT ═══ */}
      <main className="flex-1 overflow-y-auto transition-colors relative" style={{ background: '#FAFBFC', zoom: 0.78 }}>

        {/* Error Message */}
        {error && (
          <div className={`${stage === 'upload' ? 'px-8' : 'max-w-7xl mx-auto'} mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3`}>
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Error</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="ml-auto">
              <X className="w-5 h-5 text-red-400 hover:text-red-600" />
            </button>
          </div>
        )}

        {/* Search & Filter Bar (Upload stage only) */}
        {stage === 'upload' && (
          <div className="px-8 py-4 bg-white border-b border-gray-200">
            <div className="flex items-center gap-4">
              {/* Search Bar */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search documents..."
                  value={uploadSearchQuery}
                  onChange={(e) => setUploadSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              {/* Sort Filter */}
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-500" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  <option value="newest">Newest → Oldest</option>
                  <option value="oldest">Oldest → Newest</option>
                </select>
              </div>
              
              {/* File Type Filter */}
              <select
                value={fileTypeFilter}
                onChange={(e) => setFileTypeFilter(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
              >
                <option value="all">All File Types</option>
                <option value="CSV">CSV</option>
                <option value="Excel">Excel</option>
                <option value="PDF">PDF</option>
                <option value="Image">Image</option>
                <option value="JSON">JSON</option>
                <option value="XML">XML</option>
              </select>
            </div>
          </div>
        )}

        {/* Stage Indicator */}
        <div className={stage === 'upload' ? 'px-8 py-6' : 'max-w-7xl mx-auto mb-8'}>
          {stage === 'upload' ? (
            /* Modern Neutral Stepper (Upload stage only) */
            <div 
              className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
            >
              <div className="flex items-center justify-between">
                {['upload', 'processing', 'preview', 'saving'].map((s, idx) => (
                  <div key={s} className="flex items-center flex-1">
                    <div className="flex items-center gap-3">
                      <div className={`flex items-center justify-center w-11 h-11 rounded-xl transition-all ${ 
                        stage === s ? 'bg-[#1a0a2e] text-white' : 
                        ['processing', 'preview', 'saving'].indexOf(stage) > idx - 1 ? 'bg-gray-100 text-gray-700' : 
                        'bg-gray-50 text-gray-400'
                      }`}>
                        {s === 'upload' && <Upload className="w-5 h-5" />}
                        {s === 'processing' && <Zap className="w-5 h-5" />}
                        {s === 'preview' && <Eye className="w-5 h-5" />}
                        {s === 'saving' && <Save className="w-5 h-5" />}
                      </div>
                      <div>
                        <p className={`text-sm font-semibold ${
                          stage === s ? 'text-[#1a0a2e]' : 
                          ['processing', 'preview', 'saving'].indexOf(stage) > idx - 1 ? 'text-gray-700' : 
                          'text-gray-500'
                        }`}>
                          {s.charAt(0).toUpperCase() + s.slice(1)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {idx === 0 && 'Step 1'}
                          {idx === 1 && 'Step 2'}
                          {idx === 2 && 'Step 3'}
                          {idx === 3 && 'Step 4'}
                        </p>
                      </div>
                    </div>
                    {idx < 3 && (
                      <div className="flex-1 mx-4">
                        <div className={`h-[2px] rounded-full transition-all ${
                          ['processing', 'preview', 'saving'].indexOf(stage) > idx ? 'bg-gray-300' : 'bg-gray-200'
                        }`} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Original Circle Stepper (Other stages) */
            <div className="flex items-center justify-between">
              {['upload', 'processing', 'preview', 'saving'].map((s, idx) => (
                <div key={s} className="flex items-center">
                  <div className={`flex items-center justify-center w-14 h-14 rounded-full border-2 ${ 
                    stage === s ? 'border-[#0F0F11] bg-[#0F0F11] text-white' : 
                    ['processing', 'preview', 'saving'].indexOf(stage) > idx - 1 ? 'border-[#7B5CF0] bg-[#7B5CF0] text-white' : 
                    'border-gray-300 bg-white text-gray-400'
                  }`}>
                    {s === 'upload' && <Upload className="w-6 h-6" />}
                    {s === 'processing' && <Zap className="w-6 h-6" />}
                    {s === 'preview' && <Eye className="w-6 h-6" />}
                    {s === 'saving' && <Save className="w-6 h-6" />}
                  </div>
                  <div className="ml-4">
                    <p className={`text-base font-semibold ${stage === s ? 'text-[#0F0F11]' : 'text-gray-500'}`}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </p>
                  </div>
                  {idx < 3 && <ChevronRight className="w-6 h-6 text-gray-300 mx-6" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className={stage === 'upload' ? 'px-8 pb-8' : 'max-w-7xl mx-auto'}>
          {stage === 'upload' && (
            <div className="relative p-[2px] rounded-xl group">
              {/* Magenta + Black + Purple glow (subtle) */}
              <div className={`absolute inset-0 rounded-xl blur-md transition-opacity duration-300 bg-gradient-to-r from-black via-purple-600 to-fuchsia-600 ${
                isDragging ? 'opacity-30' : 'opacity-15 group-hover:opacity-20'
              }`}></div>
              
              <div 
                className="relative bg-white rounded-xl border-2 border-dashed border-gray-300 p-12 transition-all hover:border-purple-400"
                style={{ boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}
              >
                <div
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  onDragLeave={handleDragLeave}
                  className="text-center cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="w-16 h-16 text-[#0F0F11] mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Drop files here or click to browse
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Supports: CSV, Excel (.xlsx, .xls), PDF, Images (PNG, JPG), Text files, JSON, XML
                  </p>
                  <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <FileSpreadsheet className="w-4 h-4" />
                      CSV/Excel
                    </div>
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      PDF
                    </div>
                    <div className="flex items-center gap-1">
                      <ImageIcon className="w-4 h-4" />
                      Images
                    </div>
                    <div className="flex items-center gap-1">
                      <FileIcon className="w-4 h-4" />
                      JSON/XML
                    </div>
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      Text
                    </div>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls,.pdf,.txt,.png,.jpg,.jpeg,.json,.xml"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Uploaded Files Card */}
          {stage === 'upload' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 mt-6 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Recent Uploads</h3>
                    <p className="text-xs text-gray-500 mt-1">Files uploaded by team members</p>
                  </div>
                  <button
                    onClick={fetchRecentUploads}
                    disabled={uploadsLoading}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    title="Refresh uploads"
                  >
                    <RotateCcw className={`w-3.5 h-3.5 ${uploadsLoading ? 'animate-spin' : ''}`} />
                    <span className="text-xs font-medium">Refresh</span>
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto" style={{ maxHeight: '420px' }}>
                <table className="w-full">
                  <thead className="bg-gray-100 border-b border-gray-200 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">File Name</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Uploaded By</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">File Type</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Records</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {uploadsLoading ? (
                      <tr>
                        <td colSpan="7" className="px-6 py-8 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Loader2 className="w-5 h-5 text-purple-600 animate-spin" />
                            <span className="text-gray-500">Loading recent uploads...</span>
                          </div>
                        </td>
                      </tr>
                    ) : recentUploads.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="px-6 py-8 text-center">
                          <div className="flex flex-col items-center gap-2">
                            <FileText className="w-12 h-12 text-gray-300" />
                            <p className="text-gray-500">No recent uploads yet</p>
                            <p className="text-sm text-gray-400">Upload your first file to get started</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      recentUploads
                        // Apply search filter
                        .filter((upload) => {
                          if (!uploadSearchQuery) return true;
                          const searchLower = uploadSearchQuery.toLowerCase();
                          return (
                            upload.file_name.toLowerCase().includes(searchLower) ||
                            upload.uploaded_by.toLowerCase().includes(searchLower) ||
                            upload.file_type.toLowerCase().includes(searchLower)
                          );
                        })
                        // Apply file type filter
                        .filter((upload) => {
                          if (fileTypeFilter === 'all') return true;
                          return upload.file_type === fileTypeFilter;
                        })
                        // Apply sorting
                        .sort((a, b) => {
                          const dateA = new Date(a.uploaded_at);
                          const dateB = new Date(b.uploaded_at);
                          return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
                        })
                        .map((upload, index) => (
                        <UploadedFileRow 
                          key={upload.id || index}
                          uploadId={upload.id}
                          fileName={upload.file_name} 
                          user={upload.uploaded_by} 
                          time={new Date(upload.uploaded_at).toLocaleTimeString('en-US', { 
                            hour: '2-digit', 
                            minute: '2-digit', 
                            second: '2-digit' 
                          })} 
                          fileType={upload.file_type} 
                          records={upload.row_count}
                          status={upload.ml_prep_status}
                          isOwner={upload.is_owner}
                          onDelete={() => handleDeleteUpload(upload.id)}
                        />
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {stage === 'processing' && (
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div className="text-center">
                {getFileIcon()}
                <h3 className="text-lg font-semibold text-gray-900 mt-4 mb-2">
                  {uploadedFile?.name}
                </h3>
                <p className="text-sm text-gray-600 mb-6">
                  {fileType === 'unstructured' ? 'Running OCR and entity extraction...' : 'Analyzing structure...'}
                </p>
                
                <div className="max-w-md mx-auto">
                  <div className="flex items-center justify-between text-sm text-gray-700 mb-2">
                    <span>{ocrProgress.status}</span>
                    <span>{ocrProgress.current} / {ocrProgress.total}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-[#5B3CC9] h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(ocrProgress.current / ocrProgress.total) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-center gap-2 text-[#5B3CC9]">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm">Processing...</span>
                </div>

                {/* Processing Logs */}
                {processingLogs.length > 0 && (
                  <div className="mt-8 max-w-2xl mx-auto">
                    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <FileCheck className="w-4 h-4 text-gray-600" />
                        <h4 className="text-sm font-semibold text-gray-700">Processing Log</h4>
                      </div>
                      <div className="space-y-1 max-h-64 overflow-y-auto text-left font-mono text-xs">
                        {processingLogs.map((log, idx) => (
                          <div 
                            key={idx} 
                            className={`flex items-start gap-2 ${
                              log.type === 'error' ? 'text-red-600' : 
                              log.type === 'success' ? 'text-green-600' : 
                              'text-gray-700'
                            }`}
                          >
                            <span className="text-gray-400 text-[10px] w-20 flex-shrink-0">{log.timestamp}</span>
                            <span className="flex-shrink-0 mt-0.5">{getIconComponent(log.icon)}</span>
                            <span className="flex-1">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {stage === 'preview' && previewData && (
            <div className="space-y-4">
              {/* Preview Header */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Preview & Edit</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {previewData.total_rows} rows • Review and edit before saving
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      placeholder="Dataset name (optional)"
                      value={datasetConfig.datasetName}
                      onChange={(e) => setDatasetConfig({...datasetConfig, datasetName: e.target.value})}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                    <button
                      onClick={() => navigate('/data-cleaning', { 
                        state: { 
                          sessionId, 
                          datasetType: datasetConfig.datasetType,
                          rowCount: previewData.total_rows 
                        }
                      })}
                      className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 text-gray-700 rounded-lg hover:border-purple-primary/40 transition-all text-sm font-medium"
                    >
                      <BarChart3 className="w-4 h-4" />
                      View Quality Report
                    </button>
                    <button
                      onClick={handleContinueToMLPrep}
                      disabled={isProcessing}
                      className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:bg-gray-300 shadow-md text-sm font-medium"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Saving & Loading...
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4" />
                          Save & Start ML Prep
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* OCR Info (for unstructured) */}
                {fileType === 'unstructured' && ocrResult && (
                  <div className="flex items-center gap-6 text-sm text-gray-600 border-t pt-4 mt-4">
                    <div className="flex items-center gap-2">
                      <FileCheck className="w-4 h-4" />
                      {ocrResult.page_count} pages processed
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      {ocrResult.processing_time?.toFixed(1)}s
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      {(ocrResult.confidence * 100).toFixed(0)}% confidence
                    </div>
                  </div>
                )}
              </div>

              {/* Table */}
              <div className="bg-white rounded-none shadow-sm overflow-hidden -mx-6">
                {/* Search bar */}
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="relative flex-1 max-w-md">
                      <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                        <Search className="w-4 h-4 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        placeholder="Search columns or data..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                      {searchQuery && (
                        <button
                          onClick={() => setSearchQuery('')}
                          className="absolute inset-y-0 right-3 flex items-center"
                        >
                          <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                        </button>
                      )}
                    </div>
                    <span className="text-sm text-gray-600">
                      {searchQuery ? `Filtering results` : `${previewData.total_rows} total rows`}
                    </span>
                  </div>
                </div>
                
                <div className="overflow-x-auto w-full">
                  {!previewData.rows || previewData.rows.length === 0 ? (
                    <div className="text-center py-12">
                      <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-600 mb-2">No data to display</p>
                      <p className="text-sm text-gray-500">The uploaded file appears to be empty or has no valid data.</p>
                    </div>
                  ) : !previewData.rows[0] || !previewData.rows[0].data ? (
                    <div className="text-center py-12">
                      <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
                      <p className="text-red-600 mb-2">Invalid data structure</p>
                      <p className="text-sm text-gray-500">The preview data is missing required fields.</p>
                      <pre className="mt-4 text-xs text-left bg-gray-100 p-4 rounded max-w-md mx-auto overflow-auto">
                        {JSON.stringify(previewData, null, 2)}
                      </pre>
                    </div>
                  ) : (
                  <table className="w-full">
                    <thead className="bg-gray-800 border-b-2 border-gray-700">
                      <tr>
                        <th className="sticky left-0 z-10 bg-gray-800 px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider w-14 border-r border-gray-700 whitespace-nowrap">
                          #
                        </th>
                        {Object.keys(previewData.rows[0].data).map((col) => (
                          <th key={col} className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider whitespace-nowrap">
                            {col.replace(/_/g, ' ')}
                          </th>
                        ))}
                        <th className="px-4 py-3 text-right text-xs font-bold text-white uppercase tracking-wider w-20 whitespace-nowrap">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {previewData.rows
                        .filter((row) => {
                          if (!searchQuery) return true;
                          const searchLower = searchQuery.toLowerCase();
                          // Search in all column values and column names
                          return Object.entries(row.data).some(([colName, value]) => 
                            colName.toLowerCase().includes(searchLower) ||
                            String(value || '').toLowerCase().includes(searchLower)
                          );
                        })
                        .map((row, rowIndex) => {
                          const rowBg = row.is_edited ? '#fef3c7' : (rowIndex % 2 === 0 ? '#ffffff' : '#f9fafb');
                          return (
                        <tr key={row.staging_id} className={`${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'} ${row.is_edited ? 'bg-yellow-50' : ''} hover:bg-blue-50 transition-colors`}>
                          <td className="sticky left-0 z-10 px-4 py-2 text-sm font-semibold text-gray-500 border-r border-gray-200 text-center" style={{ backgroundColor: rowBg }}>
                            {row.row_number}
                          </td>
                          {Object.entries(row.data).map(([colName, value]) => (
                            <td key={colName} className="px-4 py-2 text-[13px] whitespace-nowrap">
                              {editingCell?.rowIndex === rowIndex && editingCell?.columnName === colName ? (
                                <input
                                  type="text"
                                  value={editingCell.value}
                                  onChange={(e) => setEditingCell({...editingCell, value: e.target.value})}
                                  onBlur={handleCellSave}
                                  onKeyDown={(e) => e.key === 'Enter' && handleCellSave()}
                                  className="w-full px-2 py-0.5 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-[13px]"
                                  autoFocus
                                />
                              ) : (
                                <div
                                  onClick={() => handleCellEdit(rowIndex, colName, value)}
                                  className="cursor-pointer hover:bg-gray-100 rounded px-1 py-0.5 text-gray-900 max-w-[200px] truncate"
                                  title={value !== null && value !== undefined ? String(value) : 'null'}
                                >
                                  {value !== null && value !== undefined ? String(value) : <span className="text-gray-400 italic">null</span>}
                                </div>
                              )}
                            </td>
                          ))}
                          <td className="px-4 py-2 text-right">
                            <button
                              onClick={() => handleRowDelete(rowIndex)}
                              className="text-red-600 hover:text-red-800"
                              title="Delete row"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
                    <div className="text-sm text-gray-700">
                      Page {currentPage} of {totalPages} • {previewData.total_rows} total rows
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1 || isProcessing}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages || isProcessing}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {stage === 'saving' && (
            <div className="bg-white rounded-lg shadow-sm p-12 text-center">
              <Loader2 className="w-16 h-16 text-[#5B3CC9] mx-auto mb-4 animate-spin" />
              <h3 className="text-lg font-semibold text-gray-900">Saving to PostgreSQL...</h3>
              <p className="text-sm text-gray-600 mt-2">
                Writing {previewData?.total_rows || 0} records to flexible_dataset_wide table
              </p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

// ========== UPLOADED FILE ROW COMPONENT ==========
function UploadedFileRow({ uploadId, fileName, user, time, fileType, records, status, isOwner = true, onDelete }) {
  // Profile avatar color map - soft, subtle pastels matching dashboard
  const getAvatarColor = (username) => {
    const colors = [
      'bg-gradient-to-br from-purple-200 to-purple-300',
      'bg-gradient-to-br from-violet-200 to-violet-300', 
      'bg-gradient-to-br from-indigo-200 to-indigo-300',
      'bg-gradient-to-br from-blue-200 to-blue-300',
      'bg-gradient-to-br from-pink-200 to-purple-300',
      'bg-gradient-to-br from-blue-200 to-indigo-300'
    ];
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  const getInitials = (username) => {
    const parts = username.split(/[_\s]/);
    if (parts.length > 1) {
      return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
    }
    return username.substring(0, 2).toUpperCase();
  };

  // File type badge color (neutral theme)
  const getFileTypeBadge = () => {
    const typeMap = {
      'CSV': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileSpreadsheet },
      'CSV/Excel': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileSpreadsheet },
      'Excel': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileSpreadsheet },
      'PDF': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileText },
      'PDF/Image': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileText },
      'JSON': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileIcon },
      'XML': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileIcon },
      'ZIP': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileIcon },
      'Image': { bg: 'bg-gray-100', text: 'text-gray-700', icon: ImageIcon },
      'API Import': { bg: 'bg-gray-100', text: 'text-gray-700', icon: Zap }
    };
    const config = typeMap[fileType] || typeMap['CSV'];
    const IconComponent = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${config.bg} ${config.text} text-xs font-medium`}>
        <IconComponent className="w-3.5 h-3.5" />
        {fileType}
      </span>
    );
  };

  // Status badge (neutral theme)
  const getStatusBadge = () => {
    const statusMap = {
      'not_started': { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Not Started', icon: Clock },
      'ready': { bg: 'bg-green-50', text: 'text-green-700', label: 'Ready', icon: CheckCircle },
      'processing': { bg: 'bg-blue-50', text: 'text-blue-700', label: 'Processing', icon: Loader2 },
      'complete': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Complete', icon: Check }
    };
    
    const config = statusMap[status] || statusMap['not_started'];
    const IconComponent = config.icon;
    
    // Dim colors for non-owned files
    const bgClass = !isOwner ? 'bg-gray-50' : config.bg;
    const textClass = !isOwner ? 'text-gray-400' : config.text;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${bgClass} ${textClass} text-xs font-medium`}>
        <IconComponent className={`w-3.5 h-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
        {config.label}
        {!isOwner && <Lock className="w-3 h-3 ml-0.5" />}
      </span>
    );
  };

  return (
    <tr className={`hover:bg-gray-50 transition-colors ${!isOwner ? 'bg-gray-50/50' : ''}`}>
      <td className="px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">
            {!isOwner ? (
              <Lock className="w-4 h-4 text-gray-400" title="View Only - Uploaded by another user" />
            ) : (
              <FileCheck className="w-4 h-4 text-gray-400" />
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-medium text-gray-900 truncate max-w-xs" title={fileName}>
              {fileName}
            </span>
            {!isOwner && (
              <span className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                <Shield className="w-3 h-3" />
                View Only
              </span>
            )}
          </div>
        </div>
      </td>
      <td className="px-6 py-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full ${getAvatarColor(user)} flex items-center justify-center text-purple-700 text-xs font-bold flex-shrink-0 ${!isOwner ? 'opacity-75' : ''}`}>
            {getInitials(user)}
          </div>
          <div className="flex flex-col">
            <span className="text-sm text-gray-900">{user}</span>
            {!isOwner && (
              <span className="text-xs text-gray-500">Other Team Member</span>
            )}
          </div>
        </div>
      </td>
      <td className="px-6 py-3 text-sm text-gray-600">{time}</td>
      <td className="px-6 py-3">{getFileTypeBadge()}</td>
      <td className="px-6 py-3">
        <span className="text-sm font-medium text-gray-900">
          {records?.toLocaleString() || '—'}
        </span>
        <span className="text-xs text-gray-500 ml-1">rows</span>
      </td>
      <td className="px-6 py-3">{getStatusBadge()}</td>
      <td className="px-6 py-3">
        <div className="flex items-center justify-center">
          {isOwner && onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
              title="Delete upload"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          {!isOwner && (
            <span className="text-xs text-gray-400">—</span>
          )}
        </div>
      </td>
    </tr>
  );
}