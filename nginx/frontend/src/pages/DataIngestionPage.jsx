import { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileUp,
  Database,
  Clock3,
  CheckCircle2,
  AlertCircle,
  Tag,
  Trash2,
  Search,
  Filter,
  Calendar,
  Rocket,
  Activity,
  HardDrive,
  ChevronRight,
  Eye,
  X,
  ChevronLeft,
  ChevronRight as ChevronRightIcon,
  Loader2,
  FileText,
  ArrowRight,
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { dataIngestionAPI } from '../services/api-ingestion';
import { unstructuredPipelineAPI, structuredPipelineAPI } from '../services/api-complete';

const MOCK_BATCHES = [
  {
    id: '9161cd88-e7bb-43a6-9f6f-0f62ecf9f01a',
    dataset: '111_patients_wide.csv',
    user: 'Dr. Ahmad',
    fileType: 'CSV',
    uploaded: '2026-04-19 14:30',
    records: 111,
    status: 'ready',
  },
  {
    id: '7f1cebb8-1b03-4cf3-a8ab-c3f074a9ad37',
    dataset: 'sle_cohort_2.xlsx',
    user: 'Dr. Sarah',
    fileType: 'XLSX',
    uploaded: '2026-04-19 16:45',
    records: 89,
    status: 'processing',
  },
  {
    id: 'aa3c8f2d-9b14-4e87-bd6c-2a1f5e8d9c3b',
    dataset: 'chest_xray_001.jpg',
    user: 'Dr. Ahmad',
    fileType: 'JPG',
    uploaded: '2026-04-19 13:20',
    records: 1,
    status: 'ready',
  },
  {
    id: 'cc7d4e1f-3a28-4b96-9e5a-8f2b6d9c1a4e',
    dataset: 'patient_report_scan.pdf',
    user: 'Dr. Lim',
    fileType: 'PDF',
    uploaded: '2026-04-19 11:30',
    records: 1,
    status: 'labeled',
  },
  {
    id: 'be34fd53-c8d0-49f4-96ac-38f9e021d8f3',
    dataset: 'ra_patients.csv',
    user: 'Dr. Lim',
    fileType: 'CSV',
    uploaded: '2026-04-19 10:00',
    records: 45,
    status: 'labeled',
  },
  {
    id: '15aa7a6f-8ec1-487a-a85c-5cc5d7c7ca49',
    dataset: 'legacy_invalid.json',
    user: 'System',
    fileType: 'JSON',
    uploaded: '2026-04-18 09:15',
    records: 0,
    status: 'failed',
  },
];

const STATUS_META = {
  ready: {
    label: 'Ready for Processing',
    className: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    icon: CheckCircle2,
  },
  processing: {
    label: 'Processing',
    className: 'bg-amber-100 text-amber-700 border-amber-200',
    icon: Clock3,
  },
  failed: {
    label: 'Failed',
    className: 'bg-rose-100 text-rose-700 border-rose-200',
    icon: AlertCircle,
  },
  labeled: {
    label: 'Labeled',
    className: 'bg-sky-100 text-sky-700 border-sky-200',
    icon: Tag,
  },
};

const ACTIVITY_LOG = [
  { date: 'April 20, 2026', time: '14:30', event: 'Uploaded: 111_patients_wide.csv (111 records)' },
  { date: 'April 20, 2026', time: '12:15', event: 'Deleted batch: test_data_old' },
  { date: 'April 19, 2026', time: '16:45', event: 'Uploaded: sle_cohort_2.xlsx (89 records)' },
  { date: 'April 19, 2026', time: '10:00', event: 'Uploaded: ra_patients.csv (45 records)' },
];

export default function DataIngestionPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadType, setUploadType] = useState('structured'); // 'structured' or 'unstructured'
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [datasetName, setDatasetName] = useState('SLE Patients - April 2026');
  const [diseaseCode, setDiseaseCode] = useState('');
  
  // Upload states
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  
  // OCR Preview states (for unstructured)
  const [ocrPreview, setOcrPreview] = useState(null);
  const [validationId, setValidationId] = useState(null);
  const [showOCRPreview, setShowOCRPreview] = useState(false);
  
  // Preview states
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [previewPage, setPreviewPage] = useState(0);
  const rowsPerPage = 20;
  
  // Recent uploads
  const [recentUploads, setRecentUploads] = useState([]);
  const [isLoadingUploads, setIsLoadingUploads] = useState(false);

  const [search, setSearch] = useState('');

  // Load recent uploads when tab changes
  useEffect(() => {
    if (activeTab === 'recent') {
      loadRecentUploads();
    }
  }, [activeTab]);

  const loadRecentUploads = async () => {
    setIsLoadingUploads(true);
    try {
      const data = await dataIngestionAPI.getRecentUploads(10);
      // Backend now returns simplified array: [{ id, dataset, user, fileType, uploaded, records, is_owner }]
      setRecentUploads(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load recent uploads:', err);
      setError('Failed to load recent uploads. Using local data.');
      // Fallback to mock data if API fails
      setRecentUploads(MOCK_BATCHES);
    } finally {
      setIsLoadingUploads(false);
    }
  };

  const filteredBatches = useMemo(() => {
    const batches = recentUploads.length > 0 ? recentUploads : MOCK_BATCHES;
    return batches.filter((b) => {
      const matchesSearch =
        (b.id?.toLowerCase().includes(search.toLowerCase()) || '') ||
        (b.dataset?.toLowerCase().includes(search.toLowerCase()) || '') ||
        (b.user?.toLowerCase().includes(search.toLowerCase()) || '');
      // No status filter - show all recent uploads
      return matchesSearch;
    });
  }, [recentUploads, search]);

  const groupedActivity = useMemo(() => {
    const groups = {};
    for (const item of ACTIVITY_LOG) {
      groups[item.date] = groups[item.date] || [];
      groups[item.date].push(item);
    }
    return groups;
  }, []);

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      validateFile(dropped);
    }
  };

  const generateDiseaseCode = () => {
    // Auto-generate unique tracking code (format: DC-YYYYMMDD-XXXXX)
    const date = new Date();
    const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.random().toString(36).substring(2, 7).toUpperCase();
    return `DC-${dateStr}-${random}`;
  };

  const validateFile = (selectedFile) => {
    const supported = ['csv', 'xlsx', 'xls', 'json', 'pdf', 'jpg', 'jpeg', 'png', 'webp', 'tiff', 'tif', 'txt'];
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (!supported.includes(ext)) {
      setError('Invalid format. Supported: CSV, XLSX, JSON, PDF, Images, TXT.');
      setMessage('');
      return false;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File too large. Maximum size is 50MB.');
      setMessage('');
      return false;
    }
    // Auto-generate disease code when file is validated
    if (!diseaseCode) {
      setDiseaseCode(generateDiseaseCode());
    }
    
    setMessage(`File validated: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`);
    setError('');
    return true;
  };

  // UNSTRUCTURED PIPELINE: Step 1 - Upload for OCR
  const handleUnstructuredUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setIsUploading(true);
    setError('');
    setMessage('Uploading for OCR processing...');
    
    try {
      const result = await unstructuredPipelineAPI.uploadForOCR(file);
      
      setValidationId(result.validation_id);
      setOcrPreview({
        validationId: result.validation_id,
        extractedText: result.extracted_text,
        medicalEntities: result.medical_entities || [],
        pageCount: result.page_count,
        confidence: result.confidence,
        structuredTests: result.structured_tests || []
      });
      
      setShowOCRPreview(true);
      setMessage(`OCR complete! Extracted ${result.extracted_text?.length || 0} characters from ${result.page_count} pages.`);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      setError(`OCR processing failed: ${errorMsg}`);
      console.error('OCR error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  // UNSTRUCTURED PIPELINE: Step 2 - Convert OCR to Tabular
  const handleConvertToTabular = async () => {
    if (!validationId) return;
    
    setIsUploading(true);
    setError('');
    setMessage('Converting OCR results to tabular format...');
    
    try {
      const result = await unstructuredPipelineAPI.convertToTabular(validationId);
      
      // Store session ID for next step
      sessionStorage.setItem('preview_session_id', result.session_id);
      sessionStorage.setItem('workflow_stage', 'preview');
      
      setMessage('Conversion successful! Redirecting to data preparation...');
      
      // Navigate to data preparation page
      setTimeout(() => {
        navigate('/data-preparation');
      }, 1000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      setError(`Conversion failed: ${errorMsg}`);
      console.error('Conversion error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  // STRUCTURED PIPELINE: Upload CSV/Excel for Preview
  const handleStructuredUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setIsUploading(true);
    setError('');
    setMessage('Uploading file...');
    
    try {
      const result = await structuredPipelineAPI.uploadForPreview(file, 'structured');
      
      // Store session ID for next step
      sessionStorage.setItem('preview_session_id', result.session_id);
      sessionStorage.setItem('workflow_stage', 'preview');
      
      setMessage(`Upload successful! ${result.row_count} rows loaded. Redirecting to data preparation...`);
      
      // Navigate to data preparation page
      setTimeout(() => {
        navigate('/data-preparation');
      }, 1000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      setError(`Upload failed: ${errorMsg}`);
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  // Main upload handler - routes to correct pipeline
  const handleUpload = async () => {
    if (uploadType === 'unstructured') {
      await handleUnstructuredUpload();
    } else {
      await handleStructuredUpload();
    }
  };



  // Step 3: Import from Preview (after user reviews)
  const handleImportFromPreview = async () => {
    if (!previewData) return;
    
    setIsUploading(true);
    setError('');
    
    try {
      const result = await dataIngestionAPI.importFromPreview(previewData);
      
      setMessage(
        `Import successful! ` +
        `${result.patients_created || result.rows_imported || 0} records saved.`
      );
      
      setShowPreview(false);
      setPreviewData(null);
      setFile(null);
      
      // Reload recent uploads
      if (activeTab === 'recent') {
        loadRecentUploads();
      }
      
    } catch (err) {
      setError(`Import failed: ${err.response?.data?.detail || err.message}`);
      console.error('Import error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 border-b border-purple-100 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Data Ingestion</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0]">Data Ingestion</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#f3f2f8] via-[#f8f7fc] to-[#eeeafb]" style={{ zoom: 0.9 }}>
        <div className="max-w-7xl mx-auto space-y-6">

          <section className="rounded-2xl border border-purple-100 bg-white/90 shadow-[0_14px_34px_rgba(88,55,160,0.10)] overflow-hidden">
            <div className="flex border-b border-purple-100">
              {[
                { id: 'upload', label: 'Upload File' },
                { id: 'recent', label: 'Recent Uploads' },
                { id: 'activity', label: 'Activity Log' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-5 py-3 text-sm font-semibold transition-all ${
                    activeTab === tab.id
                      ? 'text-purple-700 border-b-2 border-purple-600 bg-purple-50/70'
                      : 'text-gray-500 hover:text-purple-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="p-6">
              {activeTab === 'upload' && (
                <div className="space-y-5">
                  {/* Upload Type Selector */}
                  <div className="flex gap-3 p-1 bg-gray-100 rounded-lg w-fit">
                    <button
                      onClick={() => setUploadType('structured')}
                      className={`px-4 py-2 rounded-md text-sm font-semibold transition-all ${
                        uploadType === 'structured'
                          ? 'bg-white text-purple-700 shadow'
                          : 'text-gray-600 hover:text-purple-700'
                      }`}
                    >
                      <Database className="w-4 h-4 inline mr-2" />
                      Structured (CSV/Excel)
                    </button>
                    <button
                      onClick={() => setUploadType('unstructured')}
                      className={`px-4 py-2 rounded-md text-sm font-semibold transition-all ${
                        uploadType === 'unstructured'
                          ? 'bg-white text-purple-700 shadow'
                          : 'text-gray-600 hover:text-purple-700'
                      }`}
                    >
                      <FileText className="w-4 h-4 inline mr-2" />
                      Unstructured (PDF/Image - Qwen OCR)
                    </button>
                  </div>

                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragging(true);
                    }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('ingestion-file-input')?.click()}
                    className={`rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all ${
                      dragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 bg-white hover:border-purple-400'
                    }`}
                  >
                    <FileUp className="w-12 h-12 mx-auto text-purple-500 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900">Drag & Drop Files Here</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {uploadType === 'structured' 
                        ? 'or click to browse (CSV, XLSX, JSON)'
                        : 'or click to browse (PDF, Images, TXT)'}
                    </p>
                    {file && (
                      <div className="mt-4 text-sm text-purple-700 font-medium">
                        Selected: {file.name}
                      </div>
                    )}
                    <input
                      id="ingestion-file-input"
                      type="file"
                      accept={uploadType === 'structured' ? '.csv,.xlsx,.xls,.json' : '.pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.txt'}
                      className="hidden"
                      onChange={(e) => {
                        const selected = e.target.files?.[0];
                        if (selected) {
                          setFile(selected);
                          validateFile(selected);
                        }
                      }}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">Dataset Name</label>
                      <input
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                        placeholder="SLE Patients - April 2026"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Tracking Code <span className="text-xs text-gray-500">(auto-generated)</span>
                      </label>
                      <input
                        value={diseaseCode}
                        readOnly
                        className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-600 cursor-not-allowed"
                        placeholder="Auto-generated on upload"
                      />
                    </div>
                  </div>

                  {isUploading && (
                    <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center gap-3">
                      <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
                      <span className="text-sm text-indigo-700">{message}</span>
                    </div>
                  )}

                  {error && (
                    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  {message && !isUploading && !error && (
                    <div className="p-3 rounded-lg bg-green-50 border border-green-200 text-sm text-green-700">
                      {message}
                    </div>
                  )}

                  {/* OCR Preview for Unstructured */}
                  {showOCRPreview && ocrPreview && (
                    <div className="rounded-lg border-2 border-purple-200 bg-purple-50 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-bold text-gray-900">OCR Extraction Result</h3>
                        <button
                          onClick={() => setShowOCRPreview(false)}
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>

                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="p-3 bg-white rounded-lg">
                          <p className="text-xs text-gray-600">Pages</p>
                          <p className="text-lg font-bold text-purple-600">{ocrPreview.pageCount}</p>
                        </div>
                        <div className="p-3 bg-white rounded-lg">
                          <p className="text-xs text-gray-600">Entities Found</p>
                          <p className="text-lg font-bold text-purple-600">{ocrPreview.medicalEntities.length}</p>
                        </div>
                        <div className="p-3 bg-white rounded-lg">
                          <p className="text-xs text-gray-600">Confidence</p>
                          <p className="text-lg font-bold text-purple-600">
                            {(ocrPreview.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>

                      <div className="p-3 bg-white rounded-lg mb-3 max-h-60 overflow-y-auto">
                        <p className="text-xs text-gray-600 mb-2">Extracted Text:</p>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">
                          {ocrPreview.extractedText?.substring(0, 500)}...
                        </p>
                      </div>

                      <button
                        onClick={handleConvertToTabular}
                        disabled={isUploading}
                        className="w-full px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <ArrowRight className="w-4 h-4" />
                        Convert to Tabular & Continue to Preview
                      </button>
                    </div>
                  )}

                  {!showOCRPreview && (
                    <button
                      onClick={handleUpload}
                      disabled={!file || isUploading}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold shadow-lg shadow-purple-500/25 hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          {uploadType === 'unstructured' ? 'Processing OCR...' : 'Uploading...'}
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          {uploadType === 'unstructured' ? 'Upload & Extract with Qwen OCR' : 'Upload & Preview'}
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}

              {activeTab === 'recent' && (
                <div>
                  {isLoadingUploads ? (
                    <div className="text-center py-12">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                      <p className="mt-3 text-sm text-gray-600">Loading recent uploads...</p>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-purple-100 overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-800 text-white">
                          <tr>
                            <th className="px-4 py-3 text-left font-semibold">Dataset</th>
                            <th className="px-4 py-3 text-left font-semibold">Uploaded By</th>
                            <th className="px-4 py-3 text-left font-semibold">Type</th>
                            <th className="px-4 py-3 text-left font-semibold">Date/Time</th>
                            <th className="px-4 py-3 text-left font-semibold">Records</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white">
                          {filteredBatches.length === 0 ? (
                            <tr>
                              <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                                No uploads found. Upload your first dataset to get started.
                              </td>
                            </tr>
                          ) : (
                            filteredBatches.map((batch) => {
                              return (
                                <tr key={batch.id} className="border-t border-gray-100 hover:bg-purple-50/30 transition-colors">
                                  <td className="px-4 py-3 text-gray-900 font-medium">{batch.dataset}</td>
                                  <td className="px-4 py-3 text-gray-700">{batch.user}</td>
                                  <td className="px-4 py-3">
                                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-purple-100 text-purple-700 text-xs font-semibold">
                                      {batch.fileType}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-gray-600 text-xs">{batch.uploaded}</td>
                                  <td className="px-4 py-3 text-gray-700">
                                    <span className="font-semibold">{batch.records}</span>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'activity' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-[1fr,220px] gap-3">
                    <div className="relative">
                      <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                      <input
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search by batch ID or filename"
                        className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:border-purple-500"
                      />
                    </div>
                    <button className="px-3 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 inline-flex items-center justify-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Date Range
                    </button>
                  </div>

                  <div className="rounded-xl border border-purple-100 bg-white p-4">
                    {Object.entries(groupedActivity).map(([date, items]) => (
                      <div key={date} className="mb-4 last:mb-0">
                        <h4 className="text-sm font-bold text-gray-900 mb-2">{date}</h4>
                        <div className="space-y-2">
                          {items.map((item, idx) => (
                            <div key={`${date}-${idx}`} className="flex items-start gap-3 text-sm text-gray-700">
                              <Activity className="w-4 h-4 text-purple-600 mt-0.5" />
                              <span className="font-mono text-xs text-gray-500 w-14">{item.time}</span>
                              <span>{item.event}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-xl border border-purple-100 bg-white p-4">
                    <h4 className="text-sm font-bold text-gray-900 mb-3">Filtered Batches</h4>
                    <div className="space-y-2">
                      {filteredBatches.map((batch) => (
                        <div key={batch.id} className="text-sm text-gray-700 flex items-center justify-between border-b border-gray-100 pb-2 last:border-b-0">
                          <span className="font-mono text-xs text-gray-500">{batch.id.slice(0, 16)}...</span>
                          <span>{batch.dataset}</span>
                          <span>{batch.records} records</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section className="grid grid-cols-4 gap-4">
            <InfoCard icon={Database} title="Structured Inputs" value="CSV / XLSX" subtitle="Wide-format clinical tables" />
            <InfoCard icon={FileUp} title="Unstructured Inputs" value="JSON" subtitle="Clinical note payloads" />
            <InfoCard icon={FileUp} title="Documents & Images" value="PDF / JPG / PNG" subtitle="Medical reports & imaging" />
            <InfoCard icon={HardDrive} title="Storage" value="Batch IDs" subtitle="Each upload version tracked" />
          </section>
        </div>
      </main>

      {/* Preview Modal */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Data Preview</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {previewData.preview?.format === 'unstructured' || previewData.format === 'unstructured'
                    ? `${previewData.preview?.word_count || previewData.word_count || 0} words${(previewData.preview?.ocr_used || previewData.ocr_used) ? ' (OCR extracted)' : ''}`
                    : `${previewData.preview?.row_count || previewData.row_count || 0} rows × ${previewData.preview?.column_count || previewData.column_count || 0} columns`
                  }
                </p>
              </div>
              <button
                onClick={() => setShowPreview(false)}
                className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-auto p-6">
              {/* Unstructured Format (PDF/Images/TXT) */}
              {(previewData.preview?.format === 'unstructured' || previewData.format === 'unstructured') && (
                <div className="space-y-4">
                  {/* Metadata */}
                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Document Information</h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Format:</span>
                        <span className="ml-2 font-semibold text-purple-700">Unstructured</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Text Length:</span>
                        <span className="ml-2 font-semibold text-gray-900">
                          {(previewData.preview?.text_length || previewData.text_length || 0).toLocaleString()} chars
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Word Count:</span>
                        <span className="ml-2 font-semibold text-gray-900">
                          {(previewData.preview?.word_count || previewData.word_count || 0).toLocaleString()} words
                        </span>
                      </div>
                    </div>
                    {(previewData.preview?.ocr_used || previewData.ocr_used) && (
                      <div className="mt-2 text-xs text-green-700 bg-green-50 px-2 py-1 rounded inline-block">
                        OCR Processing Applied
                      </div>
                    )}
                  </div>

                  {/* Text Preview */}
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-800 text-white px-4 py-2 text-sm font-semibold">
                      Extracted Text Preview
                    </div>
                    <div className="p-4 bg-white max-h-[400px] overflow-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                        {previewData.preview?.preview_text || previewData.preview_text || 'No text extracted'}
                      </pre>
                    </div>
                    {(previewData.preview?.preview_truncated || previewData.preview_truncated) && (
                      <div className="px-4 py-2 bg-amber-50 text-xs text-amber-700 border-t border-amber-200">
                        Preview truncated. Full text will be processed on import.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Structured Format (CSV/Excel/JSON) */}
              {(previewData.preview?.format === 'structured' || previewData.format === 'structured' || previewData.columns) && (
                <>
                  {/* Column Mapping Summary */}
                  {previewData.mapping_summary && (
                    <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <h3 className="text-sm font-semibold text-gray-900 mb-2">Column Mapping</h3>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Mapped:</span>
                          <span className="ml-2 font-semibold text-green-700">
                            {previewData.mapping_summary.mapped_count} columns
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Unmapped:</span>
                          <span className="ml-2 font-semibold text-yellow-700">
                            {previewData.mapping_summary.unmapped_count} columns
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Total:</span>
                          <span className="ml-2 font-semibold text-gray-900">
                            {previewData.preview?.column_count || previewData.column_count || 0} columns
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Data Table */}
                  <div className="overflow-auto max-h-[400px] border border-gray-200 rounded-lg">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-800 text-white sticky top-0">
                        <tr>
                          {((previewData.preview?.columns || previewData.columns) || []).slice(0, 10).map((col, idx) => (
                            <th key={idx} className="px-3 py-2 text-left font-semibold whitespace-nowrap">
                              <div>{typeof col === 'string' ? col : col.name}</div>
                              {col.mapped_to && (
                                <div className="text-[10px] text-gray-400 font-normal">
                                  {col.mapped_to}
                                </div>
                              )}
                            </th>
                          ))}
                          {(previewData.preview?.column_count || previewData.column_count || 0) > 10 && (
                            <th className="px-3 py-2 text-left text-gray-400">
                              +{(previewData.preview?.column_count || previewData.column_count) - 10} more...
                            </th>
                          )}
                        </tr>
                      </thead>
                      <tbody className="bg-white">
                        {((previewData.preview?.preview || previewData.rows || previewData.preview) || []).slice(previewPage * rowsPerPage, (previewPage + 1) * rowsPerPage).map((row, rowIdx) => (
                          <tr key={rowIdx} className="border-t border-gray-100 hover:bg-purple-50/30">
                            {((previewData.preview?.columns || previewData.columns) || []).slice(0, 10).map((col, colIdx) => {
                              const colName = typeof col === 'string' ? col : col.name;
                              return (
                                <td key={colIdx} className="px-3 py-2 text-gray-700 whitespace-nowrap">
                                  {row[colName] !== null && row[colName] !== undefined
                                    ? String(row[colName])
                                    : <span className="text-gray-400 italic">null</span>}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {(previewData.preview?.row_count || previewData.row_count || 0) > rowsPerPage && (
                    <div className="flex items-center justify-between mt-3">
                      <p className="text-xs text-gray-500">
                        Showing {previewPage * rowsPerPage + 1} - {Math.min((previewPage + 1) * rowsPerPage, (previewData.preview?.row_count || previewData.row_count))} of {previewData.preview?.row_count || previewData.row_count} rows
                      </p>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setPreviewPage(Math.max(0, previewPage - 1))}
                          disabled={previewPage === 0}
                          className="px-3 py-1 rounded border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                          <ChevronLeft className="w-4 h-4" />
                          Previous
                        </button>
                        <span className="text-xs text-gray-600">
                          Page {previewPage + 1} of {Math.ceil((previewData.preview?.row_count || previewData.row_count) / rowsPerPage)}
                        </span>
                        <button
                          onClick={() => setPreviewPage(Math.min(Math.ceil((previewData.preview?.row_count || previewData.row_count) / rowsPerPage) - 1, previewPage + 1))}
                          disabled={previewPage >= Math.ceil((previewData.preview?.row_count || previewData.row_count) / rowsPerPage) - 1}
                          className="px-3 py-1 rounded border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                          Next
                          <ChevronRightIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 text-sm font-semibold hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleImportFromPreview}
                disabled={isUploading}
                className="px-6 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold shadow-lg hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50"
              >
                {isUploading ? 'Importing...' : 'Confirm and Import'}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

function InfoCard({ icon: Icon, title, value, subtitle }) {
  return (
    <div className="rounded-xl border border-purple-100 bg-gradient-to-br from-white to-purple-50/60 p-4 shadow-[0_10px_24px_rgba(88,55,160,0.10)]">
      <div className="w-9 h-9 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center mb-3">
        <Icon className="w-4.5 h-4.5" />
      </div>
      <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      <p className="text-xl font-bold text-purple-700 mt-1">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
}
