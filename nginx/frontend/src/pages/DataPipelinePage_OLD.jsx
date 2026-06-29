import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, unstructuredAPI, uploadAPI, patientsAPI } from '../services/api';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Zap,
  TrendingUp,
  Eye,
  Brain,
  Bot,
  Check,
  ChevronRight,
  X,
  Trash2,
  Info,
  BarChart3,
  Settings,
  Save,
  RotateCcw,
  Loader2,
  FileCheck,
  FileSpreadsheet,
  Image as ImageIcon
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function DataPipelinePage() {
  const navigate = useNavigate();
  const [currentStage, setCurrentStage] = useState(1); // 1: Upload, 2: Validate, 3: Preprocess, 4: Preview & Edit
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [preprocessingConfig, setPreprocessingConfig] = useState({});
  const [tableData, setTableData] = useState(null);
  const [previewData, setPreviewData] = useState(null); // Store preview before saving to DB
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [validationId, setValidationId] = useState(null);
  const [error, setError] = useState(null);
  const [importConfig, setImportConfig] = useState({
    diseaseName: 'Systemic Lupus Erythematosus',
    datasetType: 'SLE',
    diseaseCode: 'M32.1',
    autoApprove: false
  });
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) handleFile(file);
  };

  const handleFile = async (file) => {
    setUploadedFile(file);
    setIsProcessing(true);
    setError(null);
    
    // Determine file type
    const ext = file.name.split('.').pop().toLowerCase();
    const isUnstructured = ['pdf', 'txt', 'png', 'jpg', 'jpeg'].includes(ext);
    const isStructured = ['csv', 'xlsx', 'xls'].includes(ext);
    
    try {
      if (isUnstructured) {
        // REAL API CALL: Unstructured pipeline
        const result = await unstructuredAPI.upload(file);
        
        // Set validation ID for later use
        setValidationId(result.validation_id);
        
        // Create validation results from OCR response
        const mockValidation = {
          fileName: result.filename,
          fileSize: (file.size / (1024 * 1024)).toFixed(2),
          fileType: 'unstructured',
          recordCount: result.medical_entities?.length || 0,
          columnCount: 0,
          issues: [],
          qualityScore: (result.confidence * 100).toFixed(1),
          ocrData: {
            extractedText: result.extracted_text,
            medicalEntities: result.medical_entities,
            pageCount: result.page_count,
            processingTime: result.processing_time
          }
        };
        
        setValidationResults(mockValidation);
        setIsProcessing(false);
        setCurrentStage(2);
        
      } else if (isStructured) {
        // REAL API CALL: Structured data import
        // For now, we'll do a basic validation and let user configure import
        const mockValidation = {
          fileName: file.name,
          fileSize: (file.size / (1024 * 1024)).toFixed(2),
          fileType: 'structured',
          recordCount: 0, // Will be known after import
          columnCount: 0,
          issues: [],
          qualityScore: 0,
          needsConfig: true // Flag to show import configuration
        };
        
        setValidationResults(mockValidation);
        setIsProcessing(false);
        setCurrentStage(2);
      }
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || err.message || 'Upload failed. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleApplyPreprocessing = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      if (validationResults.fileType === 'unstructured' && validationId) {
        // REAL API CALL: Get preview for unstructured data
        const preview = await unstructuredAPI.getPreview(validationId);
        
        // Transform preview data to table format
        const mockData = {
          columns: ['entity_type', 'entity_text', 'confidence', 'context'],
          rows: (preview.data?.medical_entities || []).map(entity => ({
            entity_type: entity.type || 'Unknown',
            entity_text: entity.text || '',
            confidence: (entity.confidence * 100).toFixed(1) + '%',
            context: entity.context || ''
          }))
        };
        
        setTableData(mockData);
        setIsProcessing(false);
        setCurrentStage(4);
        
      } else if (validationResults.fileType === 'structured') {
        // NEW WORKFLOW: Preview data WITHOUT saving to database
        // This allows researcher to review and edit BEFORE import
        const preview = await uploadAPI.previewFile(uploadedFile, importConfig);
        
        // Store preview data for later import
        setPreviewData(preview);
        
        // Transform to editable table format
        const tableColumns = preview.columns.map(col => col.name);
        const tableRows = preview.rows;
        
        setTableData({
          columns: tableColumns,
          rows: tableRows,
          total: preview.row_count,
          isPreview: true, // Flag to show this is preview, not saved data
          currentPage: 0,
          pageSize: 20,
          mappingSummary: preview.mapping_summary,
          metadata: preview.metadata
        });
        
        setIsProcessing(false);
        setCurrentStage(4);
      }
      
    } catch (err) {
      console.error('Preprocessing error:', err);
      setError(err.response?.data?.detail || err.message || 'Preprocessing failed. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleSaveDataset = async () => {
    if (validationResults.fileType === 'unstructured' && validationId) {
      try {
        // REAL API CALL: Approve unstructured data
        await unstructuredAPI.approve(validationId);
        alert('✅ Dataset approved and saved to PostgreSQL!');
        navigate('/dashboard');
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to save dataset');
      }
    } else if (validationResults.fileType === 'structured' && previewData) {
      // NEW WORKFLOW: Import edited preview data to database
      // This is where duplicate checking happens
      try {
        setIsProcessing(true);
        
        // Prepare edited data with tableData that may have been edited
        const editedData = {
          rows: tableData.rows,
          columns: previewData.columns,
          metadata: {
            ...previewData.metadata,
            auto_approve: importConfig.autoApprove
          }
        };
        
        // Import to database with duplicate checking
        const result = await uploadAPI.importFromPreview(editedData);
        
        // Extract statistics from response
        const stats = result.statistics || {};
        
        // Count actual errors (not duplicates)
        const duplicateCount = (result.errors || []).filter(err => 
          err.includes('duplicate key') || err.includes('UniqueViolation')
        ).length;
        const realErrors = (result.errors || []).filter(err => 
          !err.includes('duplicate key') && !err.includes('UniqueViolation')
        );
        
        // Show summary - duplicates are warnings, not errors
        let message = `✅ Data saved to PostgreSQL!\n\n`;
        message += `Patients: ${stats.patients_imported || 0} imported\n`;
        message += `Diagnoses: ${stats.diagnoses_imported || 0} imported\n`;
        message += `Disease data: ${stats.disease_data_imported || 0} imported\n`;
        if (duplicateCount > 0) {
          message += `\n⚠️  ${duplicateCount} duplicate records skipped (already in database)`;
        }
        if (realErrors.length > 0) {
          message += `\n❌ ${realErrors.length} errors encountered`;
        }
        
        alert(message);
        setIsProcessing(false);
        navigate('/dashboard');
        
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to save dataset');
        setIsProcessing(false);
      }
    } else {
      // Structured data already imported (old workflow fallback)
      alert('✅ Dataset saved successfully!');
      navigate('/dashboard');
    }
  };

  const handleReject = async () => {
    if (validationId) {
      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) return; // User cancelled
      
      try {
        await unstructuredAPI.reject(validationId, reason);
        alert('🔄 Data rejected. Please upload a new file.');
        handleReset(); // Reset to upload stage
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to reject data');
      }
    }
  };

  const handleReset = () => {
    setCurrentStage(1);
    setUploadedFile(null);
    setValidationResults(null);
    setValidationId(null);
    setError(null);
    setPreprocessingConfig({});
    setTableData(null);
    setPreviewData(null); // Clear preview data
    setImportConfig({
      diseaseName: 'Systemic Lupus Erythematosus',
      datasetType: 'SLE',
      diseaseCode: 'M32.1',
      autoApprove: false
    });
  };

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col bg-gray-bg">
        {/* Header with Stepper */}
        <div className="px-6 py-5 bg-white/70 backdrop-blur-sm border-b border-white/30">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="font-syne text-xl font-bold text-black-text">Data Pipeline</h1>
                <p className="text-sm text-gray-muted mt-1">Ingest, validate, and prepare clinical datasets</p>
              </div>
              {currentStage > 1 && (
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/40 hover:border-purple-primary/40 hover:bg-purple-dim text-sm font-medium text-gray-muted hover:text-purple-primary transition-all"
                >
                  <RotateCcw className="w-4 h-4" />
                  Start Over
                </button>
              )}
            </div>
            
            {/* Stepper */}
            <StepperProgress currentStage={currentStage} />
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            {/* Error Alert */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-red-900">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-400 hover:text-red-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            
            {currentStage === 1 && (
              <UploadStage 
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onFileSelect={() => fileInputRef.current?.click()}
                isProcessing={isProcessing}
              />
            )}
            
            {currentStage === 2 && validationResults && (
              <ValidationStage 
                results={validationResults}
                isProcessing={isProcessing}
                onNext={() => setCurrentStage(3)}
                importConfig={importConfig}
                setImportConfig={setImportConfig}
              />
            )}
            
            {currentStage === 3 && (
              <PreprocessingStage 
                config={preprocessingConfig}
                setConfig={setPreprocessingConfig}
                issues={validationResults?.issues || []}
                isProcessing={isProcessing}
                onApply={handleApplyPreprocessing}
                onSkip={() => setCurrentStage(4)}
              />
            )}
            
            {currentStage === 4 && tableData && (
              <PreviewEditStage 
                data={tableData}
                setData={setTableData}
                onSave={handleSaveDataset}
              />
            )}
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.pdf,.txt,.png,.jpg,.jpeg,.json"
          onChange={handleFileUpload}
          className="hidden"
        />

        {/* Assistant Panel (collapsed by default) */}
        {assistantOpen && (
          <AssistantPanel onClose={() => setAssistantOpen(false)} />
        )}
      </div>
    </DashboardLayout>
  );
}

