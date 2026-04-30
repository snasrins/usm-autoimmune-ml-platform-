import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  Filter,
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  Clock,
  Brain,
  TrendingUp,
  Target,
  Activity,
  Download,
  Eye,
  BarChart3,
  Gauge,
  Zap,
  Shield
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function PatientClassifierPage() {
  const navigate = useNavigate();
  const [selectedPatients, setSelectedPatients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [classificationMode, setClassificationMode] = useState('single'); // 'single' or 'batch'

  // Mock patient data
  const patients = [
    { 
      id: 'PAT-2341', 
      name: 'Sarah Chen', 
      age: 34, 
      gender: 'F', 
      status: 'classified',
      prediction: 'SLE',
      confidence: 94.2,
      riskScore: 'High',
      lastUpdated: '2024-04-08 14:23',
      biomarkers: { ANA: 'Positive', dsDNA: 'High', C3: 'Low', C4: 'Low' }
    },
    { 
      id: 'PAT-2340', 
      name: 'Michael Torres', 
      age: 42, 
      gender: 'M', 
      status: 'classified',
      prediction: 'Rheumatoid Arthritis',
      confidence: 87.5,
      riskScore: 'Moderate',
      lastUpdated: '2024-04-08 13:15',
      biomarkers: { RF: 'Positive', CCP: 'High', ESR: 'Elevated', CRP: 'High' }
    },
    { 
      id: 'PAT-2339', 
      name: 'Jennifer Lopez', 
      age: 29, 
      gender: 'F', 
      status: 'pending',
      prediction: null,
      confidence: null,
      riskScore: null,
      lastUpdated: '2024-04-08 12:40',
      biomarkers: { ANA: 'Pending', RF: 'Negative' }
    },
    { 
      id: 'PAT-2338', 
      name: 'David Kim', 
      age: 51, 
      gender: 'M', 
      status: 'classified',
      prediction: 'Sjögren Syndrome',
      confidence: 91.3,
      riskScore: 'High',
      lastUpdated: '2024-04-08 11:22',
      biomarkers: { SSA: 'Positive', SSB: 'Positive', RF: 'Positive' }
    },
    { 
      id: 'PAT-2337', 
      name: 'Emily Watson', 
      age: 38, 
      gender: 'F', 
      status: 'review',
      prediction: 'Uncertain - Mixed Connective Tissue Disease',
      confidence: 72.8,
      riskScore: 'Moderate',
      lastUpdated: '2024-04-08 10:15',
      biomarkers: { ANA: 'Positive', RNP: 'High', Sm: 'Negative' }
    }
  ];

  const filteredPatients = patients.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         p.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || p.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const statusColors = {
    classified: { bg: 'bg-green-dim', text: 'text-green', border: 'border-green/20' },
    pending: { bg: 'bg-amber-dim', text: 'text-amber', border: 'border-amber/20' },
    review: { bg: 'bg-purple-dim', text: 'text-purple-primary', border: 'border-purple-primary/20' }
  };

  const riskColors = {
    High: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' },
    Moderate: { bg: 'bg-amber-dim', text: 'text-amber', border: 'border-amber/20' },
    Low: { bg: 'bg-green-dim', text: 'text-green', border: 'border-green/20' }
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-syne text-2xl font-bold text-black-text">Patient Classifier</h1>
                  <p className="text-xs text-gray-muted">AI-powered autoimmune disease classification</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/40 bg-white/80 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <Download className="w-4 h-4" />
                  Export Results
                </button>
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all text-sm font-medium">
                  <Upload className="w-4 h-4" />
                  Upload Patient Data
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mt-4">
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Total Patients</span>
                  <Users className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">1,847</div>
                <div className="text-xs text-gray-muted mt-1">+23 this week</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Classified</span>
                  <CheckCircle className="w-4 h-4 text-green" />
                </div>
                <div className="font-syne text-2xl font-bold text-green">1,652</div>
                <div className="text-xs text-gray-muted mt-1">89.4% of total</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Avg Confidence</span>
                  <Target className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-purple-primary">91.8%</div>
                <div className="text-xs text-gray-muted mt-1">+2.3% vs last month</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">High Risk</span>
                  <AlertCircle className="w-4 h-4 text-red-600" />
                </div>
                <div className="font-syne text-2xl font-bold text-red-600">247</div>
                <div className="text-xs text-gray-muted mt-1">Require attention</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Classification Mode Selector */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <h3 className="font-syne text-base font-bold text-black-text mb-4">Classification Mode</h3>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setClassificationMode('single')}
                  className={`flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                    classificationMode === 'single'
                      ? 'border-purple-primary bg-purple-dim'
                      : 'border-white/40 bg-white/60 hover:border-purple-primary/40'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    classificationMode === 'single' ? 'bg-purple-primary' : 'bg-gray-200'
                  }`}>
                    <FileText className={`w-5 h-5 ${classificationMode === 'single' ? 'text-white' : 'text-gray-muted'}`} />
                  </div>
                  <div className="flex-1 text-left">
                    <h4 className="font-semibold text-sm text-black-text mb-1">Single Patient</h4>
                    <p className="text-xs text-gray-muted">Classify individual patient with detailed analysis and biomarker interpretation</p>
                  </div>
                </button>
                <button
                  onClick={() => setClassificationMode('batch')}
                  className={`flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                    classificationMode === 'batch'
                      ? 'border-purple-primary bg-purple-dim'
                      : 'border-white/40 bg-white/60 hover:border-purple-primary/40'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    classificationMode === 'batch' ? 'bg-purple-primary' : 'bg-gray-200'
                  }`}>
                    <Users className={`w-5 h-5 ${classificationMode === 'batch' ? 'text-white' : 'text-gray-muted'}`} />
                  </div>
                  <div className="flex-1 text-left">
                    <h4 className="font-semibold text-sm text-black-text mb-1">Batch Processing</h4>
                    <p className="text-xs text-gray-muted">Upload CSV file to classify multiple patients at once with automated report generation</p>
                  </div>
                </button>
              </div>
            </div>

            {/* Filters & Search */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-5">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by patient ID or name..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary focus:ring-2 focus:ring-purple-primary/20"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 text-sm focus:outline-none focus:border-purple-primary"
                >
                  <option value="all">All Status</option>
                  <option value="classified">Classified</option>
                  <option value="pending">Pending</option>
                  <option value="review">Needs Review</option>
                </select>
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/40 bg-white/90 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <Filter className="w-4 h-4" />
                  More Filters
                </button>
              </div>
            </div>

            {/* Patient List */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                <div className="flex items-center justify-between">
                  <h3 className="font-syne text-base font-bold text-black-text">Recent Classifications</h3>
                  <span className="text-xs text-gray-muted">{filteredPatients.length} patients</span>
                </div>
              </div>
              <div className="divide-y divide-white/20">
                {filteredPatients.map((patient) => {
                  const statusStyle = statusColors[patient.status];
                  const riskStyle = patient.riskScore ? riskColors[patient.riskScore] : null;
                  
                  return (
                    <div key={patient.id} className="p-5 hover:bg-white/40 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 rounded-full bg-purple-dim flex items-center justify-center flex-shrink-0">
                            <span className="font-syne text-base font-bold text-purple-primary">
                              {patient.name.split(' ').map(n => n[0]).join('')}
                            </span>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-sm text-black-text">{patient.name}</h4>
                              <span className="text-xs text-gray-muted">• {patient.id}</span>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-gray-muted">
                              <span>{patient.age}y • {patient.gender === 'M' ? 'Male' : 'Female'}</span>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {patient.lastUpdated}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                            {patient.status.toUpperCase()}
                          </span>
                          {patient.riskScore && (
                            <span className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${riskStyle.bg} ${riskStyle.text} ${riskStyle.border}`}>
                              {patient.riskScore} Risk
                            </span>
                          )}
                        </div>
                      </div>

                      {patient.prediction && (
                        <div className="bg-gradient-to-br from-purple-50 to-purple-50/50 border border-purple-200 rounded-xl p-4 mb-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Brain className="w-4 h-4 text-purple-primary" />
                              <span className="text-xs font-semibold text-purple-primary uppercase">Classification Result</span>
                            </div>
                            {patient.confidence && (
                              <div className="flex items-center gap-2">
                                <Gauge className="w-4 h-4 text-purple-primary" />
                                <span className="text-xs font-bold text-purple-primary">{patient.confidence}% Confidence</span>
                              </div>
                            )}
                          </div>
                          <div className="font-syne text-base font-bold text-purple-primary">{patient.prediction}</div>
                        </div>
                      )}

                      {/* Biomarkers */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-medium text-gray-muted">Biomarkers:</span>
                          {Object.entries(patient.biomarkers).map(([key, value]) => (
                            <span key={key} className="px-2 py-1 rounded bg-white/80 border border-white/40 text-xs">
                              <span className="font-semibold text-black-text">{key}:</span>{' '}
                              <span className="text-gray-muted">{value}</span>
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center gap-2">
                          <button className="p-2 rounded-lg border border-white/40 hover:bg-white text-purple-primary hover:border-purple-primary/40 transition-all">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="p-2 rounded-lg border border-white/40 hover:bg-white text-purple-primary hover:border-purple-primary/40 transition-all">
                            <BarChart3 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
