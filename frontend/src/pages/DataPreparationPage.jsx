import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as Tooltip from '@radix-ui/react-tooltip';
import {
  Database,
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Tag,
  BarChart3,
  TrendingUp,
  Users,
  Activity,
  Play,
  RefreshCw,
  Download,
  Eye,
  Edit,
  Search,
  Filter,
  Zap,
  Shield,
  Target,
  Settings,
  ArrowLeft,
  Save,
  Lock,
  X,
  HelpCircle,
  Sparkles
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import RuleBasedLabelingWorkflow from '../components/RuleBasedLabelingWorkflow';
import { mlAPI, flexibleAPI, labelingAPI } from '../services/api';

// ─── Inflammatory & Immunological Feature Engineering Catalogue ──────────────
// Each entry encodes the formula, required source columns, disease scope,
// evidence base, and the reasoning why linear models cannot discover it alone.
const FEATURE_CATALOG = {
  crpEsrRatio: {
    label: 'CRP/ESR Ratio',
    formula: 'CRP ÷ ESR',
    requires: ['CRP', 'ESR'],
    evidenceTag: 'Acute-vs-chronic discriminator',
    scope: 'SLE · RA · AS · Sjögren\'s · IBD · Vasculitis',
    scopeNote:
      'Not reliable in scleroderma (characteristically low CRP despite active fibrosis) or multiple sclerosis (CNS inflammation does not consistently raise peripheral markers).',
    rationale:
      'ESR rises slowly and reflects chronic background inflammation. CRP rises fast and captures acute responses. The ratio encodes whether a patient is experiencing an acute flare on top of chronic disease — information that exists in neither value alone.',
    modelNote:
      'Linear and logistic regression models only capture additive relationships. They cannot derive CRP÷ESR from raw columns; the feature must be provided explicitly.',
  },
  nlrRatio: {
    label: 'NLR (Neutrophil-Lymphocyte Ratio)',
    formula: 'Neutrophils ÷ Lymphocytes',
    requires: ['Neutrophils', 'Lymphocytes'],
    evidenceTag: 'Validated in >50 clinical studies',
    scope: 'Universal — autoimmune and oncology',
    scopeNote:
      'Validated across SLE, RA, AS, IBD, Sjögren\'s, and Vasculitis. Also a prognostic marker in colorectal, lung, gastric, and ovarian cancer. The most broadly applicable single ratio in this catalogue.',
    rationale:
      'In SLE and RA, immune dysregulation consistently shifts this ratio. It is a validated predictor of disease activity, hospitalisation risk, and mortality across multiple autoimmune cohorts. Universally available from a full blood count.',
    modelNote:
      'LASSO and logistic regression need this ratio supplied explicitly. Providing raw neutrophil and lymphocyte counts and expecting the model to divide them requires exponentially more data than simply engineering the feature.',
  },
  plrRatio: {
    label: 'PLR (Platelet-Lymphocyte Ratio)',
    formula: 'Platelets ÷ Lymphocytes',
    requires: ['Platelets', 'Lymphocytes'],
    evidenceTag: 'Validated disease-severity surrogate',
    scope: 'Universal — autoimmune and oncology',
    scopeNote:
      'Validated across most systemic inflammatory conditions and as a cancer prognostic marker. Evidence in multiple sclerosis is limited due to infrequent peripheral platelet dysregulation in CNS-predominant disease.',
    rationale:
      'Platelets rise during systemic inflammation; lymphocytes drop in active autoimmune disease. The ratio is a validated low-cost surrogate for disease severity when a formal scoring index (e.g., SLEDAI) is unavailable.',
    modelNote:
      'The cross-lineage relationship (thrombocyte count versus lymphocyte count) is invisible to models that see each column independently.',
  },
  sii: {
    label: 'SII (Systemic Immune-Inflammation Index)',
    formula: 'Platelets × Neutrophils ÷ Lymphocytes',
    requires: ['Platelets', 'Neutrophils', 'Lymphocytes'],
    evidenceTag: 'Cross-disease meta-analysis validated',
    scope: 'Universal — autoimmune and oncology',
    scopeNote:
      'Meta-analysis validated across SLE, RA, IBD, AS, and six cancer types (colorectal, lung, gastric, ovarian, hepatocellular, cervical). The most universally applicable single derived index in this catalogue.',
    rationale:
      'SII integrates three immune lineages — platelet-mediated coagulation, neutrophil-driven innate immunity, and lymphocyte-driven adaptive immunity — into a single value that captures systemic immune dysregulation more completely than NLR or PLR alone. It is particularly useful when a researcher wants a single composite marker for cross-disease or cancer-adjacent studies.',
    modelNote:
      'The three-way multiplicative relationship is invisible to any linear model without explicit engineering. It also reduces the dimensionality cost of supplying Platelets, Neutrophils, and Lymphocytes as separate columns to a LASSO model.',
  },
  diseaseDuration: {
    label: 'Disease Duration (Years)',
    formula: 'Current Date − Diagnosis Date',
    requires: ['DiagnosisDate (or equivalent)'],
    evidenceTag: 'Fundamental clinical risk factor',
    scope: 'Universal — all chronic diseases',
    scopeNote:
      'Applicable to any chronic condition with a definable diagnosis date, including autoimmune diseases, cancer, and chronic inflammatory conditions.',
    rationale:
      'A patient diagnosed 15 years ago carries fundamentally different accumulated organ damage, medication exposure, and tolerance patterns than one diagnosed last year. A raw calendar date is a high-cardinality nominal value; converted to duration it becomes a meaningful continuous predictor.',
    modelNote:
      'Raw dates cannot be used as-is in ML. Converting to years-since-diagnosis transforms a nominal timestamp into an informative continuous variable.',
  },
  inflammationScore: {
    label: 'Inflammation Index',
    formula: 'Mean(CRP, ESR)',
    requires: ['CRP', 'ESR'],
    evidenceTag: 'Reduces multicollinearity',
    scope: 'SLE · RA · AS · IBD · Vasculitis',
    scopeNote:
      'Applies wherever both CRP and ESR are routinely measured. Less informative in scleroderma or MS where one or both markers are unreliable indicators of disease activity.',
    rationale:
      'CRP and ESR are correlated (r > 0.6 in most cohorts). Feeding both raw values to a linear model inflates variance and destabilises coefficient estimates. A combined index reduces this multicollinearity while preserving the inflammatory signal for feature selection.',
    modelNote:
      'LASSO shrinkage is biased by correlated predictors — one of the pair is arbitrarily zeroed. A combined index gives LASSO a single stable handle on the inflammatory signal.',
  },
  organInvolvement: {
    label: 'Organ Involvement Count',
    formula: 'Sum of binary organ-system flags',
    requires: ['Joint_involvement', 'Kidney_involvement', 'Skin_involvement', '...'],
    evidenceTag: 'Mirrors SLEDAI scoring methodology',
    scope: 'SLE · MCTD · Vasculitis · multi-system diseases',
    scopeNote:
      'Optimised for multi-system diseases using SLEDAI-aligned organ flags. For ankylosing spondylitis, IBD, or MS, organ flag definitions differ; this feature is still applicable but column selection must align with the disease-specific activity index.',
    rationale:
      'Individual organ flags are sparse binary columns that each contribute little signal. Their sum is a direct disease-severity ordinal that aligns with how clinicians calculate SLEDAI scores — the count of affected organ systems is a cornerstone of every validated multi-system autoimmune activity index.',
    modelNote:
      'Sparse individual binary flags contribute weak signal. Their sum creates a high-signal ordinal severity variable that is far more informative per feature slot.',
  },
};
// ──────────────────────────────────────────────────────────────────────────────

// Label type configurations for different prediction tasks
const LABEL_TYPES = {
  'labels_disease_classification': {
    name: 'Disease Classification',
    description: 'For multi-disease datasets (RA vs SLE vs Mixed)',
    categories: [
      { value: 'SLE', label: 'Systemic Lupus Erythematosus (SLE)' },
      { value: 'Sjogren', label: 'Sjögren\'s Syndrome' },
      { value: 'RA', label: 'Rheumatoid Arthritis (RA)' },
      { value: 'MCTD', label: 'Mixed Connective Tissue Disease' },
      { value: 'Healthy', label: 'Healthy Control' },
      { value: 'Unknown', label: 'Unknown/Undifferentiated' }
    ]
  },
  'labels_disease_severity': {
    name: 'Disease Severity',
    description: 'For single-disease datasets - predict severity levels',
    categories: [
      { value: 'Mild', label: 'Mild (SLEDAI ≤4 or minimal symptoms)' },
      { value: 'Moderate', label: 'Moderate (SLEDAI 5-12 or moderate symptoms)' },
      { value: 'Severe', label: 'Severe (SLEDAI >12 or severe/organ-threatening)' }
    ]
  },
  'labels_disease_activity': {
    name: 'Disease Activity',
    description: 'Current disease activity status',
    categories: [
      { value: 'Remission', label: 'Remission (No active disease)' },
      { value: 'Active', label: 'Active (Ongoing disease activity)' },
      { value: 'Flare', label: 'Flare (Acute exacerbation)' }
    ]
  },
  'labels_organ_involvement': {
    name: 'Organ Involvement',
    description: 'Primary organ system affected',
    categories: [
      { value: 'Renal', label: 'Renal (Lupus nephritis)' },
      { value: 'Neuropsychiatric', label: 'Neuropsychiatric (CNS involvement)' },
      { value: 'Hematologic', label: 'Hematologic (Blood disorders)' },
      { value: 'Musculoskeletal', label: 'Musculoskeletal (Joint involvement)' },
      { value: 'Cutaneous', label: 'Cutaneous (Skin involvement only)' },
      { value: 'Non-organ-specific', label: 'Non-organ-specific' }
    ]
  },
  'labels_treatment_response': {
    name: 'Treatment Response',
    description: 'Response to current treatment',
    categories: [
      { value: 'Complete-responder', label: 'Complete Responder (Full response)' },
      { value: 'Partial-responder', label: 'Partial Responder (Partial response)' },
      { value: 'Non-responder', label: 'Non-responder (No response)' }
    ]
  },
  'labels_flare_risk': {
    name: 'Flare Risk',
    description: 'Risk of disease flare',
    categories: [
      { value: 'Low-risk', label: 'Low Risk (Stable, good control)' },
      { value: 'High-risk', label: 'High Risk (Unstable, multiple risk factors)' }
    ]
  }
};

export default function DataPreparationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Check if we're coming from DataPipelinePage with session data
  const sessionData = location.state || null;
  const fromPreprocessing = sessionData?.fromPreprocessing || false;
  const fromDataCatalog = sessionData?.fromDataCatalog || false;
  const preselectedBatch = sessionData?.preselectedBatch || null;
  const startTab = sessionData?.startTab || null;
  
  // View mode: 'queue' (shows dataset list) or 'workflow' (shows 6-tab workflow)
  const [viewMode, setViewMode] = useState(fromPreprocessing || fromDataCatalog ? 'workflow' : 'queue');
  
  // Filter state for queue view
  const [queueFilter, setQueueFilter] = useState('all'); // 'all', 'ready', 'processing', 'complete'
  const [searchQuery, setSearchQuery] = useState(''); // Search filter
  
  // If coming from preprocessing, start at target selection tab
  // If coming from data catalog with startTab, use that
  // If coming from data catalog without startTab, start at upload tab
  const initialTab = startTab || (fromPreprocessing ? 'target' : 'upload');
  
  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedBatch, setSelectedBatch] = useState(preselectedBatch || null);
  const [labelingStats, setLabelingStats] = useState(null);
  const [validationResults, setValidationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Batches state - loaded from API
  const [batches, setBatches] = useState([]);
  const [batchesLoading, setBatchesLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState(null); // Track current user ID for permissions
  
  // Target selection state
  const [targetColumn, setTargetColumn] = useState('labels_disease_classification');
  const [trainTestSplit, setTrainTestSplit] = useState(0.35); // 65/35 split matching research framework
  const [stratifyEnabled, setStratifyEnabled] = useState(true);
  const [targetDistribution, setTargetDistribution] = useState(null);
  const [availableColumns, setAvailableColumns] = useState([]);
  
  // Cross-validation configuration
  const [useCrossValidation, setUseCrossValidation] = useState(false);
  const [cvFolds, setCvFolds] = useState(5); // Default 5-fold CV
  
  // Label type selection (what to predict)
  const [labelType, setLabelType] = useState('labels_disease_classification');
  const currentLabelConfig = LABEL_TYPES[labelType];
  
  // Labeling interface state
  const [unlabeledRecords, setUnlabeledRecords] = useState([]);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [selectedLabel, setSelectedLabel] = useState('');
  const [labelingInProgress, setLabelingInProgress] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [recordsPerPage] = useState(20);
  
  // Preprocessing state (Tab 4 - matches research methodology)
  const [preprocessingResults, setPreprocessingResults] = useState(null);
  const [preprocessingStep, setPreprocessingStep] = useState(null); // 'filtration', 'imputation', 'winsorization', 'standardization', 'complete'
  const [filtrationThreshold, setFiltrationThreshold] = useState(0.5); // Remove variables with >50% missing
  const [imputationStrategy, setImputationStrategy] = useState('median'); // 'median', 'mode', 'mean'
  const [winsorLower, setWinsorLower] = useState(0.01); // 1st percentile
  const [winsorUpper, setWinsorUpper] = useState(0.99); // 99th percentile
  const [standardizationMethod, setStandardizationMethod] = useState('standard'); // 'standard' (Z-score), 'minmax', 'robust'
  const [preprocessingInProgress, setPreprocessingInProgress] = useState(false);
  const [filtrationReport, setFiltrationReport] = useState(null);
  const [imputationReport, setImputationReport] = useState(null);
  const [winsorizeReport, setWinsorizeReport] = useState(null);
  const [standardizationReport, setStandardizationReport] = useState(null);

  // Feature engineering state
  const [featureEngineeringConfig, setFeatureEngineeringConfig] = useState({
    enableRatios: true,
    crpEsrRatio: true,
    nlrRatio: true,
    plrRatio: true,
    siiIndex: false,         // off by default — requires Platelets + Neutrophils + Lymphocytes
    enableTemporal: true,
    diseaseDuration: true,
    enableDerived: true,
    inflammationScore: true,
    organInvolvement: false
  });
  const [featureEngineeringResults, setFeatureEngineeringResults] = useState(null);
  const [expandedFeature, setExpandedFeature] = useState(null); // key of FEATURE_CATALOG currently expanded
  const [showFeatureRationale, setShowFeatureRationale] = useState(false); // "Why Feature Engineering?" panel
  const [selectedFeatures, setSelectedFeatures] = useState([]);
  const [scalingMethod, setScalingMethod] = useState('standard');
  const [featureConfig, setFeatureConfig] = useState({
    removeHighCorr: false,
    logTransform: false,
    polynomialFeatures: false,
    interactionTerms: false
  });
  
  // Feature Selection state
  const [availableFeatures, setAvailableFeatures] = useState([]); // All features (clinical + derived)
  const [clinicianSelectedFeatures, setClinicianSelectedFeatures] = useState([]); // Manual selection
  const [correlationThreshold, setCorrelationThreshold] = useState(0.85); // Correlation detection threshold
  const [lassoFeatures, setLassoFeatures] = useState([]); // LASSO-selected features
  const [finalFeatures, setFinalFeatures] = useState([]); // Final combined selection
  const [featureSelectionMode, setFeatureSelectionMode] = useState('manual'); // 'manual', 'lasso', 'combined'
  const [lassoAlpha, setLassoAlpha] = useState(0.00001); // LASSO regularization strength (very low for small datasets)
  const [featureImportance, setFeatureImportance] = useState(null); // Feature importance scores

  // Sync targetColumn with labelType (auto-select based on labeling choice)
  useEffect(() => {
    setTargetColumn(labelType);
  }, [labelType]);

  // Fetch batches on component mount
  useEffect(() => {
    // If coming from preprocessing with session data, auto-select it
    if (fromPreprocessing && sessionData) {
      setSelectedBatch({
        id: sessionData.sessionId,
        name: sessionData.datasetName || 'Preprocessed Dataset',
        uploadedAt: new Date().toLocaleString(),
        totalRecords: sessionData.rowCount || 0,
        labeledRecords: 0,
        features: 0,
        status: 'from_preprocessing',
        owner: 'Current User'
      });
      setBatchesLoading(false);
      return; // Skip fetching batches list
    }

    // If coming from Data Catalog with preselected batch, auto-select it
    if (fromDataCatalog && preselectedBatch) {
      setSelectedBatch(preselectedBatch);
      // Still fetch batches for context, but don't change selection
    }
    
    const fetchBatches = async () => {
      setBatchesLoading(true);
      try {
        // Fetch recent uploads with metadata and ownership info
        // Include both staging (just uploaded) and saved files
        const response = await flexibleAPI.getRecentUploads(50, true, true);
        
        // Store current user ID for permission checks
        if (response.current_user_id) {
          setCurrentUserId(response.current_user_id);
        }
        
        // Transform API response to match expected batch format
        const transformedBatches = response.uploads.map(upload => {
          // Determine labeled records count
          const labeledCount = upload.labeled_count || upload.labelled_count || 0;
          const totalRecords = upload.row_count || 0;
          
          // Determine status based on multiple conditions
          let status = 'ready'; // Default
          
          // Check if dataset has been labeled (indicates ML prep complete)
          if (labeledCount > 0 || upload.ml_prep_status === 'complete' || upload.status === 'from_preprocessing') {
            status = 'ml_prep_complete';
          } else if (upload.ml_prep_status === 'processing' || upload.ml_prep_status === 'in_progress') {
            status = 'in_progress';
          } else if (upload.ml_prep_status === 'ready' || upload.status === 'saved') {
            status = 'ready';
          }
          
          return {
            id: upload.id, // This is the import_batch_id
            name: upload.file_name,
            uploadedAt: new Date(upload.uploaded_at).toLocaleString(),
            totalRecords: totalRecords,
            labeledRecords: labeledCount,
            features: upload.feature_count || upload.column_count || 0,
            status: status,
            owner: upload.uploaded_by,
            ownerId: upload.uploaded_by_id,
            isOwner: upload.is_owner, // Permission flag from API
            fileType: upload.file_type,
            size: upload.size,
            source: upload.source || 'Upload',
            datasetType: upload.dataset_type || 'General'
          };
        });

        setBatches(transformedBatches);
        
        // Debug: Log status distribution
        const statusCounts = transformedBatches.reduce((acc, batch) => {
          acc[batch.status] = (acc[batch.status] || 0) + 1;
          return acc;
        }, {});
        console.log('Loaded datasets:', transformedBatches.length, 'total');
        console.log('Status distribution:', statusCounts);
        console.log('Datasets with labels:', transformedBatches.filter(b => b.labeledRecords > 0).length);
      } catch (error) {
        console.error('Failed to load datasets:', error);
        setBatches([]);
      } finally {
        setBatchesLoading(false);
      }
    };

    fetchBatches();
  }, []);

  // Fetch labeling statistics
  const fetchLabelingStats = async (batchId, targetCol = null) => {
    setLoading(true);
    try {
      const columnToUse = targetCol || labelType;
      console.log('[Labeling] Fetching stats for batch:', batchId, 'targetColumn:', columnToUse);
      const stats = await labelingAPI.getLabelStatistics(null, batchId, columnToUse);
      
      console.log('[Labeling] Stats received:', stats);
      
      setLabelingStats({
        total_records: stats.total_records || 0,
        labeled_records: stats.labeled_count || 0,
        unlabeled_records: stats.unlabeled_count || 0,
        labels: stats.label_distribution || {},
        labeling_progress: stats.progress_percentage || 0,
        confidence_distribution: {
          'High (>80%)': 0,  // Backend doesn't track confidence yet
          'Medium (60-80%)': 0,
          'Low (<60%)': 0
        }
      });
    } catch (error) {
      console.error('[Labeling] Failed to fetch stats:', error);
      console.error('[Labeling] Error details:', error.response?.data);
      // Set empty state on error
      setLabelingStats({
        total_records: 0,
        labeled_records: 0,
        unlabeled_records: 0,
        labels: {},
        labeling_progress: 0,
        confidence_distribution: {
          'High (>80%)': 0,
          'Medium (60-80%)': 0,
          'Low (<60%)': 0
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Run validation
  const runValidation = async (batchId) => {
    setLoading(true);
    try {
      const validation = await mlAPI.validateDataset(batchId, labelType);
      
      // Transform API response to match UI format
      const allChecks = [
        ...(validation.info || []).map(c => ({ ...c, status: 'passed' })),
        ...(validation.warnings || []).map(c => ({ ...c, status: c.severity === 'error' ? 'error' : 'warning' })),
        ...(validation.errors || []).map(c => ({ ...c, status: 'error' }))
      ];
      
      const transformedValidation = {
        status: validation.valid ? (validation.warnings?.length > 0 ? 'warning' : 'passed') : 'error',
        total_checks: allChecks.length,
        passed: (validation.info || []).length,
        warnings: (validation.warnings || []).filter(w => w.severity !== 'error').length,
        errors: (validation.errors || []).length + (validation.warnings || []).filter(w => w.severity === 'error').length,
        checks: allChecks.map(check => ({
          name: check.check || check.name || 'Unknown Check',
          status: check.status,
          message: check.message,
          severity: check.severity || 'info'
        })),
        recommendations: validation.recommendations || [],
        is_valid: validation.valid,
        summary: validation.summary
      };
      
      setValidationResults(transformedValidation);
      
      if (transformedValidation.errors > 0) {
        alert(`Validation completed with ${transformedValidation.errors} error(s). Please review the results.`);
      } else if (transformedValidation.warnings > 0) {
        alert(`Validation completed with ${transformedValidation.warnings} warning(s).`);
      } else {
        alert('✓ All validation checks passed! Dataset is ready for training.');
      }
    } catch (error) {
      console.error('Failed to run validation:', error);
      alert(`Validation failed: ${error.message || 'Unknown error'}`);
      setValidationResults(null);
    } finally {
      setLoading(false);
    }
  };

  // Fetch unlabeled records for labeling interface
  const fetchUnlabeledRecords = async (batchId) => {
    setLoading(true);
    try {
      console.log('[Labeling] Fetching unlabeled records for batch:', batchId);
      const response = await labelingAPI.getUnlabeledRecords(null, batchId, 100, 0, labelType);
      
      console.log('[Labeling] Unlabeled records response:', response);
      console.log('[Labeling] Number of unlabeled records:', response.unlabeled_records?.length || 0);
      
      // DEBUG: Show actual data structure of first record
      if (response.unlabeled_records && response.unlabeled_records.length > 0) {
        const firstRecord = response.unlabeled_records[0];
        console.log('[Labeling] ═══════════════════════════════════════════════════════');
        console.log('[Labeling] FIRST RECORD SAMPLE:');
        console.log('[Labeling] Record ID:', firstRecord.record_id);
        console.log('[Labeling] Dataset:', firstRecord.dataset_name);
        console.log('[Labeling] ═══════════════════════════════════════════════════════');
        console.log('[Labeling] AVAILABLE DATA FIELDS:', Object.keys(firstRecord.data || {}));
        console.log('[Labeling] ═══════════════════════════════════════════════════════');
        console.log('[Labeling] FULL RECORD DATA:');
        console.table(firstRecord.data || {});
        console.log('[Labeling] ═══════════════════════════════════════════════════════');
        console.log('[Labeling] 💡 TIP: Copy one of the field names above to use as "Source Column" for auto-labeling');
        console.log('[Labeling] Example: If you see "SLEDAI" in the fields, use that for severity labeling');
        console.log('[Labeling] ═══════════════════════════════════════════════════════');
      }
      
      setUnlabeledRecords(response.unlabeled_records || []);
      setSelectedRecords([]); // Clear selection
    } catch (error) {
      console.error('[Labeling] Failed to fetch unlabeled records:', error);
      console.error('[Labeling] Error details:', error.response?.data);
      setUnlabeledRecords([]);
    } finally {
      setLoading(false);
    }
  };

  // Assign label to individual record
  const assignIndividualLabel = async (recordId, label) => {
    setLabelingInProgress(true);
    try {
      await labelingAPI.assignLabel(recordId, label, 1.0, null, labelType);
      
      // Refresh unlabeled records and statistics
      await fetchUnlabeledRecords(selectedBatch.id);
      await fetchLabelingStats(selectedBatch.id);
      
      alert(`✓ Label "${label}" assigned successfully!`);
    } catch (error) {
      console.error('Failed to assign label:', error);
      alert(`Failed to assign label: ${error.message || 'Unknown error'}`);
    } finally {
      setLabelingInProgress(false);
    }
  };

  // Bulk assign labels to selected records
  const bulkAssignLabels = async () => {
    if (selectedRecords.length === 0) {
      alert('Please select at least one record');
      return;
    }
    if (!selectedLabel) {
      alert('Please select a label');
      return;
    }

    setLabelingInProgress(true);
    try {
      await labelingAPI.bulkAssignLabels(selectedRecords, selectedLabel, 1.0, null, labelType);
      
      // Refresh unlabeled records and statistics
      await fetchUnlabeledRecords(selectedBatch.id);
      await fetchLabelingStats(selectedBatch.id);
      
      alert(`✓ Successfully labeled ${selectedRecords.length} records as "${selectedLabel}"!`);
      setSelectedRecords([]);
      setSelectedLabel('');
    } catch (error) {
      console.error('Failed to bulk assign labels:', error);
      alert(`Failed to assign labels: ${error.message || 'Unknown error'}`);
    } finally {
      setLabelingInProgress(false);
    }
  };

  // Auto-label based on existing data (e.g., SLEDAI scores)
  const autoLabelRecords = async () => {
    // Determine source column and strategy based on label type
    let sourceColumn = 'SLEDAI';
    let labelTypeStrategy = 'severity';
    
    if (labelType === 'labels_disease_severity') {
      sourceColumn = 'SLEDAI';
      labelTypeStrategy = 'severity';
    } else if (labelType === 'labels_disease_activity') {
      sourceColumn = 'SLEDAI';
      labelTypeStrategy = 'activity';
    } else if (labelType === 'labels_organ_involvement') {
      sourceColumn = 'Urinary protein';
      labelTypeStrategy = 'kidney';
    }
    
    const confirmed = window.confirm(
      `Auto-Label All Records?\n\n` +
      `This will automatically assign ${currentLabelConfig.name} labels based on existing ${sourceColumn} data in your dataset.\n\n` +
      `Strategy: ${labelTypeStrategy}\n` +
      `Source: ${sourceColumn} column\n\n` +
      `Records without ${sourceColumn} data will be skipped.\n\n` +
      `Click OK to proceed.`
    );
    
    if (!confirmed) return;
    
    setLabelingInProgress(true);
    try {
      // Use the API method instead of raw fetch
      const result = await labelingAPI.autoLabel(
        selectedBatch.id,
        sourceColumn,
        labelType,
        labelTypeStrategy
      );
      
      // Refresh data
      await fetchUnlabeledRecords(selectedBatch.id);
      await fetchLabelingStats(selectedBatch.id);
      
      alert(
        `Auto-Labeling Complete!\n\n` +
        `Total records: ${result.total_records}\n` +
        `Labeled: ${result.labeled_count}\n` +
        `Skipped (no ${sourceColumn}): ${result.skipped_count}\n` +
        `Errors: ${result.error_count}`
      );
    } catch (error) {
      console.error('Auto-labeling failed:', error);
      
      // Show detailed error message
      let errorMessage = error.message || 'Unknown error';
      
      // Check if error is about column not found
      if (errorMessage.includes('Not Found') || errorMessage.includes('not found') || errorMessage.includes('Available fields')) {
        errorMessage = (
          `Auto-labeling failed: Not Found\n\n` +
          `Make sure your data has '${sourceColumn}' field with valid values.\n\n` +
          `Tips:\n` +
          `1. Check if your Excel column is named exactly "${sourceColumn}"\n` +
          `2. Verify the column has non-empty values\n` +
          `3. Column names are case-sensitive\n` +
          `4. Or use manual labeling with the bulk select feature`
        );
      } else {
        errorMessage = `Auto-labeling failed: ${errorMessage}\n\nMake sure your data has '${sourceColumn}' field with valid values.`;
      }
      
      alert(errorMessage);
    } finally {
      setLabelingInProgress(false);
    }
  };

  // Toggle record selection
  const toggleRecordSelection = (recordId) => {
    setSelectedRecords(prev =>
      prev.includes(recordId)
        ? prev.filter(id => id !== recordId)
        : [...prev, recordId]
    );
  };

  // Select all records on current page
  const selectAllOnPage = () => {
    const start = currentPage * recordsPerPage;
    const end = start + recordsPerPage;
    const pageRecords = unlabeledRecords.slice(start, end);
    const pageRecordIds = pageRecords.map(r => r.record_id);
    
    const allSelected = pageRecordIds.every(id => selectedRecords.includes(id));
    
    if (allSelected) {
      setSelectedRecords(prev => prev.filter(id => !pageRecordIds.includes(id)));
    } else {
      setSelectedRecords(prev => [...new Set([...prev, ...pageRecordIds])]);
    }
  };

  useEffect(() => {
    if (selectedBatch) {
      fetchLabelingStats(selectedBatch.id);
      // Fetch unlabeled records if on labeling tab
      if (activeTab === 'labeling') {
        fetchUnlabeledRecords(selectedBatch.id);
      }
    }
  }, [selectedBatch, activeTab]);

  const statusConfig = {
    ready: { bg: 'bg-green-dim', text: 'text-green', border: 'border-green/20', label: 'Ready for Training' },
    in_progress: { bg: 'bg-amber-dim', text: 'text-amber', border: 'border-amber/20', label: 'In Progress' },
    pending_labels: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', label: 'Pending Labels' },
    staging: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200', label: 'Staging' },
    uploaded: { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200', label: 'Uploaded' },
    default: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200', label: 'Unknown' }
  };

  const labelingProgress = labelingStats 
    ? labelingStats.labeling_progress
    : (selectedBatch && selectedBatch.totalRecords > 0
      ? (((selectedBatch.labeledRecords || 0) / selectedBatch.totalRecords) * 100).toFixed(1)
      : 0);
  
  const isReadyForTraining = selectedBatch && 
    validationResults && 
    validationResults.errors === 0 && 
    parseFloat(labelingProgress) >= 80 &&
    targetColumn &&
    featureEngineeringResults !== null;
  
  // Check tab completion status
  const isUploadComplete = selectedBatch !== null;
  const isLabelingComplete = labelingStats && labelingStats.labeling_progress >= 80;
  const isTargetComplete = targetColumn !== null; // Removed targetDistribution requirement
  const isPreprocessingComplete = preprocessingStep === 'complete'; // All 4 steps done
  const isFeaturesComplete = featureEngineeringResults !== null;
  const isValidationComplete = validationResults && validationResults.errors === 0;
  
  // Save configuration
  const saveConfiguration = async () => {
    // If in preprocessing flow, persist the session to the database
    if (fromPreprocessing && sessionData?.sessionId) {
      try {
        setLoading(true);
        const result = await flexibleAPI.saveToDatabase(
          sessionData.sessionId,
          sessionData.datasetName || 'ML Prepared Dataset'
        );
        sessionStorage.setItem('current_batch_id', result.batch_id);
        sessionStorage.setItem('current_target_column', labelType);
        alert('Draft saved. Your preprocessed dataset is now available in Training Jobs.');
      } catch (error) {
        // If already saved, that's fine — just inform the user
        if (error?.response?.status === 409 || error?.message?.includes('already')) {
          alert('This dataset was already saved. It is available in Training Jobs.');
        } else {
          alert(`Failed to save draft: ${error.message}`);
        }
      } finally {
        setLoading(false);
      }
    } else {
      // Non-preprocessing flow: config is held locally, no backend save needed
      alert('Configuration saved locally. Click "Proceed to Training" to start training.');
    }
  };
  
  // Handle "Proceed to Training" - save to database if from preprocessing
  const handleProceedToTraining = async () => {
    if (!selectedBatch) return;
    
    try {
      // If coming from preprocessing, save to database first
      if (fromPreprocessing && sessionData?.sessionId) {
        setLoading(true);
        
        const result = await flexibleAPI.saveToDatabase(
          sessionData.sessionId,
          sessionData.datasetName || 'ML Prepared Dataset'
        );
        
        console.log('Dataset saved:', result);
        
        // Save to sessionStorage for TrainingJobsPage to pick up
        sessionStorage.setItem('current_batch_id', result.batch_id);
        sessionStorage.setItem('current_target_column', labelType);
        
        // Navigate to training with the new batch_id
        navigate('/training', {
          state: {
            dataset_id: result.batch_id,
            target_column: labelType,
            selected_features: selectedFeatures,
            train_test_split: trainTestSplit,
            stratify: stratifyEnabled,
            scaling_method: scalingMethod,
            feature_config: featureConfig,
            feature_engineering_config: featureEngineeringConfig,
            feature_engineering_results: featureEngineeringResults
          }
        });
      } else {
        // Normal flow - dataset already in database
        // Save to sessionStorage for TrainingJobsPage to pick up
        sessionStorage.setItem('current_batch_id', selectedBatch.id);
        sessionStorage.setItem('current_target_column', labelType);
        
        navigate('/training', {
          state: {
            dataset_id: selectedBatch.id,
            target_column: labelType,
            selected_features: selectedFeatures,
            train_test_split: trainTestSplit,
            stratify: stratifyEnabled,
            scaling_method: scalingMethod,
            feature_config: featureConfig,
            feature_engineering_config: featureEngineeringConfig,
            feature_engineering_results: featureEngineeringResults
          }
        });
      }
    } catch (error) {
      console.error('Failed to proceed to training:', error);
      alert(`Failed to proceed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Apply feature engineering
  const applyFeatureEngineering = async () => {
    if (!selectedBatch) {
      alert('Please select a batch first');
      return;
    }

    setLoading(true);
    try {
      console.log('[Feature Engineering] Starting for batch:', selectedBatch.id);
      console.log('[Feature Engineering] Config:', featureEngineeringConfig);
      console.log('[Feature Engineering] Target column:', labelType);
      
      // Call feature engineering API with target column from labelType
      const response = await mlAPI.engineerFeatures(
        selectedBatch.id,
        {
          ...featureEngineeringConfig,
          targetColumn: labelType  // Use the label type selected in labeling tab
        }
      );

      console.log('[Feature Engineering] Response:', response);

      if (response.success) {
        setFeatureEngineeringResults(response);
        
        // Auto-select all successfully created features
        const newFeatureNames = response.new_features.map(f => f.name);
        setSelectedFeatures(newFeatureNames);

        const message = `✓ Feature Engineering Completed!\n\n` +
          `Original Features: ${response.original_feature_count}\n` +
          `New Features: ${response.features_added}\n` +
          `Total Features: ${response.engineered_feature_count}\n\n` +
          `Created Features:\n${response.new_features.map(f => `  • ${f.name} (${f.type})`).join('\n')}`;
        
        if (response.skipped_features && response.skipped_features.length > 0) {
          console.warn('[Feature Engineering] Skipped features:', response.skipped_features);
        }

        alert(message);
      } else {
        throw new Error(response.message || 'Feature engineering failed');
      }

    } catch (error) {
      console.error('[Feature Engineering] Error:', error);
      alert(`Feature Engineering Failed:\n${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch target distribution
  const fetchTargetDistribution = async () => {
    if (!selectedBatch?.id || !targetColumn) return;
    
    try {
      const result = await mlAPI.getTargetDistribution(selectedBatch.id, labelType);
      setTargetDistribution(result.distribution);
    } catch (error) {
      console.error('Failed to fetch target distribution:', error);
      setTargetDistribution({});
    }
  };
  
  // Fetch available columns when batch is selected
  const fetchAvailableColumns = async () => {
    if (!selectedBatch?.id) return;
    
    try {
      const columns = await mlAPI.getAvailableColumns(selectedBatch.id);
      setAvailableColumns(columns);
      
      // Set default target column if not already set
      if (!targetColumn && columns.length > 0) {
        setTargetColumn(columns[0]);
      }
    } catch (error) {
      console.error('Failed to fetch available columns:', error);
      // Fallback to defaults
      setAvailableColumns(['labels_disease_classification', 'labels_disease_severity']);
    }
  };
  
  // Fetch target distribution when batch or target column changes
  useEffect(() => {
    if (selectedBatch && targetColumn) {
      fetchTargetDistribution();
    }
  }, [selectedBatch?.id, targetColumn]);
  
  // Fetch available columns when batch is selected
  useEffect(() => {
    if (selectedBatch) {
      fetchAvailableColumns();
    }
  }, [selectedBatch?.id]);
  
  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
        // Advance to next tab if current tab is complete
        if (activeTab === 'upload' && isUploadComplete) setActiveTab('labeling');
        else if (activeTab === 'labeling' && isLabelingComplete) setActiveTab('target');
        else if (activeTab === 'target' && isTargetComplete) setActiveTab('preprocessing');
        else if (activeTab === 'preprocessing' && isPreprocessingComplete) setActiveTab('features');
        else if (activeTab === 'features' && isFeaturesComplete) setActiveTab('feature-selection');
        else if (activeTab === 'feature-selection' && finalFeatures.length > 0) setActiveTab('validation');
        else if (activeTab === 'validation' && isValidationComplete) setActiveTab('summary');
      }
    };
    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [activeTab, isUploadComplete, isLabelingComplete, isTargetComplete, isPreprocessingComplete, isFeaturesComplete, isValidationComplete]);

  // Handle selecting a dataset from queue
  const handleSelectDataset = (batch) => {
    setSelectedBatch(batch);
    setViewMode('workflow');
    setActiveTab('labeling'); // Start from labeling tab
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)', zoom: 0.75 }}>
        
        {/* QUEUE VIEW: Show dataset list with ML prep status */}
        {viewMode === 'queue' && (
          <>
            {/* Header */}
            <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
              <div className="px-6 py-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                      <Target className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h1 className="font-syne text-2xl font-bold text-black-text">ML Preparation Queue</h1>
                      <p className="text-xs text-gray-muted">Select a dataset to continue ML preparation</p>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate('/data-preparation')}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-purple-primary text-purple-primary hover:bg-purple-50 transition-all"
                  >
                    <Upload className="w-4 h-4" />
                    Upload New Data
                  </button>
                </div>
              </div>
            </div>

            {/* Queue Content */}
            <div className="flex-1 px-6 pt-6">
              <div className="max-w-7xl mx-auto space-y-4">
                
                {/* Search Bar & Filter Tabs */}
                <div className="flex flex-col gap-4">
                  {/* Search Bar */}
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search datasets by name, type, or owner..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 bg-white/80 border border-white/60 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {/* Filter Tabs */}
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setQueueFilter('all')}
                      className={`px-3 py-1.5 rounded-md font-medium text-xs transition-all ${
                        queueFilter === 'all'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'bg-white/60 border border-white/60 text-gray-600 hover:bg-white'
                      }`}
                    >
                      All ({batches.length})
                    </button>
                    <button 
                      onClick={() => setQueueFilter('ready')}
                      className={`px-3 py-1.5 rounded-md font-medium text-xs transition-all ${
                        queueFilter === 'ready'
                          ? 'bg-green-600 text-white shadow-sm'
                          : 'bg-white/60 border border-white/60 text-gray-600 hover:bg-white'
                      }`}
                    >
                      Ready ({batches.filter(b => b.status === 'ready' || b.status === 'from_preprocessing').length})
                    </button>
                    <button 
                      onClick={() => setQueueFilter('processing')}
                      className={`px-3 py-1.5 rounded-md font-medium text-xs transition-all ${
                        queueFilter === 'processing'
                          ? 'bg-amber-600 text-white shadow-sm'
                          : 'bg-white/60 border border-white/60 text-gray-600 hover:bg-white'
                      }`}
                    >
                      Processing ({batches.filter(b => b.status === 'in_progress').length})
                    </button>
                    <button 
                      onClick={() => setQueueFilter('complete')}
                      className={`px-3 py-1.5 rounded-md font-medium text-xs transition-all ${
                        queueFilter === 'complete'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-white/60 border border-white/60 text-gray-600 hover:bg-white'
                      }`}
                    >
                      Complete ({batches.filter(b => b.status === 'ml_prep_complete').length})
                    </button>
                  </div>
                </div>

                {/* Dataset Table (S3/MinIO style) */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-lg overflow-hidden shadow-sm">
                  {batchesLoading ? (
                    <div className="text-center py-12">
                      <RefreshCw className="w-8 h-8 text-purple-primary animate-spin mx-auto mb-2" />
                      <p className="text-sm text-gray-600">Loading datasets...</p>
                    </div>
                  ) : batches.length === 0 ? (
                    <div className="text-center py-12">
                      <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-600 mb-4">No datasets yet. Upload data to get started.</p>
                      <button
                        onClick={() => navigate('/data-preparation')}
                        className="px-6 py-2 bg-purple-primary text-white rounded-lg hover:shadow-lg transition-all text-sm font-medium"
                      >
                        Upload Data
                      </button>
                    </div>
                  ) : (
                    (() => {
                      const filteredBatches = batches.filter(batch => {
                        // Filter by tab
                        const matchesFilter = 
                          queueFilter === 'all' ||
                          (queueFilter === 'ready' && (batch.status === 'ready' || batch.status === 'from_preprocessing')) ||
                          (queueFilter === 'processing' && batch.status === 'in_progress') ||
                          (queueFilter === 'complete' && (batch.status === 'ml_prep_complete' || batch.labeledRecords > 0));
                        
                        // Filter by search query
                        const matchesSearch = !searchQuery || 
                          batch.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          batch.owner?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          batch.datasetType?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          batch.fileType?.toLowerCase().includes(searchQuery.toLowerCase());
                        
                        return matchesFilter && matchesSearch;
                      });

                      if (filteredBatches.length === 0) {
                        return (
                          <div className="text-center py-12">
                            <Filter className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                            <p className="text-sm text-gray-600 mb-2">
                              {searchQuery ? 'No datasets match your search' : 'No datasets match this filter'}
                            </p>
                            <button
                              onClick={() => {
                                setQueueFilter('all');
                                setSearchQuery('');
                              }}
                              className="text-xs text-purple-primary hover:underline"
                            >
                              Clear filters
                            </button>
                          </div>
                        );
                      }

                      return (
                        <table className="w-full">
                          <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Dataset Name
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Type
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Records
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Owner
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Uploaded
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Status
                              </th>
                              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Actions
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {filteredBatches.map(batch => (
                              <motion.tr 
                                key={batch.id}
                                className={`hover:bg-purple-50/50 transition-colors cursor-pointer group ${
                                  !batch.isOwner ? 'bg-gray-50/50' : ''
                                }`}
                                onClick={() => handleSelectDataset(batch)}
                                whileHover={{ scale: 1.005, x: 2 }}
                                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                              >
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    {/* Lock icon for view-only datasets */}
                                    {!batch.isOwner && (
                                      <Lock className="w-4 h-4 text-gray-400 flex-shrink-0" title="View Only - Uploaded by another user" />
                                    )}
                                    <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
                                      batch.fileType?.includes('PDF') ? 'bg-red-100' :
                                      batch.fileType?.includes('Excel') || batch.fileType?.includes('CSV') ? 'bg-green-100' :
                                      'bg-purple-100'
                                    } ${!batch.isOwner ? 'opacity-75' : ''}`}>
                                      {batch.fileType?.includes('PDF') ? (
                                        <FileText className="w-4 h-4 text-red-600" />
                                      ) : batch.fileType?.includes('Image') ? (
                                        <Eye className="w-4 h-4 text-orange-600" />
                                      ) : (
                                        <Database className="w-4 h-4 text-purple-600" />
                                      )}
                                    </div>
                                    <div className="min-w-0">
                                      <div className={`font-medium text-sm truncate max-w-xs group-hover:text-purple-600 transition-colors ${
                                        !batch.isOwner ? 'text-gray-600' : 'text-gray-900'
                                      }`}>
                                        {batch.name}
                                      </div>
                                      <div className="flex items-center gap-2 mt-0.5">
                                        {batch.datasetType && (
                                          <span className="text-xs text-gray-500">{batch.datasetType}</span>
                                        )}
                                        {!batch.isOwner && (
                                          <span className="text-xs text-gray-500 flex items-center gap-1">
                                            <Shield className="w-3 h-3" />
                                            View Only
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                  <span className={`px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium ${
                                    !batch.isOwner ? 'opacity-75' : ''
                                  }`}>
                                    {batch.fileType || 'Unknown'}
                                  </span>
                                </td>
                                <td className={`px-4 py-3 text-sm font-medium ${
                                  !batch.isOwner ? 'text-gray-600' : 'text-gray-900'
                                }`}>
                                  {batch.totalRecords.toLocaleString()}
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm text-gray-600">{batch.owner || 'Unknown'}</span>
                                    {!batch.isOwner && (
                                      <span className="text-xs text-gray-500">(Other Team Member)</span>
                                    )}
                                  </div>
                                </td>
                                <td className={`px-4 py-3 text-xs ${
                                  !batch.isOwner ? 'text-gray-400' : 'text-gray-500'
                                }`}>
                                  {batch.uploadedAt}
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                      batch.status === 'ready' || batch.status === 'from_preprocessing'
                                        ? 'bg-green-100 text-green-700'
                                        : batch.status === 'in_progress'
                                        ? 'bg-amber-100 text-amber-700'
                                        : batch.status === 'ml_prep_complete'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'bg-gray-100 text-gray-700'
                                    }`}>
                                      {batch.status === 'from_preprocessing' ? 'Ready' : 
                                       batch.status === 'ready' ? 'Ready' :
                                       batch.status === 'ml_prep_complete' ? 'Complete' :
                                       batch.status === 'in_progress' ? 'Processing' : 'Pending'}
                                    </span>
                                    {!batch.isOwner && (
                                      <Lock className="w-3 h-3 text-gray-400" />
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <button 
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleSelectDataset(batch);
                                    }}
                                    className={`px-3 py-1.5 rounded text-xs font-medium hover:shadow-md transition-all opacity-0 group-hover:opacity-100 ${
                                      !batch.isOwner 
                                        ? 'bg-gray-500 text-white cursor-default' 
                                        : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                                    }`}
                                    title={!batch.isOwner ? 'View Only - Cannot edit' : 'Start ML Preparation'}
                                  >
                                    {!batch.isOwner ? (
                                      <span className="flex items-center gap-1">
                                        <Eye className="w-3 h-3" />
                                        View Only
                                      </span>
                                    ) : 'Start Prep →'}
                                  </button>
                                </td>
                              </motion.tr>
                            ))}
                          </tbody>
                        </table>
                      );
                    })()
                  )}
                </div>
                
                {/* Results Count */}
                {!batchesLoading && batches.length > 0 && (
                  <div className="text-xs text-gray-500 text-center">
                    Showing {batches.filter(b => {
                      const matchesFilter = 
                        queueFilter === 'all' ||
                        (queueFilter === 'ready' && (b.status === 'ready' || b.status === 'from_preprocessing')) ||
                        (queueFilter === 'processing' && b.status === 'in_progress') ||
                        (queueFilter === 'complete' && b.status === 'ml_prep_complete');
                      const matchesSearch = !searchQuery || 
                        b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        b.owner?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        b.datasetType?.toLowerCase().includes(searchQuery.toLowerCase());
                      return matchesFilter && matchesSearch;
                    }).length} of {batches.length} datasets
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* WORKFLOW VIEW: 6-Tab ML Preparation */}
        {viewMode === 'workflow' && (
          <>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setViewMode('queue')}
                  className="w-10 h-10 rounded-lg border-2 border-gray-300 flex items-center justify-center hover:bg-gray-50 transition-all"
                  title="Back to Queue"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-600" />
                </button>
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <Database className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h1 className="font-syne text-2xl font-bold text-black-text">ML Preparation</h1>
                    {fromPreprocessing && sessionData && (
                      <span className="px-3 py-1 text-xs font-mono bg-blue-100 text-blue-700 rounded-md border border-blue-200">
                        Preprocessed Session {sessionData.sessionId?.substring(0, 8)}...
                      </span>
                    )}
                    <button
                      onClick={() => alert(
                        'ML Preparation Workflow\n\n' +
                        'This workflow prepares your dataset for machine learning training:\n\n' +
                        '1. Upload: Import your dataset\n' +
                        '2. Labeling: Assign target labels to records (min 80% required)\n' +
                        '3. Target Selection: Choose what to predict\n' +
                        '4. Features: Configure feature engineering\n' +
                        '5. Validation: Check data quality for ML\n' +
                        '6. Summary: Review and proceed to training\n\n' +
                        'Note: Auto-labeling uses existing clinical data (SLEDAI, etc.) to automatically assign labels. Manual labeling is available for records without source data.'
                      )}
                      className="w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center hover:bg-gray-100 transition-all text-gray-600 hover:text-purple-600 hover:border-purple-600"
                      title="Help: Learn about ML Preparation workflow"
                    >
                      <HelpCircle className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-gray-muted">
                    {fromPreprocessing 
                      ? 'Continue with labeling, target selection, and feature engineering'
                      : selectedBatch?.name || 'Select dataset and prepare for ML training'
                    }
                  </p>
                </div>
              </div>
              {selectedBatch && (
                <div className="flex items-center gap-2">
                  {isReadyForTraining ? (
                    <button
                      onClick={() => navigate('/training')}
                      className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-green to-green/90 text-white hover:shadow-lg transition-all font-medium"
                    >
                      <Play className="w-5 h-5" />
                      Ready for Training
                    </button>
                  ) : (
                    <button
                      disabled
                      className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gray-300 text-gray-500 cursor-not-allowed font-medium"
                    >
                      <AlertCircle className="w-5 h-5" />
                      Complete Labeling First
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-2 border-b border-white/40">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'upload'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isUploadComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isUploadComplete ? '1' : '1'}
                  </span>
                  <Upload className="w-4 h-4" />
                  Upload
                </div>
              </button>
              <button
                onClick={() => setActiveTab('labeling')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'labeling'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isLabelingComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isLabelingComplete ? '2' : '2'}
                  </span>
                  <Tag className="w-4 h-4" />
                  Labeling
                  {selectedBatch && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-dim text-purple-primary text-xs font-bold">
                      {selectedBatch.labeledRecords}/{selectedBatch.totalRecords}
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('target')}
                disabled={!selectedBatch}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'target'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isTargetComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isTargetComplete ? '3' : '3'}
                  </span>
                  <Target className="w-4 h-4" />
                  Target Selection
                </div>
              </button>
              <button
                onClick={() => setActiveTab('preprocessing')}
                disabled={!selectedBatch || !targetColumn}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'preprocessing'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isPreprocessingComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isPreprocessingComplete ? '4' : '4'}
                  </span>
                  <Settings className="w-4 h-4" />
                  Preprocessing
                  {preprocessingStep && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-dim text-purple-primary text-xs font-bold">
                      {preprocessingStep === 'complete' ? '4/4' : `${['filtration', 'imputation', 'winsorization', 'standardization'].indexOf(preprocessingStep) + 1}/4`}
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('features')}
                disabled={!selectedBatch || !targetColumn}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'features'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isFeaturesComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isFeaturesComplete ? '5' : '5'}
                  </span>
                  <Zap className="w-4 h-4" />
                  Features
                  {featureEngineeringResults && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-dim text-purple-primary text-xs font-bold">
                      {featureEngineeringResults.features_created || 0} features
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('feature-selection')}
                disabled={!selectedBatch || !targetColumn}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'feature-selection'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    finalFeatures.length > 0 ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {finalFeatures.length > 0 ? '6' : '6'}
                  </span>
                  <Filter className="w-4 h-4" />
                  Feature Selection
                  {finalFeatures.length > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-dim text-purple-primary text-xs font-bold">
                      {finalFeatures.length} selected
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('validation')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'validation'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isValidationComplete ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isValidationComplete ? '7' : '7'}
                  </span>
                  <Shield className="w-4 h-4" />
                  Validation
                  {validationResults && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      validationResults.errors > 0
                        ? 'bg-red-50 text-red-600'
                        : validationResults.warnings > 0
                        ? 'bg-amber-dim text-amber'
                        : 'bg-green-dim text-green'
                    }`}>
                      {validationResults.passed}/{validationResults.total_checks}
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('summary')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'summary'
                    ? 'border-purple-primary text-purple-primary'
                    : 'border-transparent text-gray-muted hover:text-black-text'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isReadyForTraining ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isReadyForTraining ? '8' : '8'}
                  </span>
                  <BarChart3 className="w-4 h-4" />
                  Summary
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {/* TAB 1: Upload & Import */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                {/* Existing Batches */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                    <h3 className="font-syne text-base font-bold text-black-text">Existing Datasets</h3>
                  </div>
                  <div className="p-5 space-y-3">
                    {batches.map((batch) => {
                      const statusStyle = statusConfig[batch.status] || statusConfig.default;
                      const totalRecords = batch.totalRecords || 0;
                      const labeledRecords = batch.labeledRecords || 0;
                      const progress = totalRecords > 0 ? ((labeledRecords / totalRecords) * 100).toFixed(1) : '0.0';
                      
                      return (
                        <div
                          key={batch.id}
                          onClick={() => setSelectedBatch(batch)}
                          className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${
                            selectedBatch?.id === batch.id
                              ? 'border-purple-primary bg-purple-dim'
                              : 'border-white/40 bg-white/60 hover:border-purple-primary/40'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-sm text-black-text mb-1">{batch.name}</h4>
                              <div className="flex items-center gap-3 text-xs text-gray-muted">
                                <span>ID: {batch.id}</span>
                                <span>•</span>
                                <span>Uploaded: {batch.uploadedAt}</span>
                                <span>•</span>
                                <span>Owner: {batch.owner}</span>
                              </div>
                            </div>
                            <span className={`px-3 py-1 rounded-lg text-xs font-medium border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                              {statusStyle.label}
                            </span>
                          </div>

                          <div className="grid grid-cols-4 gap-3 mb-3">
                            <div className="bg-white/60 rounded-lg p-2">
                              <div className="text-[10px] text-gray-muted mb-0.5">Total Records</div>
                              <div className="font-bold text-sm text-black-text">{totalRecords}</div>
                            </div>
                            <div className="bg-white/60 rounded-lg p-2">
                              <div className="text-[10px] text-gray-muted mb-0.5">Labeled</div>
                              <div className="font-bold text-sm text-purple-primary">{labeledRecords}</div>
                            </div>
                            <div className="bg-white/60 rounded-lg p-2">
                              <div className="text-[10px] text-gray-muted mb-0.5">Features</div>
                              <div className="font-bold text-sm text-black-text">{batch.features || 0}</div>
                            </div>
                            <div className="bg-white/60 rounded-lg p-2">
                              <div className="text-[10px] text-gray-muted mb-0.5">Progress</div>
                              <div className="font-bold text-sm text-green">{progress}%</div>
                            </div>
                          </div>

                          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-primary to-purple-primary/80 rounded-full"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Smart Labeling */}
            {activeTab === 'labeling' && selectedBatch && (
              <RuleBasedLabelingWorkflow
                batchId={selectedBatch.id}
                targetColumn={labelType}
                onComplete={async (actualTargetColumn) => {
                  // Update labelType to match what was actually labeled
                  console.log('[DataPreparation] Labeling complete. Target column used:', actualTargetColumn);
                  if (actualTargetColumn && actualTargetColumn !== labelType) {
                    console.log('[DataPreparation] Updating labelType from', labelType, 'to', actualTargetColumn);
                    setLabelType(actualTargetColumn);
                    setTargetColumn(actualTargetColumn);
                  }
                  
                  // Refresh stats after successful labeling with correct target column
                  console.log('[DataPreparation] Refreshing statistics for batch:', selectedBatch.id, 'with targetColumn:', actualTargetColumn || labelType);
                  await fetchLabelingStats(selectedBatch.id, actualTargetColumn);
                  
                  // Update selectedBatch with new labeled count
                  const updatedStats = await labelingAPI.getLabelStatistics(null, selectedBatch.id, actualTargetColumn || labelType);
                  setSelectedBatch(prev => ({
                    ...prev,
                    labeledRecords: updatedStats.labeled_count || 0
                  }));
                  
                  console.log('[DataPreparation] Updated batch labeledRecords:', updatedStats.labeled_count);
                  // Note: Don't auto-advance to next tab - let user review results first
                }}
                onBack={() => setViewMode('queue')}
              />
            )}

            {/* TAB 3: Target Selection */}
            {activeTab === 'target' && selectedBatch && (
              <div className="space-y-6">
                {/* Info Banner */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
                    <Target className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-sm text-blue-900">Target Variable Selection</h4>
                      <div className="relative group">
                        <HelpCircle className="w-4 h-4 text-blue-400 hover:text-blue-600 cursor-help transition-colors" />
                        <div className="absolute left-0 top-6 w-80 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                          <div className="font-semibold mb-2">What this does:</div>
                          <div className="space-y-2">
                            <div>You're telling the ML model <strong>what to predict</strong>.</div>
                            <div>Based on your labeling in the previous tab, the target is automatically set to <strong>{LABEL_TYPES[labelType]?.name || labelType}</strong>.</div>
                            <div className="mt-2 pt-2 border-t border-gray-700">
                              The model will learn from other features to predict this automatically for new patients.
                            </div>
                          </div>
                          <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 p-2 bg-blue-100 rounded text-xs text-blue-800 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <div><strong>Your labels are ready!</strong> The model will predict: {LABEL_TYPES[labelType]?.description || 'target variable'}</div>
                    </div>
                  </div>
                </div>

                {/* Auto-Selected Target (Read-Only) */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <h3 className="font-syne text-lg font-bold text-black-text mb-4">Target Variable (Auto-Selected)</h3>
                  <p className="text-sm text-gray-muted mb-4">
                    This was automatically set based on the label type you selected and used in the Labeling tab.
                  </p>
                  
                  <div className="p-4 bg-purple-50 border-2 border-purple-300 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs text-purple-600 font-medium mb-1">Target Column</div>
                        <div className="text-lg font-bold text-purple-900">{labelType}</div>
                        <div className="text-xs text-purple-600 mt-1">{LABEL_TYPES[labelType]?.name}</div>
                      </div>
                      <CheckCircle className="w-8 h-8 text-purple-600" />
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-xs text-green-700">
                          <strong>Automatic & Correct:</strong> No need to select manually! 
                          The system automatically uses the label type you chose when labeling ({LABEL_TYPES[labelType]?.name}). 
                          This ensures consistency and prevents errors.
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Target Distribution Preview */}
                  {targetDistribution && Object.keys(targetDistribution).length > 0 ? (
                    <div className="mt-6">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-sm text-black-text">Class Distribution</h4>
                        <div className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">{Object.values(targetDistribution).reduce((a, b) => a + b, 0)} records labeled</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {Object.entries(targetDistribution)
                          .sort(([, a], [, b]) => b - a) // Sort by count descending
                          .map(([label, count]) => {
                            const total = Object.values(targetDistribution).reduce((a, b) => a + b, 0);
                            const percent = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                            return (
                              <div key={label}>
                                <div className="flex items-center justify-between text-sm mb-1">
                                  <span className="font-medium text-gray-700">{label}</span>
                                  <span className="text-gray-600">{count} patients ({percent}%)</span>
                                </div>
                                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-to-r from-purple-500 to-purple-600"
                                    style={{ width: `${percent}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                      </div>
                      
                      <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                        <p className="text-xs text-purple-700">
                          <strong>📊 What this means:</strong> Your labeled data shows {Object.keys(targetDistribution).length} different diagnoses. 
                          The ML model will learn to distinguish between these based on biomarker patterns.
                        </p>
                      </div>
                      
                      {/* Imbalance Warning */}
                      {(() => {
                        const counts = Object.values(targetDistribution);
                        if (counts.length === 0) return null;
                        const maxCount = Math.max(...counts);
                        const minCount = Math.min(...counts);
                        if (minCount === 0) return null;
                        const ratio = maxCount / minCount;
                        return ratio > 3 && (
                          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                            <div>
                              <div className="font-semibold text-sm text-amber-900">Class Imbalance Detected</div>
                              <div className="text-sm text-amber-700 mt-1">
                                Classes are imbalanced (ratio: {ratio.toFixed(1)}:1). Consider applying SMOTE oversampling or class weighting during training.
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  ) : labelingStats && labelingStats.labeled_records === 0 ? (
                    <div className="mt-6 text-center py-8 bg-amber-50 border border-amber-200 rounded-xl">
                      <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
                      <p className="text-sm font-semibold text-amber-900">No Labeled Data Available</p>
                      <p className="text-xs text-amber-700 mt-1">Please label some records first to see target distribution</p>
                    </div>
                  ) : null}
                </div>
                
                {/* Validation Strategy Configuration */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <h3 className="font-syne text-lg font-bold text-black-text">Validation Strategy</h3>
                    <div className="relative group">
                      <HelpCircle className="w-4 h-4 text-gray-400 hover:text-purple-primary cursor-help transition-colors" />
                      <div className="absolute left-0 top-6 w-80 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                        <div className="font-semibold mb-2">Validation Strategy:</div>
                        <div className="space-y-2">
                          <div><strong>Simple Split:</strong> Single train/test division matching your research framework (65%/35%).</div>
                          <div><strong>Cross-Validation:</strong> Multiple train/test splits (k-fold) for more reliable evaluation.</div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-700">
                          For ~100 samples, CV provides better accuracy estimates.
                        </div>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                      </div>
                    </div>
                  </div>

                  {/* Strategy Selector */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Choose Validation Method
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {/* Simple Split Option */}
                      <button
                        onClick={() => setUseCrossValidation(false)}
                        className={`p-4 border-2 rounded-lg transition-all text-left ${
                          !useCrossValidation
                            ? 'border-purple-primary bg-purple-50'
                            : 'border-gray-200 bg-white hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                            !useCrossValidation ? 'border-purple-primary' : 'border-gray-300'
                          }`}>
                            {!useCrossValidation && (
                              <div className="w-2 h-2 rounded-full bg-purple-primary"></div>
                            )}
                          </div>
                          <span className="font-semibold text-sm">Simple Split</span>
                        </div>
                        <p className="text-xs text-gray-600 ml-6">
                          Single train/test division (65%/35%)
                        </p>
                      </button>

                      {/* Cross-Validation Option */}
                      <button
                        onClick={() => setUseCrossValidation(true)}
                        className={`p-4 border-2 rounded-lg transition-all text-left ${
                          useCrossValidation
                            ? 'border-green-600 bg-green-50'
                            : 'border-gray-200 bg-white hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                            useCrossValidation ? 'border-green-600' : 'border-gray-300'
                          }`}>
                            {useCrossValidation && (
                              <div className="w-2 h-2 rounded-full bg-green-600"></div>
                            )}
                          </div>
                          <span className="font-semibold text-sm">Cross-Validation</span>
                          <span className="px-1.5 py-0.5 bg-green-600 text-white text-[10px] font-bold rounded">RECOMMENDED</span>
                        </div>
                        <p className="text-xs text-gray-600 ml-6">
                          K-fold validation for robust accuracy
                        </p>
                      </button>
                    </div>
                  </div>

                  {/* Simple Split Configuration */}
                  {!useCrossValidation && (
                    <div className="space-y-4">
                      <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5 text-purple-600" />
                          <span className="text-sm font-semibold text-purple-900">Research Framework Alignment</span>
                        </div>
                        <p className="text-xs text-purple-700">
                          Matches your study design: <strong>65% Training (n≈67), 35% Testing (n≈37)</strong>
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Test Size: {(trainTestSplit * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0.2"
                          max="0.4"
                          step="0.05"
                          value={trainTestSplit}
                          onChange={(e) => setTrainTestSplit(parseFloat(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-600 mt-1">
                          <span>{((1 - trainTestSplit) * 100).toFixed(0)}% Train</span>
                          <span>{(trainTestSplit * 100).toFixed(0)}% Test</span>
                        </div>
                        {targetDistribution && (
                          <div className="mt-2 text-xs text-gray-600">
                            <span>Approx. </span>
                            <strong>{Math.floor(Object.values(targetDistribution).reduce((a, b) => a + b, 0) * (1 - trainTestSplit))}</strong>
                            <span> train, </span>
                            <strong>{Math.ceil(Object.values(targetDistribution).reduce((a, b) => a + b, 0) * trainTestSplit)}</strong>
                            <span> test samples</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <label className="flex items-start gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={stratifyEnabled}
                            onChange={(e) => setStratifyEnabled(e.target.checked)}
                            className="w-4 h-4 text-purple-primary rounded focus:ring-purple-primary mt-0.5"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-medium text-gray-900">
                              Stratify split (Recommended)
                            </span>
                            <p className="text-xs text-gray-600 mt-1">
                              Maintains class balance in both train and test sets
                            </p>
                          </div>
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Cross-Validation Configuration */}
                  {useCrossValidation && (
                    <div className="space-y-4">
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="text-sm font-semibold text-green-900">Best Practice for Small Datasets</span>
                        </div>
                        <p className="text-xs text-green-700">
                          Cross-validation provides more reliable performance estimates by using all data for both training and testing.
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="block text-sm font-medium text-gray-700">
                            Number of Folds: {cvFolds}
                          </label>
                          {targetDistribution && (
                            <span className="text-xs text-gray-500">
                              ~{Math.floor(Object.values(targetDistribution).reduce((a, b) => a + b, 0) / cvFolds)} samples/fold
                            </span>
                          )}
                        </div>
                        <input
                          type="range"
                          min="3"
                          max="10"
                          step="1"
                          value={cvFolds}
                          onChange={(e) => setCvFolds(parseInt(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-600 mt-1">
                          <span>3 folds (fast)</span>
                          <span>10 folds (thorough)</span>
                        </div>
                      </div>

                      {/* Fold Recommendations */}
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={() => setCvFolds(5)}
                          className={`p-2 text-xs border rounded transition-all ${
                            cvFolds === 5
                              ? 'border-green-600 bg-green-50 text-green-900 font-semibold'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          5-Fold
                          <div className="text-[10px] text-gray-500 mt-0.5">Standard</div>
                        </button>
                        <button
                          onClick={() => setCvFolds(10)}
                          className={`p-2 text-xs border rounded transition-all ${
                            cvFolds === 10
                              ? 'border-green-600 bg-green-50 text-green-900 font-semibold'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          10-Fold
                          <div className="text-[10px] text-gray-500 mt-0.5">Thorough</div>
                        </button>
                        <button
                          onClick={() => targetDistribution && setCvFolds(Object.values(targetDistribution).reduce((a, b) => a + b, 0))}
                          className={`p-2 text-xs border rounded transition-all ${
                            targetDistribution && cvFolds === Object.values(targetDistribution).reduce((a, b) => a + b, 0)
                              ? 'border-green-600 bg-green-50 text-green-900 font-semibold'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                          }`}
                          disabled={!targetDistribution}
                        >
                          LOOCV
                          <div className="text-[10px] text-gray-500 mt-0.5">Leave-One-Out</div>
                        </button>
                      </div>

                      {/* Stratified CV Note */}
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-blue-700">
                          <strong>Stratified CV enabled:</strong> Each fold maintains class balance for fair evaluation.
                        </p>
                      </div>

                      {/* Warning for too many/few folds */}
                      {targetDistribution && (() => {
                        const totalSamples = Object.values(targetDistribution).reduce((a, b) => a + b, 0);
                        const minClassSize = Math.min(...Object.values(targetDistribution));
                        const samplesPerClass = minClassSize / cvFolds;
                        
                        if (samplesPerClass < 2) {
                          return (
                            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                              <div className="text-xs text-amber-700">
                                <strong>Too many folds:</strong> Some folds may have &lt;2 samples per class. Consider {Math.max(3, Math.floor(minClassSize / 2))} folds instead.
                              </div>
                            </div>
                          );
                        }
                        return null;
                      })()}
                    </div>
                  )}
                  
                  {/* Confirm and Proceed */}
                  {targetDistribution && Object.keys(targetDistribution).length > 0 && (
                    <div className="mt-6 flex items-center justify-between p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="text-sm font-semibold text-green-900">
                          {useCrossValidation ? `${cvFolds}-Fold CV` : `${((1 - trainTestSplit) * 100).toFixed(0)}/${(trainTestSplit * 100).toFixed(0)} Split`} configured!
                        </span>
                      </div>
                      <button
                        onClick={() => setActiveTab('preprocessing')}
                        className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium"
                      >
                        Next: Preprocessing →
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 4: Preprocessing (Research Methodology) */}
            {activeTab === 'preprocessing' && selectedBatch && (
              <div className="space-y-6">
                {/* Info Banner */}
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500 flex items-center justify-center flex-shrink-0">
                    <Settings className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-bold text-purple-900 mb-1">Data Preprocessing Pipeline</h3>
                    <p className="text-xs text-purple-700">
                      Transform raw data following research standards: <strong>Variable Filtration</strong> → <strong>Imputation</strong> → <strong>Winsorization</strong> → <strong>Standardization</strong>
                    </p>
                  </div>
                </div>

                {/* Run Complete Pipeline (Quick Action) */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                    <h3 className="font-syne text-base font-bold text-black-text flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-purple-primary" />
                      Quick Start: Complete Pipeline
                    </h3>
                  </div>
                  <div className="p-5">
                    <div className="space-y-4">
                      <p className="text-sm text-gray-600">
                        Run all 4 preprocessing steps automatically with research-standard settings (50% missing threshold, median imputation, 1%/99% winsorization, Z-score normalization).
                      </p>
                      <button
                        onClick={async () => {
                          if (!selectedBatch?.id) return;
                          setPreprocessingInProgress(true);
                          try {
                            const data = await mlAPI.runCompletePipeline(selectedBatch.id, {
                              filter_missing_threshold: filtrationThreshold,
                              imputation_strategy: { default: imputationStrategy },
                              winsorize_lower: winsorLower,
                              winsorize_upper: winsorUpper,
                              standardization_method: standardizationMethod
                            });
                            setPreprocessingResults(data.pipeline_report);
                            setPreprocessingStep('complete');
                            alert(`Preprocessing complete! ${data.pipeline_report.columns_removed} columns removed, ${data.pipeline_report.final_rows} rows preserved.`);
                          } catch (error) {
                            console.error('Pipeline failed:', error);
                            alert('Preprocessing pipeline failed. See console for details.');
                          } finally {
                            setPreprocessingInProgress(false);
                          }
                        }}
                        disabled={preprocessingInProgress || preprocessingStep === 'complete'}
                        className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-purple-primary to-purple-600 text-white hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-semibold flex items-center justify-center gap-2"
                      >
                        {preprocessingInProgress ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Processing Pipeline...
                          </>
                        ) : preprocessingStep === 'complete' ? (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Pipeline Complete
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            Run Complete Pipeline
                          </>
                        )}
                      </button>
                      {preprocessingResults && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg space-y-2">
                          <div className="flex items-center gap-2 text-sm font-semibold text-green-900">
                            <CheckCircle className="w-4 h-4" />
                            Pipeline Execution Summary
                          </div>
                          <div className="grid grid-cols-2 gap-3 text-xs">
                            <div className="p-2 bg-white rounded border">
                              <div className="text-gray-500">Original Columns</div>
                              <div className="font-bold text-black-text">{preprocessingResults.original_columns}</div>
                            </div>
                            <div className="p-2 bg-white rounded border">
                              <div className="text-gray-500">Final Columns</div>
                              <div className="font-bold text-black-text">{preprocessingResults.final_columns}</div>
                            </div>
                            <div className="p-2 bg-white rounded border">
                              <div className="text-gray-500">Columns Removed</div>
                              <div className="font-bold text-red-600">{preprocessingResults.columns_removed}</div>
                            </div>
                            <div className="p-2 bg-white rounded border">
                              <div className="text-gray-500">Rows Preserved</div>
                              <div className="font-bold text-green-600">{preprocessingResults.final_rows}</div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Individual Step Controls */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Step 1: Variable Filtration */}
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-white/40 bg-white/60">
                      <h4 className="text-sm font-bold text-black-text flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-primary flex items-center justify-center text-xs font-bold">1</span>
                        Variable Filtration
                      </h4>
                    </div>
                    <div className="p-4 space-y-3">
                      <p className="text-xs text-gray-600">Remove variables with excessive missing data (research standard: &gt;50%).</p>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Missing Data Threshold</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min="0.3"
                            max="0.8"
                            step="0.05"
                            value={filtrationThreshold}
                            onChange={(e) => setFiltrationThreshold(parseFloat(e.target.value))}
                            className="flex-1"
                          />
                          <span className="text-sm font-bold text-purple-primary w-12">{(filtrationThreshold * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <button
                        onClick={async () => {
                          if (!selectedBatch?.id) return;
                          setPreprocessingInProgress(true);
                          try {
                            const data = await mlAPI.filterVariables(selectedBatch.id, filtrationThreshold);
                            setFiltrationReport(data.filtration_report);
                            setPreprocessingStep('filtration');
                            alert(`Filtration complete! ${data.filtration_report.removed_columns?.length || 0} columns removed.`);
                          } catch (error) {
                            console.error('Filtration failed:', error);
                            alert('Variable filtration failed. See console for details.');
                          } finally {
                            setPreprocessingInProgress(false);
                          }
                        }}
                        disabled={preprocessingInProgress}
                        className="w-full px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-600 disabled:opacity-50 transition-all text-xs font-medium"
                      >
                        Run Filtration
                      </button>
                      {filtrationReport && (
                        <div className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                          <div className="font-semibold text-green-900">Removed: {filtrationReport.removed_columns?.length || 0} columns</div>
                          <div className="text-green-700">Kept: {filtrationReport.kept_columns?.length || 0} columns</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 2: Imputation */}
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-white/40 bg-white/60">
                      <h4 className="text-sm font-bold text-black-text flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-primary flex items-center justify-center text-xs font-bold">2</span>
                        Imputation
                      </h4>
                    </div>
                    <div className="p-4 space-y-3">
                      <p className="text-xs text-gray-600">Fill remaining missing values (research standard: median for numeric, mode for categorical).</p>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Strategy</label>
                        <select
                          value={imputationStrategy}
                          onChange={(e) => setImputationStrategy(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                        >
                          <option value="median">Median (Numeric) / Mode (Categorical)</option>
                          <option value="mean">Mean (Numeric) / Mode (Categorical)</option>
                          <option value="mode">Mode (All Variables)</option>
                        </select>
                      </div>
                      <button
                        onClick={async () => {
                          if (!selectedBatch?.id) return;
                          setPreprocessingInProgress(true);
                          try {
                            const data = await mlAPI.imputeMissingValues(selectedBatch.id, { default: imputationStrategy });
                            setImputationReport(data.report);
                            setPreprocessingStep('imputation');
                            alert(`Imputation complete! Missing values filled using ${imputationStrategy}.`);
                          } catch (error) {
                            console.error('Imputation failed:', error);
                            alert('Imputation failed. See console for details.');
                          } finally {
                            setPreprocessingInProgress(false);
                          }
                        }}
                        disabled={preprocessingInProgress}
                        className="w-full px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-600 disabled:opacity-50 transition-all text-xs font-medium"
                      >
                        Run Imputation
                      </button>
                      {imputationReport && (
                        <div className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                          <div className="font-semibold text-green-900">Strategy: {imputationStrategy}</div>
                          <div className="text-green-700">Missing values filled</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 3: Winsorization */}
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-white/40 bg-white/60">
                      <h4 className="text-sm font-bold text-black-text flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-primary flex items-center justify-center text-xs font-bold">3</span>
                        Winsorization
                      </h4>
                    </div>
                    <div className="p-4 space-y-3">
                      <p className="text-xs text-gray-600">Cap outliers at percentiles (research standard: 1st & 99th). Preserves sample size.</p>
                      <div className="space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Lower Percentile</label>
                          <div className="flex items-center gap-2">
                            <input
                              type="range"
                              min="0.001"
                              max="0.05"
                              step="0.005"
                              value={winsorLower}
                              onChange={(e) => setWinsorLower(parseFloat(e.target.value))}
                              className="flex-1"
                            />
                            <span className="text-xs font-bold text-purple-primary w-12">{(winsorLower * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Upper Percentile</label>
                          <div className="flex items-center gap-2">
                            <input
                              type="range"
                              min="0.95"
                              max="0.999"
                              step="0.005"
                              value={winsorUpper}
                              onChange={(e) => setWinsorUpper(parseFloat(e.target.value))}
                              className="flex-1"
                            />
                            <span className="text-xs font-bold text-purple-primary w-12">{(winsorUpper * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={async () => {
                          if (!selectedBatch?.id) return;
                          setPreprocessingInProgress(true);
                          try {
                            const data = await mlAPI.winsorizeData(selectedBatch.id, winsorLower, winsorUpper);
                            setWinsorizeReport(data.winsorization_report);
                            setPreprocessingStep('winsorization');
                            alert(`Winsorization complete! Outliers capped at ${(winsorLower * 100).toFixed(1)}% and ${(winsorUpper * 100).toFixed(1)}%.`);
                          } catch (error) {
                            console.error('Winsorization failed:', error);
                            alert('Winsorization failed. See console for details.');
                          } finally {
                            setPreprocessingInProgress(false);
                          }
                        }}
                        disabled={preprocessingInProgress}
                        className="w-full px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-600 disabled:opacity-50 transition-all text-xs font-medium"
                      >
                        Run Winsorization
                      </button>
                      {winsorizeReport && (
                        <div className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                          <div className="font-semibold text-green-900">Capped: {winsorizeReport.total_capped_values || 0} values</div>
                          <div className="text-green-700">Rows preserved: 100%</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 4: Standardization */}
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-white/40 bg-white/60">
                      <h4 className="text-sm font-bold text-black-text flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-primary flex items-center justify-center text-xs font-bold">4</span>
                        Standardization
                      </h4>
                    </div>
                    <div className="p-4 space-y-3">
                      <p className="text-xs text-gray-600">Scale features to common range (research standard: Z-score normalization).</p>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Method</label>
                        <select
                          value={standardizationMethod}
                          onChange={(e) => setStandardizationMethod(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                        >
                          <option value="standard">Z-Score (mean=0, std=1)</option>
                          <option value="minmax">Min-Max (0 to 1)</option>
                          <option value="robust">Robust (median-based)</option>
                        </select>
                      </div>
                      <button
                        onClick={async () => {
                          if (!selectedBatch?.id) return;
                          setPreprocessingInProgress(true);
                          try {
                            const data = await mlAPI.normalizeData(selectedBatch.id, standardizationMethod);
                            setStandardizationReport(data.report);
                            setPreprocessingStep('standardization');
                            alert(`Standardization complete! Features normalized using ${standardizationMethod}.`);
                          } catch (error) {
                            console.error('Standardization failed:', error);
                            alert('Standardization failed. See console for details.');
                          } finally {
                            setPreprocessingInProgress(false);
                          }
                        }}
                        disabled={preprocessingInProgress}
                        className="w-full px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-600 disabled:opacity-50 transition-all text-xs font-medium"
                      >
                        Run Standardization
                      </button>
                      {standardizationReport && (
                        <div className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                          <div className="font-semibold text-green-900">Method: {standardizationMethod}</div>
                          <div className="text-green-700">Features scaled</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Proceed to Feature Engineering */}
                {preprocessingStep === 'complete' && (
                  <div className="flex items-center justify-between p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-semibold text-green-900">
                        Preprocessing Complete! Data ready for feature engineering.
                      </span>
                    </div>
                    <button
                      onClick={() => setActiveTab('features')}
                      className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium"
                    >
                      Next: Feature Engineering →
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* TAB 5: Feature Engineering */}
            {activeTab === 'features' && selectedBatch && (
              <div className="space-y-6">
                {/* ── Info Banner ──────────────────────────────────────────── */}
                <div className="bg-white border border-gray-200 rounded-xl p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm text-gray-900 mb-1">
                        Inflammatory &amp; Immunological Feature Engineering
                      </h4>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        Derives new predictive features from raw biomarker columns.
                        These features are <strong className="text-gray-800">not redundant</strong> with raw data —
                        they encode non-linear relationships (ratios, products, temporal deltas) that linear models
                        cannot discover from raw columns alone. Scope is optimised for systemic inflammatory
                        conditions; NLR, PLR, and SII are additionally validated in oncology contexts.
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        Click the info icon on any feature to view its formula, required columns, clinical evidence, and scope notes.
                      </p>
                    </div>
                    <button
                      onClick={() => setShowFeatureRationale(!showFeatureRationale)}
                      className="flex-shrink-0 text-xs font-medium text-purple-600 hover:text-purple-800 border border-purple-200 hover:border-purple-400 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      {showFeatureRationale ? 'Hide' : 'Why not let the model figure it out?'}
                    </button>
                  </div>
                </div>

                {/* ── Collapsible model-limitation rationale ───────────────── */}
                {showFeatureRationale && (
                  <div className="bg-slate-900 text-slate-100 rounded-xl p-5 text-xs leading-relaxed space-y-4">
                    <div className="font-semibold text-slate-100 text-sm">
                      Why feature engineering cannot be skipped
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-slate-800 rounded-lg p-4 space-y-1.5">
                        <div className="font-semibold text-slate-200">Linear models — LASSO, Logistic Regression</div>
                        <p className="text-slate-400">
                          Only capture additive relationships. CRP÷ESR requires division — a non-linear operation
                          that is structurally invisible to these models regardless of dataset size.
                        </p>
                      </div>
                      <div className="bg-slate-800 rounded-lg p-4 space-y-1.5">
                        <div className="font-semibold text-slate-200">Tree models — Random Forest, XGBoost</div>
                        <p className="text-slate-400">
                          Can approximate ratios through recursive splits, but require many splits and large
                          datasets to do so. Providing the ratio explicitly is far more data-efficient and
                          produces interpretable feature importance scores.
                        </p>
                      </div>
                    </div>
                    <div className="border-t border-slate-700 pt-4 text-slate-400 space-y-1">
                      <p>
                        <strong className="text-slate-300">Feature Scaling</strong> (handled in the previous tab) normalises
                        existing values. <strong className="text-slate-300">Feature Engineering</strong> creates new information
                        that does not exist anywhere in the raw data. They serve different purposes in the ML pipeline.
                      </p>
                      <p>All features in this catalogue are derived from published clinical indices — not speculative constructs.</p>
                    </div>
                  </div>
                )}

                {/* ── Feature Engineering Configuration ───────────────────── */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <h3 className="font-syne text-lg font-bold text-black-text mb-1">Feature Engineering</h3>
                  <p className="text-sm text-gray-muted mb-6">
                    Select features to derive. Each entry shows its formula, required source columns, and disease scope.
                    Click the info icon to expand the full clinical justification.
                  </p>

                  <div className="space-y-6">

                    {/* ── Biomarker & Immune Ratios ────────────────────────── */}
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-sm text-gray-900">Biomarker &amp; Immune Ratios</h4>
                          <p className="text-xs text-gray-500 mt-0.5">Ratio features encode non-linear relationships invisible to linear models</p>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={featureEngineeringConfig.enableRatios}
                            onChange={(e) => setFeatureEngineeringConfig({
                              ...featureEngineeringConfig,
                              enableRatios: e.target.checked,
                              crpEsrRatio: e.target.checked,
                              nlrRatio: e.target.checked,
                              plrRatio: e.target.checked,
                              siiIndex: e.target.checked,
                            })}
                            className="w-4 h-4 text-purple-primary rounded"
                          />
                          <span className="text-xs font-semibold text-purple-600">Enable All</span>
                        </label>
                      </div>

                      <div className="space-y-2">
                        {/* CRP/ESR Ratio */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.crpEsrRatio}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, crpEsrRatio: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableRatios}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.crpEsrRatio.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.crpEsrRatio.formula}</code>
                                <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-100">{FEATURE_CATALOG.crpEsrRatio.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.crpEsrRatio.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.crpEsrRatio.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'crpEsrRatio' ? null : 'crpEsrRatio'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'crpEsrRatio' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.crpEsrRatio.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.crpEsrRatio.modelNote}</div>
                              <div className="bg-amber-50 border border-amber-100 rounded p-2 text-amber-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.crpEsrRatio.scopeNote}</div>
                            </div>
                          )}
                        </div>

                        {/* NLR */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.nlrRatio}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, nlrRatio: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableRatios}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.nlrRatio.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.nlrRatio.formula}</code>
                                <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded border border-green-100">{FEATURE_CATALOG.nlrRatio.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.nlrRatio.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.nlrRatio.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'nlrRatio' ? null : 'nlrRatio'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'nlrRatio' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.nlrRatio.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.nlrRatio.modelNote}</div>
                              <div className="bg-green-50 border border-green-100 rounded p-2 text-green-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.nlrRatio.scopeNote}</div>
                            </div>
                          )}
                        </div>

                        {/* PLR */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.plrRatio}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, plrRatio: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableRatios}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.plrRatio.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.plrRatio.formula}</code>
                                <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded border border-green-100">{FEATURE_CATALOG.plrRatio.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.plrRatio.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.plrRatio.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'plrRatio' ? null : 'plrRatio'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'plrRatio' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.plrRatio.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.plrRatio.modelNote}</div>
                              <div className="bg-green-50 border border-green-100 rounded p-2 text-green-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.plrRatio.scopeNote}</div>
                            </div>
                          )}
                        </div>

                        {/* SII */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.siiIndex}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, siiIndex: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableRatios}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.sii.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.sii.formula}</code>
                                <span className="text-xs bg-teal-50 text-teal-700 px-2 py-0.5 rounded border border-teal-100">{FEATURE_CATALOG.sii.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.sii.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.sii.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'sii' ? null : 'sii'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'sii' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.sii.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.sii.modelNote}</div>
                              <div className="bg-teal-50 border border-teal-100 rounded p-2 text-teal-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.sii.scopeNote}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* ── Temporal Features ────────────────────────────────── */}
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-sm text-gray-900">Temporal Features</h4>
                          <p className="text-xs text-gray-500 mt-0.5">Converts timestamps into predictive continuous variables</p>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={featureEngineeringConfig.enableTemporal}
                            onChange={(e) => setFeatureEngineeringConfig({
                              ...featureEngineeringConfig,
                              enableTemporal: e.target.checked,
                              diseaseDuration: e.target.checked
                            })}
                            className="w-4 h-4 text-purple-primary rounded"
                          />
                          <span className="text-xs font-semibold text-purple-600">Enable All</span>
                        </label>
                      </div>

                      <div className="space-y-2">
                        {/* Disease Duration */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.diseaseDuration}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, diseaseDuration: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableTemporal}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.diseaseDuration.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.diseaseDuration.formula}</code>
                                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">{FEATURE_CATALOG.diseaseDuration.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.diseaseDuration.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.diseaseDuration.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'diseaseDuration' ? null : 'diseaseDuration'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'diseaseDuration' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.diseaseDuration.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.diseaseDuration.modelNote}</div>
                              <div className="bg-slate-100 border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.diseaseDuration.scopeNote}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* ── Derived Indices ──────────────────────────────────── */}
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-sm text-gray-900">Derived Indices</h4>
                          <p className="text-xs text-gray-500 mt-0.5">Composite scores that reduce multicollinearity and mirror validated clinical activity indices</p>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={featureEngineeringConfig.enableDerived}
                            onChange={(e) => setFeatureEngineeringConfig({
                              ...featureEngineeringConfig,
                              enableDerived: e.target.checked,
                              inflammationScore: e.target.checked,
                              organInvolvement: e.target.checked
                            })}
                            className="w-4 h-4 text-purple-primary rounded"
                          />
                          <span className="text-xs font-semibold text-purple-600">Enable All</span>
                        </label>
                      </div>

                      <div className="space-y-2">
                        {/* Inflammation Index */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.inflammationScore}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, inflammationScore: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableDerived}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.inflammationScore.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.inflammationScore.formula}</code>
                                <span className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded border border-orange-100">{FEATURE_CATALOG.inflammationScore.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.inflammationScore.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.inflammationScore.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'inflammationScore' ? null : 'inflammationScore'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'inflammationScore' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.inflammationScore.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.inflammationScore.modelNote}</div>
                              <div className="bg-amber-50 border border-amber-100 rounded p-2 text-amber-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.inflammationScore.scopeNote}</div>
                            </div>
                          )}
                        </div>

                        {/* Organ Involvement Count */}
                        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                          <label className="flex items-start gap-3 cursor-pointer hover:bg-gray-50 p-3 transition-colors">
                            <input
                              type="checkbox"
                              checked={featureEngineeringConfig.organInvolvement}
                              onChange={(e) => setFeatureEngineeringConfig({ ...featureEngineeringConfig, organInvolvement: e.target.checked })}
                              disabled={!featureEngineeringConfig.enableDerived}
                              className="w-4 h-4 text-purple-primary rounded mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-900 font-medium">{FEATURE_CATALOG.organInvolvement.label}</span>
                                <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono border border-slate-200">{FEATURE_CATALOG.organInvolvement.formula}</code>
                                <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-100">{FEATURE_CATALOG.organInvolvement.evidenceTag}</span>
                              </div>
                              <p className="text-xs text-gray-400 mt-0.5">Requires: {FEATURE_CATALOG.organInvolvement.requires.join(', ')}</p>
                              <p className="text-xs text-slate-500 mt-0.5">Scope: {FEATURE_CATALOG.organInvolvement.scope}</p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); setExpandedFeature(expandedFeature === 'organInvolvement' ? null : 'organInvolvement'); }}
                              className="text-gray-400 hover:text-purple-600 transition-colors flex-shrink-0 mt-0.5"
                            >
                              <HelpCircle className="w-4 h-4" />
                            </button>
                          </label>
                          {expandedFeature === 'organInvolvement' && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 text-xs space-y-2">
                              <div><span className="font-semibold text-gray-800">Clinical rationale: </span><span className="text-gray-700">{FEATURE_CATALOG.organInvolvement.rationale}</span></div>
                              <div className="bg-white border border-slate-200 rounded p-2 text-slate-600"><span className="font-semibold">Why linear models cannot derive this: </span>{FEATURE_CATALOG.organInvolvement.modelNote}</div>
                              <div className="bg-amber-50 border border-amber-100 rounded p-2 text-amber-800"><span className="font-semibold">Scope note: </span>{FEATURE_CATALOG.organInvolvement.scopeNote}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={applyFeatureEngineering}
                      disabled={loading}
                      className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-purple-primary text-white hover:shadow-lg transition-all disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          Engineering Features...
                        </>
                      ) : (
                        <>
                          <Zap className="w-5 h-5" />
                          Apply Feature Engineering
                        </>
                      )}
                    </button>
                  </div>
                  
                  {/* Feature Engineering Results */}
                  {featureEngineeringResults && (
                    <div className="mt-6 space-y-4">
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="font-semibold text-green-900">
                            {featureEngineeringResults.features_added} new features created
                          </span>
                        </div>
                        <div className="text-sm text-green-700 mt-1">
                          {featureEngineeringResults.original_feature_count} → {featureEngineeringResults.engineered_feature_count} features
                        </div>
                      </div>
                      
                      {featureEngineeringResults.new_features.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm text-black-text mb-3">Engineered Features</h4>
                          <div className="space-y-2">
                            {featureEngineeringResults.new_features.map((feature, i) => (
                              <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
                                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="font-medium text-sm text-gray-900">{feature.name}</div>
                                  <div className="text-xs text-gray-600 mt-0.5">{feature.description}</div>
                                  <div className="text-xs text-purple-600 mt-1">
                                    {feature.type.toUpperCase()} • Sources: {feature.source_columns.join(', ')}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {featureEngineeringResults.skipped_features && featureEngineeringResults.skipped_features.length > 0 && (
                        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <div className="font-semibold text-sm text-amber-900 mb-2">
                                Skipped Features ({featureEngineeringResults.skipped_features.length})
                              </div>
                              <div className="space-y-1">
                                {featureEngineeringResults.skipped_features.map((skipped, i) => (
                                  <div key={i} className="text-xs text-amber-700">
                                    • {skipped.name}: {skipped.reason}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: Feature Selection */}
            {activeTab === 'feature-selection' && selectedBatch && (
              <div className="space-y-6">
                {/* Info Banner */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
                    <Filter className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm text-blue-900 mb-1">Feature Selection Workflow</h4>
                    <p className="text-xs text-blue-700 leading-relaxed">
                      Select the most relevant features using expert knowledge (clinician selection) and statistical methods (LASSO). 
                      This improves model accuracy and interpretability while reducing overfitting.
                    </p>
                  </div>
                </div>

                {/* Selection Mode Chooser */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <h3 className="font-syne text-lg font-bold text-black-text mb-4">Selection Strategy</h3>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => setFeatureSelectionMode('manual')}
                      className={`p-4 border-2 rounded-lg transition-all text-left ${
                        featureSelectionMode === 'manual'
                          ? 'border-purple-primary bg-purple-50'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                          featureSelectionMode === 'manual' ? 'border-purple-primary' : 'border-gray-300'
                        }`}>
                          {featureSelectionMode === 'manual' && (
                            <div className="w-2 h-2 rounded-full bg-purple-primary"></div>
                          )}
                        </div>
                        <span className="font-semibold text-sm">Clinician Selection</span>
                      </div>
                      <p className="text-xs text-gray-600 ml-6">
                        Expert-driven feature selection based on clinical knowledge
                      </p>
                    </button>

                    <button
                      onClick={() => setFeatureSelectionMode('lasso')}
                      className={`p-4 border-2 rounded-lg transition-all text-left ${
                        featureSelectionMode === 'lasso'
                          ? 'border-green-600 bg-green-50'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                          featureSelectionMode === 'lasso' ? 'border-green-600' : 'border-gray-300'
                        }`}>
                          {featureSelectionMode === 'lasso' && (
                            <div className="w-2 h-2 rounded-full bg-green-600"></div>
                          )}
                        </div>
                        <span className="font-semibold text-sm">LASSO Selection</span>
                      </div>
                      <p className="text-xs text-gray-600 ml-6">
                        Automated statistical feature selection using L1 regularization
                      </p>
                    </button>

                    <button
                      onClick={() => setFeatureSelectionMode('combined')}
                      className={`p-4 border-2 rounded-lg transition-all text-left ${
                        featureSelectionMode === 'combined'
                          ? 'border-amber-500 bg-amber-50'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                          featureSelectionMode === 'combined' ? 'border-amber-500' : 'border-gray-300'
                        }`}>
                          {featureSelectionMode === 'combined' && (
                            <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                          )}
                        </div>
                        <span className="font-semibold text-sm">Combined</span>
                        <span className="px-1.5 py-0.5 bg-amber-500 text-white text-[10px] font-bold rounded">RECOMMENDED</span>
                      </div>
                      <p className="text-xs text-gray-600 ml-6">
                        Intersection of clinician expertise and statistical significance
                      </p>
                    </button>
                  </div>
                </div>

                {/* Correlation Detection */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <h3 className="font-syne text-lg font-bold text-black-text">Correlation Detection</h3>
                    <div className="relative group">
                      <HelpCircle className="w-4 h-4 text-gray-400 hover:text-purple-primary cursor-help transition-colors" />
                      <div className="absolute left-0 top-6 w-80 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                        <div className="font-semibold mb-2">Correlation Detection:</div>
                        <div>Identifies highly correlated features (redundant information). Removing one from each pair reduces multicollinearity and improves model stability.</div>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Correlation Threshold: {correlationThreshold}
                      </label>
                      <input
                        type="range"
                        min="0.7"
                        max="0.95"
                        step="0.05"
                        value={correlationThreshold}
                        onChange={(e) => setCorrelationThreshold(parseFloat(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-600 mt-1">
                        <span>0.7 (aggressive)</span>
                        <span>0.95 (conservative)</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-2">
                        Features with correlation above {correlationThreshold} will be flagged. Higher values keep more features.
                      </p>
                    </div>

                    <button
                      onClick={async () => {
                        // Placeholder for correlation detection
                        alert('Correlation analysis will identify redundant features. Implementation pending backend endpoint.');
                      }}
                      className="w-full px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-all text-sm font-medium"
                    >
                      Detect Correlated Features
                    </button>
                  </div>
                </div>

                {/* Clinician Selection (Manual) */}
                {(featureSelectionMode === 'manual' || featureSelectionMode === 'combined') && (
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-syne text-lg font-bold text-black-text">Clinician Feature Selection</h3>
                      <div className="text-xs text-purple-600 font-semibold">
                        {clinicianSelectedFeatures.length} features selected
                      </div>
                    </div>

                    <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <p className="text-xs text-purple-700">
                        <strong>Expert-driven selection:</strong> Choose features based on clinical relevance, known biomarkers, and domain expertise. 
                        This ensures interpretability and aligns with medical practice.
                      </p>
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {/* Placeholder feature list - will be populated from actual data */}
                      {['lab_results.C3', 'lab_results.C4', 'lab_results.SLEDAI', 'lab_results.CRP', 'lab_results.ESR', 
                        'demographics.Age', 'demographics.Gender', 'clinical.Disease_Duration',
                        'derived.CRP_ESR_ratio', 'derived.Inflammation_Index'].map((feature) => (
                        <label key={feature} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors">
                          <input
                            type="checkbox"
                            checked={clinicianSelectedFeatures.includes(feature)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setClinicianSelectedFeatures([...clinicianSelectedFeatures, feature]);
                              } else {
                                setClinicianSelectedFeatures(clinicianSelectedFeatures.filter(f => f !== feature));
                              }
                            }}
                            className="w-4 h-4 text-purple-primary rounded mt-0.5"
                          />
                          <div className="flex-1">
                            <span className="text-sm text-gray-900 font-medium">{feature.split('.')[1] || feature}</span>
                            <p className="text-xs text-gray-600 mt-0.5">Category: {feature.split('.')[0]}</p>
                          </div>
                        </label>
                      ))}
                    </div>

                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={() => {
                          const allFeatures = ['lab_results.C3', 'lab_results.C4', 'lab_results.SLEDAI', 'lab_results.CRP', 'lab_results.ESR', 
                            'demographics.Age', 'demographics.Gender', 'clinical.Disease_Duration',
                            'derived.CRP_ESR_ratio', 'derived.Inflammation_Index'];
                          setClinicianSelectedFeatures(allFeatures);
                        }}
                        className="flex-1 px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all text-sm font-medium"
                      >
                        Select All
                      </button>
                      <button
                        onClick={() => setClinicianSelectedFeatures([])}
                        className="flex-1 px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all text-sm font-medium"
                      >
                        Clear Selection
                      </button>
                    </div>
                  </div>
                )}

                {/* LASSO Feature Selection */}
                {(featureSelectionMode === 'lasso' || featureSelectionMode === 'combined') && (
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-syne text-lg font-bold text-black-text">LASSO Feature Selection</h3>
                      {lassoFeatures.length > 0 && (
                        <div className="text-xs text-green-600 font-semibold">
                          {lassoFeatures.length} features selected by LASSO
                        </div>
                      )}
                    </div>

                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-xs text-green-700">
                        <strong>LASSO (L1 Regularization):</strong> Automatically selects features by shrinking irrelevant feature coefficients to zero. 
                        Features with non-zero coefficients are statistically significant for prediction.
                      </p>
                    </div>

                    <div className="space-y-4 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Regularization Strength (Alpha): {lassoAlpha.toFixed(5)}
                        </label>
                        <input
                          type="range"
                          min="0.00001"
                          max="0.01"
                          step="0.00001"
                          value={lassoAlpha}
                          onChange={(e) => setLassoAlpha(parseFloat(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-600 mt-1">
                          <span>0.00001 (more features)</span>
                          <span>0.01 (fewer features)</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-2">
                          For small datasets (~100 samples), use very low alpha (0.00001-0.0001) to keep more features. Higher alpha = stronger regularization = fewer features.
                        </p>
                      </div>

                      <button
                        onClick={async () => {
                          // Placeholder for LASSO execution
                          alert(`Running LASSO with alpha=${lassoAlpha}... Implementation pending backend endpoint.`);
                          // Simulate LASSO result
                          setLassoFeatures(['lab_results.SLEDAI', 'lab_results.C3', 'lab_results.CRP', 'demographics.Age', 'derived.CRP_ESR_ratio']);
                        }}
                        className="w-full px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium"
                      >
                        Run LASSO Feature Selection
                      </button>
                    </div>

                    {/* LASSO Results */}
                    {lassoFeatures.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-gray-900 mb-3">Selected Features:</h4>
                        <div className="space-y-2">
                          {lassoFeatures.map((feature, idx) => (
                            <div key={feature} className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm text-gray-900">{feature}</span>
                              <span className="text-xs text-green-600 font-semibold">Rank #{idx + 1}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Final Selected Features Summary */}
                <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                  <h3 className="font-syne text-lg font-bold text-black-text mb-4">Final Selected Features</h3>

                  <div className="mb-4">
                    <button
                      onClick={() => {
                        if (featureSelectionMode === 'manual') {
                          setFinalFeatures(clinicianSelectedFeatures);
                        } else if (featureSelectionMode === 'lasso') {
                          setFinalFeatures(lassoFeatures);
                        } else {
                          // Combined: intersection of both
                          const combined = clinicianSelectedFeatures.filter(f => lassoFeatures.includes(f));
                          setFinalFeatures(combined);
                        }
                      }}
                      className="w-full px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all text-sm font-medium"
                    >
                      {featureSelectionMode === 'combined' ? 'Combine Selections (Intersection)' : 'Confirm Feature Selection'}
                    </button>
                  </div>

                  {finalFeatures.length > 0 && (
                    <>
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5 text-blue-600" />
                          <span className="text-sm font-semibold text-blue-900">
                            {finalFeatures.length} features selected for training
                          </span>
                        </div>
                        <p className="text-xs text-blue-700">
                          {featureSelectionMode === 'manual' && 'Expert-selected features based on clinical knowledge.'}
                          {featureSelectionMode === 'lasso' && 'Statistically significant features identified by LASSO.'}
                          {featureSelectionMode === 'combined' && 'Features confirmed by both clinical expertise AND statistical significance.'}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mb-4">
                        {finalFeatures.map((feature) => (
                          <div key={feature} className="p-2 bg-purple-50 border border-purple-200 rounded text-sm text-purple-900">
                            {feature}
                          </div>
                        ))}
                      </div>

                      <button
                        onClick={() => setActiveTab('validation')}
                        className="w-full px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium"
                      >
                        Proceed to Validation →
                      </button>
                    </>
                  )}

                  {finalFeatures.length === 0 && (
                    <div className="text-center py-8 bg-gray-50 rounded-lg">
                      <Filter className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-sm text-gray-600">No features selected yet</p>
                      <p className="text-xs text-gray-500 mt-1">Choose features using the methods above, then confirm your selection</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 7: Validation */}
            {activeTab === 'validation' && selectedBatch && (
              <div className="space-y-6">
                {/* Info Banner */}
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center flex-shrink-0">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm text-green-900 mb-1">Data Quality Validation</h4>
                    <p className="text-xs text-green-700 leading-relaxed">
                      Run comprehensive validation checks to ensure your dataset meets ML training requirements. 
                      This includes sample size, missing values, class balance, feature quality, and labeling coverage checks.
                    </p>
                  </div>
                </div>

                {/* Run Validation Button */}
                {!validationResults ? (
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-8 text-center">
                    <Shield className="w-16 h-16 text-purple-primary mx-auto mb-4" />
                    <h3 className="font-syne text-xl font-bold text-black-text mb-2">Run 10-Check Validation</h3>
                    <p className="text-sm text-gray-muted mb-6">
                      Validate your dataset against 10 quality checks before training
                    </p>
                    
                    {/* Prerequisites Check */}
                    {(!isLabelingComplete || !isTargetComplete) ? (
                      <div className="max-w-md mx-auto mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <div className="flex items-start gap-3 text-left">
                          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-sm text-amber-900 mb-2">Prerequisites Required</div>
                            <div className="text-xs text-amber-700 space-y-1">
                              {!isLabelingComplete && <div>• Complete labeling (80% minimum)</div>}
                              {!isTargetComplete && <div>• Target column is required (default: labels_disease_classification)</div>}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : !isFeaturesComplete ? (
                      <div className="max-w-md mx-auto mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-start gap-3 text-left">
                          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-sm text-blue-900 mb-2">⚠️ Feature Engineering Skipped</div>
                            <div className="text-xs text-blue-700">
                              Validation will run on raw features only. Consider running feature engineering (Tab 4) for better model performance.
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    <button
                      onClick={() => runValidation(selectedBatch.id)}
                      disabled={loading || !isLabelingComplete || !isTargetComplete}
                      className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-5 h-5 inline mr-2 animate-spin" />
                          Running Validation...
                        </>
                      ) : (
                        <>
                          <Play className="w-5 h-5 inline mr-2" />
                          Run Validation
                        </>
                      )}
                    </button>
                    
                    {(!isLabelingComplete || !isTargetComplete) && (
                      <p className="text-xs text-gray-500 mt-3">
                        Complete labeling (80%+) and ensure target column is set
                      </p>
                    )}
                  </div>
                ) : null}

                {/* Validation Results */}
                {validationResults && (
                  <>
                    {/* Validation Summary */}
                    <div className="grid grid-cols-4 gap-4">
                      <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-muted uppercase">Total Checks</span>
                          <Shield className="w-4 h-4 text-purple-primary" />
                        </div>
                        <div className="font-syne text-2xl font-bold text-black-text">{validationResults.total_checks}</div>
                      </div>
                      <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-muted uppercase">Passed</span>
                          <CheckCircle className="w-4 h-4 text-green" />
                        </div>
                        <div className="font-syne text-2xl font-bold text-green">{validationResults.passed}</div>
                      </div>
                      <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-muted uppercase">Warnings</span>
                          <AlertCircle className="w-4 h-4 text-amber" />
                        </div>
                        <div className="font-syne text-2xl font-bold text-amber">{validationResults.warnings}</div>
                      </div>
                      <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-muted uppercase">Errors</span>
                          <AlertCircle className="w-4 h-4 text-red-600" />
                        </div>
                        <div className="font-syne text-2xl font-bold text-red-600">{validationResults.errors}</div>
                      </div>
                    </div>

                    {/* Validation Checks */}
                    <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                      <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                        <h3 className="font-syne text-base font-bold text-black-text">Validation Checks</h3>
                      </div>
                      <div className="p-5 space-y-3">
                        {validationResults.checks.map((check, idx) => {
                          const statusIcon = check.status === 'passed' ? CheckCircle : AlertCircle;
                          const StatusIcon = statusIcon;
                          const statusColor = 
                            check.status === 'passed' ? 'text-green' :
                            check.severity === 'error' ? 'text-red-600' : 'text-amber';
                          const bgColor = 
                            check.status === 'passed' ? 'bg-green-dim' :
                            check.severity === 'error' ? 'bg-red-50' : 'bg-amber-dim';
                          
                          return (
                            <div key={idx} className={`p-4 rounded-xl border ${bgColor} border-white/40`}>
                              <div className="flex items-start gap-3">
                                <StatusIcon className={`w-5 h-5 ${statusColor} mt-0.5`} />
                                <div className="flex-1">
                                  <div className="flex items-center justify-between mb-1">
                                    <h4 className="font-semibold text-sm text-black-text">{check.name}</h4>
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${statusColor}`}>
                                      {check.status.toUpperCase()}
                                    </span>
                                  </div>
                                  <p className="text-xs text-gray-muted">{check.message}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Recommendations */}
                    {validationResults.recommendations.length > 0 && (
                      <div className="bg-gradient-to-br from-purple-50 to-purple-50/50 border border-purple-200 rounded-2xl p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Zap className="w-5 h-5 text-purple-primary" />
                          <h3 className="font-syne text-base font-bold text-purple-primary">Recommendations</h3>
                        </div>
                        <ul className="space-y-2">
                          {validationResults.recommendations.map((rec, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-gray-muted">
                              <CheckCircle className="w-4 h-4 text-purple-primary mt-0.5 flex-shrink-0" />
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* TAB 8: Summary */}
            {activeTab === 'summary' && selectedBatch && (
              <div className="space-y-6">
                {/* Configuration Summary Card */}
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-300 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-purple-primary flex items-center justify-center">
                        <BarChart3 className="w-5 h-5 text-white" />
                      </div>
                      <h3 className="font-syne text-xl font-bold text-purple-primary">Configuration Summary</h3>
                    </div>
                    <button
                      onClick={saveConfiguration}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border-2 border-purple-300 text-purple-primary hover:bg-purple-50 transition-all font-medium"
                    >
                      <Save className="w-4 h-4" />
                      Save Draft
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isUploadComplete ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isUploadComplete ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">1</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Dataset Selected</div>
                          <div className="text-xs text-gray-muted">{selectedBatch.name}</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isLabelingComplete ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isLabelingComplete ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">2</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Labeling Progress</div>
                          <div className="text-xs text-gray-muted">{labelingProgress}% complete ({selectedBatch.labeledRecords ?? 0}/{selectedBatch.totalRecords ?? 0} records)</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isTargetComplete ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isTargetComplete ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">3</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Target Variable</div>
                          <div className="text-xs text-gray-muted">{targetColumn || 'Not set'}</div>
                          <div className="text-xs text-gray-muted mt-1">Split: {((1-trainTestSplit)*100).toFixed(0)}% train / {(trainTestSplit*100).toFixed(0)}% test {stratifyEnabled && '(stratified)'}</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isFeaturesComplete ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isFeaturesComplete ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">4</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Feature Engineering</div>
                          <div className="text-xs text-gray-muted">{selectedFeatures.length > 0 ? `${selectedFeatures.length} features selected` : 'Not configured'}</div>
                          <div className="text-xs text-gray-muted mt-1">Scaling: {scalingMethod}</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isValidationComplete ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isValidationComplete ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">5</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Validation Status</div>
                          <div className="text-xs text-gray-muted">
                            {validationResults 
                              ? `${validationResults.passed}/${validationResults.total_checks} checks passed`
                              : 'Not run yet'}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white/80 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isReadyForTraining ? 'bg-green-600' : 'bg-gray-300'
                        }`}>
                          {isReadyForTraining ? <CheckCircle className="w-4 h-4 text-white" /> : <span className="text-xs text-white font-bold">6</span>}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-black-text mb-1">Ready for Training</div>
                          <div className={`text-xs font-semibold ${
                            isReadyForTraining ? 'text-green-600' : 'text-amber-600'
                          }`}>
                            {isReadyForTraining ? 'All checks passed ✓' : 'Complete all steps'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-blue-600">
                        <span className="font-semibold">Keyboard Shortcut:</span> Press <kbd className="px-1.5 py-0.5 bg-white border border-blue-300 rounded text-xs font-mono">Enter</kbd> to advance to the next tab when current step is complete.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-6">
                  {/* Dataset Overview */}
                  <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6">
                    <h3 className="font-syne text-lg font-bold text-black-text mb-4">Dataset Overview</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Dataset Name</span>
                        <span className="text-sm font-semibold text-black-text">{selectedBatch.name}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Batch ID</span>
                        <span className="text-sm font-mono text-black-text">{selectedBatch.id}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Total Samples</span>
                        <span className="text-sm font-semibold text-purple-primary">{selectedBatch.totalRecords}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Selected Features</span>
                        <span className="text-sm font-semibold text-black-text">{selectedFeatures.length || selectedBatch.features}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Target Column</span>
                        <span className="text-sm font-semibold text-purple-primary">{targetColumn || 'Not set'}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Train/Test Split</span>
                        <span className="text-sm font-semibold text-black-text">{((1-trainTestSplit)*100).toFixed(0)}/{(trainTestSplit*100).toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b border-white/40">
                        <span className="text-sm text-gray-muted">Labeled Records</span>
                        <span className="text-sm font-semibold text-green">{selectedBatch.labeledRecords ?? 0}</span>
                      </div>
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-gray-muted">Status</span>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${(statusConfig[selectedBatch.status] || statusConfig.default).bg} ${(statusConfig[selectedBatch.status] || statusConfig.default).text}`}>
                          {(statusConfig[selectedBatch.status] || statusConfig.default).label}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Quality Score */}
                  <div className="bg-gradient-to-br from-purple-50 to-purple-50/50 border border-purple-200 rounded-2xl p-6">
                    <h3 className="font-syne text-lg font-bold text-purple-primary mb-4">Data Quality Score</h3>
                    <div className="flex items-center justify-center mb-6">
                      <div className="relative">
                        <div className="w-32 h-32 rounded-full flex items-center justify-center bg-white border-8 border-purple-primary">
                          <div className="text-center">
                            <div className="font-syne text-3xl font-bold text-purple-primary">
                              {validationResults 
                                ? ((validationResults.passed / validationResults.total_checks) * 100).toFixed(0)
                                : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-muted">out of 100</div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-muted">Validation Status</span>
                        <span className={`font-semibold ${
                          validationResults?.errors > 0 ? 'text-red-600' :
                          validationResults?.warnings > 0 ? 'text-amber' : 'text-green'
                        }`}>
                          {validationResults 
                            ? validationResults.errors > 0 ? 'Has Errors' : validationResults.warnings > 0 ? 'Has Warnings' : 'Passed'
                            : 'Not Run'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-muted">Labeling Completeness</span>
                        <span className={`font-semibold ${parseFloat(labelingProgress) >= 80 ? 'text-green' : 'text-amber'}`}>
                          {labelingProgress}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-muted">Target Set</span>
                        <span className={`font-semibold ${targetColumn ? 'text-green' : 'text-red-600'}`}>
                          {targetColumn ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-muted">Features Selected</span>
                        <span className={`font-semibold ${selectedFeatures.length > 0 ? 'text-green' : 'text-red-600'}`}>
                          {selectedFeatures.length > 0 ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-muted">Ready for Training</span>
                        <span className={`font-semibold ${isReadyForTraining ? 'text-green' : 'text-red-600'}`}>
                          {isReadyForTraining ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex items-center justify-between mt-8 p-6 bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl">
                  <div>
                    <h4 className="font-semibold text-black-text mb-1">Ready to proceed?</h4>
                    <p className="text-sm text-gray-muted">
                      {isReadyForTraining 
                        ? 'All checks passed! You can now proceed to model training.'
                        : 'Complete all preparation steps before training.'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setActiveTab('upload')}
                      className="flex items-center gap-2 px-6 py-3 rounded-lg border-2 border-gray-300 text-gray-700 hover:bg-gray-50 font-medium transition-all"
                    >
                      <ArrowLeft className="w-4 h-4" />
                      Back to Edit
                    </button>
                    
                    <button
                      onClick={handleProceedToTraining}
                      disabled={!isReadyForTraining || loading}
                      className="flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-primary text-white hover:shadow-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Saving & Proceeding...' : 'Proceed to Training'}
                      <Play className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        </>
        )}
        {/* End of Workflow View */}
        
      </div>
    </DashboardLayout>
  );
}