// Stepper Component
function StepperProgress({ currentStage }) {
  const steps = [
    { number: 1, label: 'Upload', icon: Upload },
    { number: 2, label: 'Validate', icon: FileCheck },
    { number: 3, label: 'Preprocess', icon: Settings },
    { number: 4, label: 'Preview & Edit', icon: Eye }
  ];

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isActive = currentStage === step.number;
        const isCompleted = currentStage > step.number;
        const isUpcoming = currentStage < step.number;

        return (
          <div key={step.number} className="flex items-center flex-1">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                  isCompleted
                    ? 'bg-purple-primary text-white shadow-md'
                    : isActive
                    ? 'bg-purple-dim border-2 border-purple-primary text-purple-primary'
                    : 'bg-white/60 border border-white/40 text-gray-muted'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" strokeWidth={2.5} />
                ) : (
                  <Icon className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className={`text-sm font-medium ${isActive ? 'text-purple-primary' : isCompleted ? 'text-black-text' : 'text-gray-muted'}`}>
                  {step.label}
                </div>
                <div className="text-xs text-gray-muted">Step {step.number}</div>
              </div>
            </div>
            
            {index < steps.length - 1 && (
              <div className="flex-1 h-0.5 mx-4 bg-white/40">
                <div
                  className={`h-full transition-all duration-500 ${
                    isCompleted ? 'bg-purple-primary' : 'bg-transparent'
                  }`}
                  style={{ width: isCompleted ? '100%' : '0%' }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Stage 1: Upload
function UploadStage({ onDrop, onDragOver, onFileSelect, isProcessing }) {
  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        className="relative bg-white/70 backdrop-blur-sm rounded-[28px] border-2 border-dashed border-purple-primary/30 hover:border-purple-primary/60 transition-all p-16 text-center cursor-pointer group"
        onClick={onFileSelect}
      >
        {isProcessing ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-purple-primary animate-spin" />
            <p className="text-base font-medium text-black-text">Processing your file...</p>
            <p className="text-sm text-gray-muted">Validating structure and quality</p>
          </div>
        ) : (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-purple-dim flex items-center justify-center group-hover:scale-110 transition-transform">
              <Upload className="w-10 h-10 text-purple-primary" />
            </div>
            <h3 className="font-syne text-xl font-bold text-black-text mb-2">
              Upload Your Dataset
            </h3>
            <p className="text-sm text-gray-muted mb-6 max-w-md mx-auto">
              Drag and drop your file here, or click to browse. We support CSV, XLSX, PDF, TXT, images, and JSON.
            </p>
            <div className="flex items-center justify-center gap-6 text-xs text-gray-muted">
              <div className="flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-purple-primary" />
                <span>CSV, XLSX</span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-purple-primary" />
                <span>PDF, TXT</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ImageIcon className="w-4 h-4 text-purple-primary" />
                <span>PNG, JPG</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-card rounded-xl p-5 border border-white/40">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-dim flex items-center justify-center flex-shrink-0">
              <FileSpreadsheet className="w-4 h-4 text-purple-primary" />
            </div>
            <div>
              <h4 className="font-medium text-sm text-black-text mb-1">Structured Data</h4>
              <p className="text-xs text-gray-muted leading-relaxed">
                CSV/XLSX files go straight to validation and preview
              </p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-xl p-5 border border-white/40">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-dim flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-purple-primary" />
            </div>
            <div>
              <h4 className="font-medium text-sm text-black-text mb-1">Unstructured Data</h4>
              <p className="text-xs text-gray-muted leading-relaxed">
                PDF/images processed through OCR pipeline before preview
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stage 2: Validation
function ValidationStage({ results, isProcessing, onNext, importConfig, setImportConfig }) {
  const isUnstructured = results.fileType === 'unstructured';
  const needsConfig = results.needsConfig === true;
  const hasIssues = results.issues && results.issues.length > 0;

  return (
    <div className="space-y-6">
      {/* File Info Card */}
      <div className="bg-white/70 backdrop-blur-sm rounded-[28px] border border-white/40 p-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="font-syne text-xl font-bold text-black-text mb-1">
              {isUnstructured ? 'OCR Extraction Complete' : needsConfig ? 'Import Configuration' : 'Validation Complete'}
            </h2>
            <p className="text-sm text-gray-muted">
              {results.fileName} {results.fileSize && `(${results.fileSize} MB)`}
            </p>
          </div>
          {!needsConfig && (
            <div className="px-4 py-2 rounded-lg bg-purple-dim border border-purple-primary/20">
              <div className="text-xs text-gray-muted mb-0.5">
                {isUnstructured ? 'Confidence' : 'Quality Score'}
              </div>
              <div className="text-2xl font-bold text-purple-primary">{results.qualityScore}%</div>
            </div>
          )}
        </div>

        {/* Import Configuration Form for Structured Data */}
        {needsConfig && importConfig && setImportConfig && (
          <div className="space-y-4">
            <p className="text-sm text-gray-muted mb-4">
              Configure import settings for this dataset
            </p>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-black-text mb-2">
                  Disease Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={importConfig.diseaseName}
                  onChange={(e) => setImportConfig({...importConfig, diseaseName: e.target.value})}
                  className="w-full px-4 py-2 rounded-lg border border-white/40 bg-white/60 focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 transition-all"
                  placeholder="e.g., Systemic Lupus Erythematosus"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-black-text mb-2">
                  Dataset Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={importConfig.datasetType}
                  onChange={(e) => setImportConfig({...importConfig, datasetType: e.target.value})}
                  className="w-full px-4 py-2 rounded-lg border border-white/40 bg-white/60 focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 transition-all"
                >
                  <option value="SLE">SLE (Lupus)</option>
                  <option value="SJOGREN">Sjögren's Syndrome</option>
                  <option value="RA">Rheumatoid Arthritis</option>
                  <option value="MIXED">Mixed CTD</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-black-text mb-2">
                  Disease Code (ICD-10)
                </label>
                <input
                  type="text"
                  value={importConfig.diseaseCode}
                  onChange={(e) => setImportConfig({...importConfig, diseaseCode: e.target.value})}
                  className="w-full px-4 py-2 rounded-lg border border-white/40 bg-white/60 focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20 transition-all"
                  placeholder="e.g., M32.1"
                />
              </div>
              
              <div className="flex items-center justify-between p-4 bg-card rounded-lg border border-white/40">
                <div>
                  <div className="text-sm font-medium text-black-text">Auto-approve new tests</div>
                  <div className="text-xs text-gray-muted mt-1">Skip manual review for new test definitions</div>
                </div>
                <input
                  type="checkbox"
                  checked={importConfig.autoApprove}
                  onChange={(e) => setImportConfig({...importConfig, autoApprove: e.target.checked})}
                  className="w-5 h-5 rounded border-gray-300 text-purple-primary focus:ring-purple-primary/20"
                />
              </div>
            </div>
          </div>
        )}

        {/* Unstructured Data (OCR) Preview */}
        {isUnstructured && results.ocrData && (
          <div className="space-y-4">
            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Pages</div>
                <div className="text-2xl font-bold text-black-text">{results.ocrData.pageCount || 1}</div>
              </div>
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Medical Entities</div>
                <div className="text-2xl font-bold text-black-text">
                  {results.ocrData.medicalEntities?.length || 0}
                </div>
              </div>
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Extracted Text</div>
                <div className="text-2xl font-bold text-black-text">
                  {results.ocrData.extractedText?.length || 0} chars
                </div>
              </div>
            </div>

            {/* Extracted Text Preview */}
            {results.ocrData.extractedText && (
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <h4 className="text-sm font-semibold text-black-text mb-2 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-purple-primary" />
                  Extracted Text Preview
                </h4>
                <div className="text-xs text-gray-muted leading-relaxed max-h-40 overflow-y-auto font-mono bg-white/60 p-3 rounded-lg">
                  {results.ocrData.extractedText.substring(0, 500)}
                  {results.ocrData.extractedText.length > 500 && '...'}
                </div>
              </div>
            )}

            {/* Medical Entities */}
            {results.ocrData.medicalEntities && results.ocrData.medicalEntities.length > 0 && (
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <h4 className="text-sm font-semibold text-black-text mb-3 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-purple-primary" />
                  Medical Entities Found
                </h4>
                <div className="flex flex-wrap gap-2">
                  {results.ocrData.medicalEntities.slice(0, 10).map((entity, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 bg-purple-dim text-purple-primary text-xs font-medium rounded-full border border-purple-primary/20"
                    >
                      {entity.text || entity}
                    </span>
                  ))}
                  {results.ocrData.medicalEntities.length > 10 && (
                    <span className="px-3 py-1.5 bg-gray-100 text-gray-muted text-xs font-medium rounded-full">
                      +{results.ocrData.medicalEntities.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Structured Data Stats */}
        {!isUnstructured && (
          <>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Records</div>
                <div className="text-2xl font-bold text-black-text">
                  {results.recordCount?.toLocaleString() || 0}
                </div>
              </div>
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Columns</div>
                <div className="text-2xl font-bold text-black-text">{results.columnCount || 0}</div>
              </div>
              <div className="bg-card rounded-xl p-4 border border-white/40">
                <div className="text-xs text-gray-muted mb-1">Issues Found</div>
                <div className="text-2xl font-bold text-black-text">{results.issues?.length || 0}</div>
              </div>
            </div>

            {/* Issues List */}
            {hasIssues && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-black-text flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                  Data Quality Issues Detected
                </h3>
                {results.issues.map((issue, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 bg-amber-50/80 rounded-lg border border-amber-200/60"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-black-text">
                          <code className="px-2 py-0.5 rounded bg-white/60 text-purple-primary font-mono text-xs">
                            {issue.column}
                          </code>
                        </div>
                        <div className="text-xs text-gray-muted mt-0.5">
                          {issue.type === 'missing'
                            ? `${issue.percentage}% missing values (${issue.count} records)`
                            : `${issue.count} outliers detected (${issue.method})`}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-amber-600 font-medium">
                      {issue.type === 'missing' ? 'Missing Data' : 'Outliers'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Action Button */}
      <div className="flex justify-end">
        <button
          onClick={onNext}
          disabled={needsConfig && !importConfig?.diseaseName}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-black-cta text-white hover:shadow-[0_6px_24px_rgba(0,0,0,0.22)] transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUnstructured 
            ? 'View Full Preview' 
            : needsConfig 
              ? 'Import Dataset' 
              : hasIssues 
                ? 'Configure Preprocessing' 
                : 'Continue to Preview'}
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Stage 3: Preprocessing
function PreprocessingStage({ config, setConfig, issues, isProcessing, onApply, onSkip }) {
  const updateColumnConfig = (column, field, value) => {
    setConfig(prev => ({
      ...prev,
      [column]: { ...prev[column], [field]: value }
    }));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white/70 backdrop-blur-sm rounded-[28px] border border-white/40 p-8">
        <h2 className="font-syne text-xl font-bold text-black-text mb-2">
          Configure Preprocessing
        </h2>
        <p className="text-sm text-gray-muted mb-6">
          Choose how to handle issues in each flagged column. Your choices will be applied before the next step.
        </p>

        {/* Column Cards */}
        <div className="space-y-4">
          {issues.map((issue, idx) => (
            <ColumnPreprocessingCard
              key={idx}
              issue={issue}
              config={config[issue.column]}
              onUpdate={(field, value) => updateColumnConfig(issue.column, field, value)}
            />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button
          onClick={onSkip}
          className="px-5 py-2.5 rounded-lg border border-white/40 hover:border-purple-primary/40 hover:bg-purple-dim text-sm font-medium text-gray-muted hover:text-purple-primary transition-all"
        >
          Skip Preprocessing
        </button>
        <button
          onClick={onApply}
          disabled={isProcessing}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-black-cta text-white hover:shadow-[0_6px_24px_rgba(0,0,0,0.22)] transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Applying...
            </>
          ) : (
            <>
              Apply Preprocessing
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

function ColumnPreprocessingCard({ issue, config, onUpdate }) {
  return (
    <div className="bg-card rounded-xl p-5 border border-white/40">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-dim flex items-center justify-center">
            <AlertCircle className="w-4 h-4 text-purple-primary" />
          </div>
          <div>
            <code className="text-sm font-mono font-medium text-purple-primary bg-purple-dim px-2 py-1 rounded">
              {issue.column}
            </code>
            <div className="text-xs text-gray-muted mt-1">
              {issue.type === 'missing'
                ? `${issue.percentage}% missing (${issue.count} records)`
                : `${issue.count} outliers (${issue.method})`}
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Options */}
      <div className="grid grid-cols-2 gap-3">
        {issue.type === 'missing' && (
          <div>
            <label className="text-xs font-medium text-gray-muted mb-2 block">
              Imputation Strategy
            </label>
            <select
              value={config?.imputation || 'median'}
              onChange={(e) => onUpdate('imputation', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-white/40 bg-input-bg text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
            >
              <option value="median">Median (numeric)</option>
              <option value="mean">Mean (numeric)</option>
              <option value="mode">Mode (categorical)</option>
              <option value="drop">Drop rows</option>
            </select>
          </div>
        )}
        
        {issue.type === 'outlier' && (
          <div>
            <label className="text-xs font-medium text-gray-muted mb-2 block">
              Outlier Handling
            </label>
            <select
              value={config?.outlierHandling || 'flag'}
              onChange={(e) => onUpdate('outlierHandling', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-white/40 bg-input-bg text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
            >
              <option value="flag">Flag only</option>
              <option value="cap">Cap at IQR bounds</option>
              <option value="drop">Drop outliers</option>
              <option value="none">Keep as-is</option>
            </select>
          </div>
        )}

        <div>
          <label className="text-xs font-medium text-gray-muted mb-2 block">
            Scaling
          </label>
          <select
            value={config?.scaling || 'none'}
            onChange={(e) => onUpdate('scaling', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-white/40 bg-input-bg text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
          >
            <option value="none">None</option>
            <option value="minmax">Min-Max (0-1)</option>
            <option value="standard">Z-score</option>
          </select>
        </div>
      </div>
    </div>
  );
}

// Stage 4: Preview & Edit
function PreviewEditStage({ data, setData, onSave }) {
  const [editedCells, setEditedCells] = useState({});

  const handleCellEdit = (rowIndex, column, value) => {
    const newData = { ...data };
    newData.rows[rowIndex][column] = value;
    setData(newData);
    
    setEditedCells(prev => ({
      ...prev,
      [`${rowIndex}-${column}`]: true
    }));
  };

  const handleDeleteRow = (rowIndex) => {
    const newData = { ...data };
    newData.rows.splice(rowIndex, 1);
    setData(newData);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white/70 backdrop-blur-sm rounded-[28px] border border-white/40 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="font-syne text-xl font-bold text-black-text mb-1">
              Preview & Edit
            </h2>
            <p className="text-sm text-gray-muted">
              Review the processed data. Click any cell to edit, or delete unwanted rows.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="px-3 py-1.5 rounded-lg bg-purple-dim text-purple-primary font-medium">
              {data.rows.length} rows
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-purple-dim text-purple-primary font-medium">
              {data.columns.length} columns
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-white/40">
          <table className="w-full text-sm">
            <thead className="bg-gray-bg border-b border-white/40">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-muted uppercase tracking-wider w-12">
                  #
                </th>
                {data.columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-muted uppercase tracking-wider"
                  >
                    <div className="flex items-center gap-1.5">
                      {col}
                      {['ana_titer', 'crp_level'].includes(col) && (
                        <AlertCircle className="w-3 h-3 text-amber-500" title="Had missing values" />
                      )}
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3 w-12"></th>
              </tr>
            </thead>
            <tbody className="bg-white">
              {data.rows.slice(0, 15).map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="border-b border-white/20 hover:bg-purple-dim/30 transition-colors group"
                >
                  <td className="px-4 py-2.5 text-xs text-gray-muted font-medium">
                    {rowIndex + 1}
                  </td>
                  {data.columns.map((col) => {
                    const isEdited = editedCells[`${rowIndex}-${col}`];
                    const isNull = row[col] === null;
                    const isOutlier = col === 'esr_rate' && parseFloat(row[col]) > 60;
                    
                    return (
                      <td key={col} className="px-4 py-2.5">
                        <input
                          type="text"
                          value={row[col] ?? ''}
                          onChange={(e) => handleCellEdit(rowIndex, col, e.target.value)}
                          className={`w-full px-2 py-1 rounded border bg-transparent text-xs focus:outline-none focus:ring-1 focus:ring-purple-primary transition-all ${
                            isEdited
                              ? 'border-green-400 bg-green-50'
                              : isNull
                              ? 'border-amber-300 bg-amber-50/50 italic text-gray-muted'
                              : isOutlier
                              ? ' border-amber-400 bg-amber-50/80 text-amber-700 font-medium'
                              : 'border-transparent hover:border-white/40'
                          }`}
                          placeholder={isNull ? '(imputed)' : ''}
                        />
                      </td>
                    );
                  })}
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => handleDeleteRow(rowIndex)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 hover:text-red-600 transition-all"
                      title="Delete row"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data.rows.length > 15 && (
          <div className="mt-3 text-center text-xs text-gray-muted">
            Showing first 15 of {data.rows.length} rows
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded border border-amber-300 bg-amber-50/50"></div>
          <span className="text-gray-muted">Imputed values</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded border border-amber-400 bg-amber-50/80"></div>
          <span className="text-gray-muted">Flagged outliers</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded border border-green-400 bg-green-50"></div>
          <span className="text-gray-muted">Edited cells</span>
        </div>
      </div>

      {/* Action */}
      <div className="flex justify-end">
        <button
          onClick={onSave}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-black-cta text-white hover:shadow-[0_6px_24px_rgba(0,0,0,0.22)] transition-all font-medium"
        >
          <Save className="w-4 h-4" />
          Save Data
        </button>
      </div>
    </div>
  );
}

// Assistant Panel (Optional - for contextual help)
function AssistantPanel({ onClose }) {
  return (
    <div className="fixed right-0 top-0 h-screen w-96 bg-white/95 backdrop-blur-md border-l border-white/40 shadow-2xl p-6 flex flex-col animate-slideIn">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-purple-dim flex items-center justify-center">
            <Bot className="w-5 h-5 text-purple-primary" />
          </div>
          <div>
            <h3 className="font-medium text-black-text">Assistant</h3>
            <p className="text-xs text-gray-muted">Ask me anything</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-purple-dim transition-colors"
        >
          <X className="w-4 h-4 text-gray-muted" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="text-sm text-gray-muted">
          <p className="mb-3">I can help you with:</p>
          <ul className="space-y-2 text-xs">
            <li>• Explaining preprocessing strategies</li>
            <li>• Understanding outlier detection methods</li>
            <li>• Recommending imputation approaches</li>
            <li>• Interpreting quality scores</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
