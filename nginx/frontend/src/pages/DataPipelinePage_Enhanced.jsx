/**
 * Enhanced Data Pipeline Page
 * ============================
 * Unified workflow for both structured (CSV/Excel) and unstructured (PDF/IMG/TXT) data
 * 
 * Flow: Upload → Process/OCR → Preview → Edit → Save
 * - Uses new flexible API (/api/v1/flexible/*)
 * - 100% flexible schema (no hardcoded fields)
 * - Real-time editing with cell-level changes
 * - OCR progress tracking with page count
 * - Entity extraction preview
 * 
 * Author: Syarifah Fajriyah
 * Date: April 7, 2026
 */

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Zap
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function DataPipelinePageEnhanced() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  // ========== STATE MANAGEMENT ==========
  const [stage, setStage] = useState('upload'); // upload → processing → preview → saving
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileType, setFileType] = useState(null); // 'structured' or 'unstructured'
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  
  // OCR-specific state
  const [ocrResult, setOcrResult] = useState(null); // {validation_id, extracted_text, page_count, etc}
  const [ocrProgress, setOcrProgress] = useState({ current: 0, total: 0, status: '' });
  
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

  // ========== FILE UPLOAD HANDLERS ==========
  
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) processFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const processFile = async (file) => {
    setUploadedFile(file);
    setError(null);
    setIsProcessing(true);
    setStage('processing');
    
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
    
    try {
      if (isUnstructured) {
        await processUnstructuredFile(file);
      } else {
        await processStructuredFile(file);
      }
    } catch (err) {
      console.error('Processing error:', err);
      setError(err.response?.data?.detail || err.message || 'Processing failed');
      setIsProcessing(false);
      setStage('upload');
    }
  };

  // ========== STRUCTURED DATA WORKFLOW ==========
  
  const processStructuredFile = async (file) => {
    setOcrProgress({ current: 1, total: 1, status: 'Analyzing CSV structure...' });
    
    // Step 1: Upload for preview
    const uploadResult = await flexibleAPI.uploadStructured(file, datasetConfig.datasetType);
    
    setSessionId(uploadResult.session_id);
    setOcrProgress({ current: 1, total: 1, status: `Detected ${uploadResult.row_count} rows` });
    
    // Step 2: Fetch preview
    await loadPreview(uploadResult.session_id, 1);
    
    setIsProcessing(false);
    setStage('preview');
  };

  // ========== UNSTRUCTURED DATA WORKFLOW ==========
  
  const processUnstructuredFile = async (file) => {
    // Step 1: Upload for OCR
    setOcrProgress({ current: 0, total: 1, status: 'Uploading to OCR engine...' });
    
    const ocrResult = await flexibleAPI.uploadUnstructured(file);
    
    setOcrResult(ocrResult);
    setOcrProgress({ 
      current: ocrResult.page_count || 1, 
      total: ocrResult.page_count || 1, 
      status: ocrResult.status === 'success' ? 'OCR completed' : 'OCR failed' 
    });
    
    if (ocrResult.status !== 'success') {
      throw new Error(ocrResult.error || 'OCR processing failed');
    }
    
    // Step 2: Convert to tabular
    setOcrProgress({ current: 1, total: 2, status: 'Converting to tabular format...' });
    
    const convertResult = await flexibleAPI.convertUnstructuredToTabular(
      ocrResult.validation_id,
      datasetConfig.datasetType,
      datasetConfig.conversionMode
    );
    
    setSessionId(convertResult.session_id);
    setOcrProgress({ current: 2, total: 2, status: `Converted to ${convertResult.row_count} rows` });
    
    // Step 3: Fetch preview
    await loadPreview(convertResult.session_id, 1);
    
    setIsProcessing(false);
    setStage('preview');
  };

  // ========== PREVIEW MANAGEMENT ==========
  
  const loadPreview = async (sessionId, page = 1) => {
    const preview = await flexibleAPI.getPreview(sessionId, page, pageSize);
    setPreviewData(preview);
    setCurrentPage(page);
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
      alert(`✅ Dataset saved successfully!\n\n` +
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

  // ========== RESET ==========
  
  const handleReset = () => {
    setStage('upload');
    setUploadedFile(null);
    setFileType(null);
    setError(null);
    setOcrResult(null);
    setOcrProgress({ current: 0, total: 0, status: '' });
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
    if (['csv', 'xlsx', 'xls'].includes(ext)) return <FileSpreadsheet className="w-12 h-12 text-green-600" />;
    if (['pdf'].includes(ext)) return <FileText className="w-12 h-12 text-red-600" />;
    if (['png', 'jpg', 'jpeg'].includes(ext)) return <ImageIcon className="w-12 h-12 text-blue-600" />;
    return <FileIcon className="w-12 h-12 text-gray-600" />;
  };

  const totalPages = previewData ? Math.ceil(previewData.total_rows / pageSize) : 0;

  // ========== RENDER ==========
  
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-50 p-6">
        {/* Header */}
        <div className="max-w-7xl mx-auto mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Data Pipeline</h1>
              <p className="text-sm text-gray-600 mt-1">
                Upload structured (CSV/Excel) or unstructured (PDF/IMG/TXT) data
              </p>
            </div>
            {stage !== 'upload' && (
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <RotateCcw className="w-4 h-4" />
                Start Over
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-7xl mx-auto mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
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

        {/* Stage Indicator */}
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex items-center justify-between">
            {['upload', 'processing', 'preview', 'saving'].map((s, idx) => (
              <div key={s} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${ 
                  stage === s ? 'border-blue-600 bg-blue-600 text-white' : 
                  ['processing', 'preview', 'saving'].indexOf(stage) > idx - 1 ? 'border-green-600 bg-green-600 text-white' : 
                  'border-gray-300 bg-white text-gray-400'
                }`}>
                  {s === 'upload' && <Upload className="w-5 h-5" />}
                  {s === 'processing' && <Zap className="w-5 h-5" />}
                  {s === 'preview' && <Eye className="w-5 h-5" />}
                  {s === 'saving' && <Save className="w-5 h-5" />}
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${stage === s ? 'text-blue-600' : 'text-gray-500'}`}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </p>
                </div>
                {idx < 3 && <ChevronRight className="w-5 h-5 text-gray-300 mx-4" />}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto">
          {stage === 'upload' && (
            <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12">
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="text-center cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Drop files here or click to browse
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Supports: CSV, Excel (.xlsx, .xls), PDF, Images (PNG, JPG), Text files
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
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.pdf,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileUpload}
                  className="hidden"
                />
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
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(ocrProgress.current / ocrProgress.total) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-center gap-2 text-blue-600">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm">Processing...</span>
                </div>
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
                      onClick={handleSaveDataset}
                      disabled={isProcessing}
                      className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          Save to Database
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
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">
                          #
                        </th>
                        {previewData.rows[0] && Object.keys(previewData.rows[0].data).map((col) => (
                          <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            {col.replace(/_/g, ' ')}
                          </th>
                        ))}
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {previewData.rows.map((row, rowIndex) => (
                        <tr key={row.staging_id} className={row.is_edited ? 'bg-yellow-50' : ''}>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {row.row_number}
                          </td>
                          {Object.entries(row.data).map(([colName, value]) => (
                            <td key={colName} className="px-4 py-3 text-sm">
                              {editingCell?.rowIndex === rowIndex && editingCell?.columnName === colName ? (
                                <input
                                  type="text"
                                  value={editingCell.value}
                                  onChange={(e) => setEditingCell({...editingCell, value: e.target.value})}
                                  onBlur={handleCellSave}
                                  onKeyDown={(e) => e.key === 'Enter' && handleCellSave()}
                                  className="w-full px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  autoFocus
                                />
                              ) : (
                                <div
                                  onClick={() => handleCellEdit(rowIndex, colName, value)}
                                  className="cursor-pointer hover:bg-gray-100 rounded px-2 py-1 min-h-[28px]"
                                >
                                  {value !== null && value !== undefined ? String(value) : <span className="text-gray-400 italic">null</span>}
                                </div>
                              )}
                            </td>
                          ))}
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleRowDelete(rowIndex)}
                              className="text-red-600 hover:text-red-800"
                              title="Delete row"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
              <Loader2 className="w-16 h-16 text-blue-600 mx-auto mb-4 animate-spin" />
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
