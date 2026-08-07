import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { authAPI, dashboardAPI } from '../services/api';
import DashboardLayout from '../components/DashboardLayout';
import {
  ArrowRight,
  Upload,
  Tag,
  Target,
  Settings as SettingsIcon,
  Layers,
  Filter,
  CheckSquare,
  Package,
  Play,
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronRight,
  Zap,
  TrendingUp,
  Activity,
  BarChart3,
  Brain,
  Database,
  Users,
  Sparkles,
  Award,
  Calendar,
  Search,
  X
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);

  const [stats, setStats] = useState({
    totalDatasets: 0,
    totalRecords: 0,
    labeledPercent: 0,
    trainingJobs: 0,
    modelsDeployed: 0,
    unlabeledRecords: 0,
    dataQuality: 0,
    modelAccuracy: 0,
    activeUsers: 0
  });

  const [pipelineStatus, setPipelineStatus] = useState({
    upload: { complete: false, count: 0 },
    labeling: { complete: false, progress: 0 },
    preprocessing: { complete: false },
    training: { active: false, running: 0 }
  });

  const [nextAction, setNextAction] = useState({
    title: 'Upload your first dataset',
    description: 'Start by uploading patient data to begin the ML pipeline',
    action: 'Upload Dataset',
    route: '/data-preparation',
    priority: 'high',
    icon: Upload
  });

  // Search data for all pages/tabs
  const searchablePages = [
    { title: 'Dashboard', route: '/dashboard', keywords: ['home', 'overview', 'stats', 'metrics'] },
    { title: 'Data Catalog', route: '/data-catalog', keywords: ['upload', 'data', 'import', 'files', 'datasets'] },
    { title: 'Data Preparation', route: '/data-preparation', keywords: ['prep', 'preprocessing', 'labeling', 'label', 'transform'] },
    { title: 'Data Quality', route: '/data-quality', keywords: ['quality', 'validation', 'checks', 'completeness'] },
    { title: 'Training Jobs', route: '/training', keywords: ['train', 'model', 'ml', 'machine learning', 'algorithms'] },
    { title: 'Model Comparison', route: '/models', keywords: ['models', 'compare', 'performance', 'metrics', 'accuracy'] },
    { title: 'Predictions', route: '/predictions', keywords: ['predict', 'inference', 'forecast', 'test'] },
    { title: 'Batch Prediction', route: '/batch-prediction', keywords: ['batch', 'bulk', 'multiple predictions'] },
    { title: 'Explainability (SHAP)', route: '/explainability', keywords: ['shap', 'explain', 'interpret', 'why', 'feature importance'] },
    { title: 'Settings', route: '/settings', keywords: ['settings', 'config', 'preferences', 'account'] },
    { title: 'API Keys', route: '/api-keys', keywords: ['api', 'keys', 'authentication', 'tokens'] },
    { title: 'Users', route: '/users', keywords: ['users', 'admin', 'accounts', 'permissions'] },
  ];

  // Mock data for charts (replace with real API data)
  const [trainingHistory, setTrainingHistory] = useState([
    { month: 'Jan', accuracy: 0.78, loss: 0.45 },
    { month: 'Feb', accuracy: 0.82, loss: 0.38 },
    { month: 'Mar', accuracy: 0.85, loss: 0.32 },
    { month: 'Apr', accuracy: 0.88, loss: 0.28 },
    { month: 'May', accuracy: 0.91, loss: 0.22 },
    { month: 'Jun', accuracy: 0.93, loss: 0.18 }
  ]);

  const [weeklyActivity, setWeeklyActivity] = useState([
    { day: 'Mon', uploads: 12, training: 8 },
    { day: 'Tue', uploads: 15, training: 10 },
    { day: 'Wed', uploads: 8, training: 12 },
    { day: 'Thu', uploads: 18, training: 15 },
    { day: 'Fri', uploads: 22, training: 18 },
    { day: 'Sat', uploads: 10, training: 8 },
    { day: 'Sun', uploads: 5, training: 3 }
  ]);

  const [recentModels, setRecentModels] = useState([
    { name: 'XGBoost SLE', accuracy: 0.94, auc: 0.96, date: '2h ago', status: 'completed' },
    { name: 'Random Forest RA', accuracy: 0.91, auc: 0.93, date: '5h ago', status: 'completed' },
    { name: 'LightGBM Lupus', accuracy: 0.89, auc: 0.91, date: '1d ago', status: 'completed' }
  ]);

  useEffect(() => {
    loadData();
    
    // Keyboard shortcut for search (Cmd+K or Ctrl+K)
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowSearch(prev => !prev);
      }
      if (e.key === 'Escape') {
        setShowSearch(false);
        setSearchQuery('');
        setSearchResults([]);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const loadData = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      
      const dashboardData = await dashboardAPI.getAllStats({
        includeAdminStats: Boolean(userData?.is_superuser)
      });
      
      const uploadsData = dashboardData.uploads;
      const labelingData = dashboardData.labeling;
      const trainingData = dashboardData.training;
      const modelsData = dashboardData.models;
      
      // Debug: Log the data to see what we're getting
      console.log('Dashboard Data:', { uploadsData, labelingData, trainingData, modelsData });
      
      const totalDatasets = uploadsData.total || 0;
      const totalRecords = labelingData.total || 0;
      const labeledCount = labelingData.labeled_count || 0;
      const unlabeledCount = labelingData.unlabeled_count || 0;
      const labeledPercent = totalRecords > 0 ? (labeledCount / totalRecords) * 100 : 0;
      
      const runningJobs = trainingData.jobs?.filter(j => j.status === 'running').length || 0;
      const queuedJobs = trainingData.jobs?.filter(j => j.status === 'queued').length || 0;
      
      // Calculate average model accuracy from completed models
      const completedModels = modelsData.models?.filter(m => m.metrics?.accuracy) || [];
      const avgAccuracy = completedModels.length > 0
        ? completedModels.reduce((sum, m) => sum + m.metrics.accuracy, 0) / completedModels.length
        : 0;
      
      // Calculate data quality score dynamically
      // Based on: labeled percentage (70%), preprocessing completeness (30%)
      const dataQualityScore = Math.min(100, Math.round(
        (labeledPercent * 0.7) + 
        (totalDatasets > 0 ? 30 : 0)
      ));
      
      setStats({
        totalDatasets,
        totalRecords,
        labeledPercent: Math.round(labeledPercent),
        trainingJobs: runningJobs + queuedJobs,
        modelsDeployed: modelsData.total_count || 0,
        unlabeledRecords: unlabeledCount,
        dataQuality: dataQualityScore,
        modelAccuracy: Math.round(avgAccuracy * 100),
        activeUsers: dashboardData.platform?.users?.active_count || 0
      });

      setPipelineStatus({
        upload: { complete: totalDatasets > 0, count: totalDatasets },
        labeling: { complete: labeledPercent >= 80, progress: labeledPercent },
        preprocessing: { complete: false },
        training: { active: runningJobs > 0, running: runningJobs }
      });

      determineNextAction(totalDatasets, labeledPercent, unlabeledCount, runningJobs, modelsData.total_count);

      // Load recent models for display
      if (completedModels.length > 0) {
        setRecentModels(completedModels.slice(0, 3).map(m => ({
          name: `${m.algorithm_name} ${m.dataset_name || ''}`,
          accuracy: m.metrics?.accuracy || 0,
          auc: m.metrics?.auc_roc || 0,
          date: new Date(m.created_at).toLocaleString(),
          status: 'completed'
        })));
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const determineNextAction = (datasets, labeledPct, unlabeled, training, models) => {
    if (datasets === 0) {
      setNextAction({
        title: 'Upload your first dataset',
        description: 'Start by uploading patient data (CSV/Excel) to begin the ML pipeline',
        action: 'Upload Dataset',
        route: '/data-preparation',
        priority: 'high',
        icon: Upload
      });
    } else if (labeledPct < 50) {
      setNextAction({
        title: `Label ${unlabeled} unlabeled records`,
        description: `You have ${labeledPct}% labeled. Aim for 80%+ before training`,
        action: 'Start Labeling',
        route: '/data-preparation?tab=labeling',
        priority: 'high',
        icon: Tag
      });
    } else if (labeledPct >= 50 && training === 0 && models === 0) {
      setNextAction({
        title: 'Ready to train your first model',
        description: `${labeledPct}% labeled - good coverage! Start training now`,
        action: 'Start Training',
        route: '/training',
        priority: 'high',
        icon: Play
      });
    } else if (training > 0) {
      setNextAction({
        title: `${training} model(s) training`,
        description: 'Training in progress. Monitor performance and compare models',
        action: 'View Training',
        route: '/training',
        priority: 'medium',
        icon: Activity
      });
    } else {
      setNextAction({
        title: 'Explore model performance',
        description: `${models} trained models ready. Compare results and deploy the best`,
        action: 'View Models',
        route: '/models',
        priority: 'low',
        icon: Brain
      });
    }
  };
  // Search handler
  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.trim() === '') {
      setSearchResults([]);
      return;
    }

    const lowerQuery = query.toLowerCase();
    const results = searchablePages.filter(page => 
      page.title.toLowerCase().includes(lowerQuery) ||
      page.keywords.some(keyword => keyword.includes(lowerQuery))
    );
    setSearchResults(results);
  };

  const navigateToPage = (route) => {
    navigate(route);
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
  };
  // Circular Progress Component (inspired by fitness app)
  const CircularProgress = ({ percentage, size = 120, strokeWidth = 8, color = 'purple' }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    const colorMap = {
      purple: { from: '#9333ea', to: '#7c3aed', glow: 'rgba(147, 51, 234, 0.2)' },
      green: { from: '#10b981', to: '#059669', glow: 'rgba(16, 185, 129, 0.2)' },
      amber: { from: '#f59e0b', to: '#d97706', glow: 'rgba(245, 158, 11, 0.2)' }
    };

    const colors = colorMap[color] || colorMap.purple;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle with gradient */}
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colors.from} />
              <stop offset="100%" stopColor={colors.to} />
            </linearGradient>
          </defs>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={`url(#gradient-${color})`}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 8px ${colors.glow})` }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{percentage}%</div>
            <div className="text-xs text-gray-500">Complete</div>
          </div>
        </div>
      </div>
    );
  };

  // Mini Area Chart Component (sparkline)
  const MiniAreaChart = ({ data, color = 'purple', height = 60 }) => {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const width = 200;
    const padding = 4;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - padding * 2) - padding;
      return `${x},${y}`;
    }).join(' ');

    const areaPoints = `0,${height} ${points} ${width},${height}`;

    const colorMap = {
      purple: { stroke: '#9333ea', fill: 'rgba(147, 51, 234, 0.1)' },
      green: { stroke: '#10b981', fill: 'rgba(16, 185, 129, 0.1)' },
      amber: { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.1)' }
    };

    const colors = colorMap[color] || colorMap.purple;

    return (
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={`area-gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={colors.stroke} stopOpacity="0.3" />
            <stop offset="100%" stopColor={colors.stroke} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon
          points={areaPoints}
          fill={`url(#area-gradient-${color})`}
          className="transition-all duration-500"
        />
        <polyline
          points={points}
          fill="none"
          stroke={colors.stroke}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-500"
        />
      </svg>
    );
  };

  // Metric Card with Sparkline
  const MetricCard = ({ title, value, subtitle, trend, trendData, icon: Icon, color = 'purple', onClick }) => {
    const colorStyles = {
      purple: 'from-purple-50 to-purple-100 border-purple-200 text-purple-700',
      green: 'from-green-50 to-green-100 border-green-200 text-green-700',
      amber: 'from-amber-50 to-amber-100 border-amber-200 text-amber-700'
    };

    return (
      <motion.div
        whileHover={{ y: -4, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' }}
        onClick={onClick}
        className={`bg-gradient-to-br ${colorStyles[color]} border rounded-2xl p-6 cursor-pointer transition-all duration-200`}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-sm font-medium text-gray-600 mb-1">{title}</div>
            <div className="text-3xl font-bold text-gray-900">{value}</div>
            {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
          </div>
          <div className={`p-3 bg-white rounded-xl shadow-sm`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        
        {trendData && (
          <div className="mt-4">
            <MiniAreaChart data={trendData} color={color} />
          </div>
        )}
        
        {trend && (
          <div className={`flex items-center text-sm mt-3 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            <TrendingUp className={`w-4 h-4 mr-1 ${trend < 0 ? 'transform rotate-180' : ''}`} />
            <span className="font-medium">{Math.abs(trend)}%</span>
            <span className="text-gray-500 ml-1">vs last week</span>
          </div>
        )}
      </motion.div>
    );
  };

  // Model Performance Card
  const ModelCard = ({ model }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-lg transition-all duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">{model.name}</h4>
          <p className="text-xs text-gray-500">{model.date}</p>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          model.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
        }`}>
          {model.status}
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs text-gray-500 mb-1">Accuracy</div>
          <div className="text-lg font-bold text-gray-900">{(model.accuracy * 100).toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">AUC-ROC</div>
          <div className="text-lg font-bold text-gray-900">{(model.auc * 100).toFixed(1)}%</div>
        </div>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-[1600px] mx-auto px-8 py-6">
        
        {/* Header with Search */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, {user?.full_name || 'Researcher'}
              </h1>
              <p className="text-gray-600">Here's what's happening with your ML platform today</p>
            </div>
            
            {/* Search Button */}
            <div className="relative">
              {!showSearch ? (
                <button
                  onClick={() => setShowSearch(true)}
                  className="flex items-center space-x-2 px-4 py-2.5 bg-white border border-gray-200 rounded-xl hover:border-purple-300 hover:shadow-md transition-all duration-200"
                >
                  <Search className="w-5 h-5 text-gray-500" />
                  <span className="text-sm text-gray-600">Search pages...</span>
                  <kbd className="px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-200 rounded">⌘K</kbd>
                </button>
              ) : (
                <>
                  {/* Backdrop */}
                  <div 
                    className="fixed inset-0 z-40 bg-black/20"
                    onClick={() => {
                      setShowSearch(false);
                      setSearchQuery('');
                      setSearchResults([]);
                    }}
                  />
                  
                  {/* Search Panel */}
                  <div className="absolute right-0 top-0 z-50 w-96 bg-white border border-gray-200 rounded-2xl shadow-2xl">
                  {/* Search Input */}
                  <div className="flex items-center p-4 border-b border-gray-200">
                    <Search className="w-5 h-5 text-gray-400 mr-3" />
                    <input
                      type="text"
                      placeholder="Search for pages, settings, or features..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      className="flex-1 outline-none text-sm"
                      autoFocus
                    />
                    <button
                      onClick={() => {
                        setShowSearch(false);
                        setSearchQuery('');
                        setSearchResults([]);
                      }}
                      className="ml-2 p-1 hover:bg-gray-100 rounded"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                  
                  {/* Search Results */}
                  <div className="max-h-96 overflow-y-auto">
                    {searchQuery === '' ? (
                      <div className="p-4 text-sm text-gray-500">
                        <p className="font-medium mb-2">Quick Access</p>
                        {searchablePages.slice(0, 6).map((page, i) => (
                          <button
                            key={i}
                            onClick={() => navigateToPage(page.route)}
                            className="w-full text-left px-3 py-2 hover:bg-purple-50 rounded-lg flex items-center justify-between group"
                          >
                            <span className="text-gray-700">{page.title}</span>
                            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600" />
                          </button>
                        ))}
                      </div>
                    ) : searchResults.length > 0 ? (
                      <div className="p-2">
                        {searchResults.map((result, i) => (
                          <button
                            key={i}
                            onClick={() => navigateToPage(result.route)}
                            className="w-full text-left px-4 py-3 hover:bg-purple-50 rounded-lg flex items-center justify-between group transition-colors"
                          >
                            <div>
                              <div className="font-medium text-gray-900">{result.title}</div>
                              <div className="text-xs text-gray-500 mt-0.5">{result.route}</div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600" />
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="p-8 text-center">
                        <div className="text-gray-400 mb-2">
                          <Search className="w-8 h-8 mx-auto" />
                        </div>
                        <p className="text-sm text-gray-500">No results found for "{searchQuery}"</p>
                      </div>
                    )}
                  </div>
                </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Next Action Hero Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-purple-600 via-purple-700 to-purple-800 rounded-3xl p-8 mb-8 shadow-xl relative overflow-hidden"
        >
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full -ml-24 -mb-24"></div>
          
          <div className="relative z-10 flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-3">
                {nextAction.icon && <nextAction.icon className="w-8 h-8 text-purple-200" />}
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-medium text-white">
                  {nextAction.priority === 'high' ? '🔥 Priority Action' : '💡 Recommended'}
                </span>
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">{nextAction.title}</h2>
              <p className="text-purple-100 text-lg mb-6">{nextAction.description}</p>
              <button
                onClick={() => navigate(nextAction.route)}
                className="bg-white text-purple-700 px-6 py-3 rounded-xl font-semibold hover:bg-purple-50 transition-colors duration-200 inline-flex items-center space-x-2 shadow-lg hover:shadow-xl"
              >
                <span>{nextAction.action}</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
            
            {/* Circular progress visualization */}
            <div className="ml-8 hidden lg:block">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
                <CircularProgress 
                  percentage={stats.labeledPercent} 
                  size={140}
                  strokeWidth={10}
                  color="purple"
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Datasets"
            value={stats.totalDatasets}
            subtitle={`${stats.totalRecords.toLocaleString()} records`}
            icon={Database}
            color="purple"
            trend={12}
            trendData={[10, 12, 11, 15, 18, 20, 22]}
            onClick={() => navigate('/data-catalog')}
          />
          
          <MetricCard
            title="Data Quality"
            value={`${stats.dataQuality}%`}
            subtitle="Across all datasets"
            icon={CheckSquare}
            color="green"
            trend={5}
            trendData={[75, 78, 80, 82, 83, 84, 85]}
            onClick={() => navigate('/data-quality')}
          />
          
          <MetricCard
            title="Active Training"
            value={stats.trainingJobs}
            subtitle="Jobs in progress"
            icon={Activity}
            color="amber"
            trendData={[2, 3, 5, 4, 6, 5, stats.trainingJobs]}
            onClick={() => navigate('/training')}
          />
          
          <MetricCard
            title="Models Deployed"
            value={stats.modelsDeployed}
            subtitle={`Avg ${stats.modelAccuracy}% accuracy`}
            icon={Brain}
            color="purple"
            trend={8}
            trendData={[5, 6, 7, 7, 8, 8, stats.modelsDeployed]}
            onClick={() => navigate('/models')}
          />
        </div>

        {/* Two Column Layout: Charts + Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Charts (2/3 width) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Model Performance Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Model Performance Trends</h3>
                  <p className="text-sm text-gray-500">Accuracy over time</p>
                </div>
                <button className="text-purple-600 text-sm font-medium hover:text-purple-700">
                  View All →
                </button>
              </div>
              
              {/* Area Chart */}
              <div className="relative h-64">
                <svg viewBox="0 0 600 200" className="w-full h-full">
                  <defs>
                    <linearGradient id="chart-gradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#9333ea" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#9333ea" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  
                  {/* Grid lines */}
                  {[0, 25, 50, 75, 100].map((y) => (
                    <line
                      key={y}
                      x1="0"
                      y1={200 - (y * 2)}
                      x2="600"
                      y2={200 - (y * 2)}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />
                  ))}
                  
                  {/* Area fill */}
                  <polygon
                    points={trainingHistory.map((point, i) => {
                      const x = (i / (trainingHistory.length - 1)) * 600;
                      const y = 200 - (point.accuracy * 200);
                      return `${x},${y}`;
                    }).join(' ') + ' 600,200 0,200'}
                    fill="url(#chart-gradient)"
                  />
                  
                  {/* Line */}
                  <polyline
                    points={trainingHistory.map((point, i) => {
                      const x = (i / (trainingHistory.length - 1)) * 600;
                      const y = 200 - (point.accuracy * 200);
                      return `${x},${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="#9333ea"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  
                  {/* Data points */}
                  {trainingHistory.map((point, i) => {
                    const x = (i / (trainingHistory.length - 1)) * 600;
                    const y = 200 - (point.accuracy * 200);
                    return (
                      <g key={i}>
                        <circle cx={x} cy={y} r="5" fill="#9333ea" stroke="white" strokeWidth="2" />
                      </g>
                    );
                  })}
                </svg>
                
                {/* X-axis labels */}
                <div className="flex justify-between mt-2">
                  {trainingHistory.map((point, i) => (
                    <span key={i} className="text-xs text-gray-500">{point.month}</span>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Weekly Activity Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Weekly Activity</h3>
                  <p className="text-sm text-gray-500">Uploads vs Training jobs</p>
                </div>
                <div className="flex items-center space-x-4 text-sm">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-purple-500 mr-2"></div>
                    <span className="text-gray-600">Uploads</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-purple-300 mr-2"></div>
                    <span className="text-gray-600">Training</span>
                  </div>
                </div>
              </div>
              
              {/* Bar Chart */}
              <div className="flex items-end justify-between h-48 space-x-4">
                {weeklyActivity.map((day, i) => {
                  const maxValue = Math.max(...weeklyActivity.map(d => Math.max(d.uploads, d.training)));
                  const uploadHeight = (day.uploads / maxValue) * 100;
                  const trainingHeight = (day.training / maxValue) * 100;
                  
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div className="w-full flex items-end justify-center space-x-1 mb-2">
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: `${uploadHeight}%` }}
                          transition={{ delay: i * 0.1, duration: 0.5 }}
                          className="w-full bg-gradient-to-t from-purple-500 to-purple-400 rounded-t-lg"
                          style={{ minHeight: '8px' }}
                        />
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: `${trainingHeight}%` }}
                          transition={{ delay: i * 0.1 + 0.05, duration: 0.5 }}
                          className="w-full bg-gradient-to-t from-purple-300 to-purple-200 rounded-t-lg"
                          style={{ minHeight: '8px' }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-2">{day.day}</span>
                    </div>
                  );
                })}
              </div>
            </motion.div>

          </div>

          {/* Right Column: Recent Models + Pipeline Status */}
          <div className="space-y-6">
            
            {/* Recent Models */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Recent Models</h3>
                <Award className="w-5 h-5 text-purple-600" />
              </div>
              
              <div className="space-y-3">
                {recentModels.map((model, i) => (
                  <ModelCard key={i} model={model} />
                ))}
              </div>
              
              <button
                onClick={() => navigate('/models')}
                className="w-full mt-4 text-center text-purple-600 text-sm font-medium hover:text-purple-700 py-2"
              >
                View all models →
              </button>
            </motion.div>

            {/* Pipeline Status */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
            >
              <h3 className="text-lg font-bold text-gray-900 mb-4">Pipeline Status</h3>
              
              <div className="space-y-4">
                {[
                  { label: 'Data Upload', status: pipelineStatus.upload.complete, count: pipelineStatus.upload.count, icon: Upload },
                  { label: 'Labeling', status: pipelineStatus.labeling.complete, progress: pipelineStatus.labeling.progress, icon: Tag },
                  { label: 'Preprocessing', status: pipelineStatus.preprocessing.complete, icon: SettingsIcon },
                  { label: 'Training', active: pipelineStatus.training.active, count: pipelineStatus.training.running, icon: Play }
                ].map((step, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        step.status ? 'bg-green-100' : step.active ? 'bg-purple-100' : 'bg-gray-100'
                      }`}>
                        <step.icon className={`w-4 h-4 ${
                          step.status ? 'text-green-600' : step.active ? 'text-purple-600' : 'text-gray-400'
                        }`} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{step.label}</div>
                        {step.progress !== undefined && (
                          <div className="text-xs text-gray-500">{step.progress}% complete</div>
                        )}
                        {step.count !== undefined && step.count > 0 && (
                          <div className="text-xs text-gray-500">{step.count} items</div>
                        )}
                      </div>
                    </div>
                    <div>
                      {step.status && <CheckCircle className="w-5 h-5 text-green-600" />}
                      {step.active && <Activity className="w-5 h-5 text-purple-600 animate-pulse" />}
                      {!step.status && !step.active && <Clock className="w-5 h-5 text-gray-400" />}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-2xl p-6"
            >
              <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
              
              <div className="space-y-2">
                {[
                  { label: 'Upload Dataset', icon: Upload, route: '/data-preparation' },
                  { label: 'Start Training', icon: Play, route: '/training' },
                  { label: 'View Models', icon: Brain, route: '/models' },
                  { label: 'Data Quality', icon: CheckSquare, route: '/data-quality' }
                ].map((action, i) => (
                  <button
                    key={i}
                    onClick={() => navigate(action.route)}
                    className="w-full flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-all duration-200 group"
                  >
                    <div className="flex items-center space-x-3">
                      <action.icon className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-gray-900">{action.label}</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 group-hover:translate-x-1 transition-all" />
                  </button>
                ))}
              </div>
            </motion.div>

          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
