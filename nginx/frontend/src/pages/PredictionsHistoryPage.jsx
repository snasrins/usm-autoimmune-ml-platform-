/**
 * Predictions History Page
 * View and download all past batch predictions
 */
import { useState, useEffect } from 'react';
import { Download, Calendar, FileText, Brain, Clock, User, Database, RefreshCw, Search } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { predictionHistoryAPI } from '../services/api-complete';

export default function PredictionsHistoryPage() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [downloading, setDownloading] = useState(null);

  // Load predictions on mount
  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const response = await predictionHistoryAPI.getHistory(100);
      console.log('[PredictionsHistory] Loaded predictions:', response);
      setPredictions(response.predictions || []);
    } catch (error) {
      console.error('[PredictionsHistory] Error loading predictions:', error);
      setPredictions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (prediction) => {
    try {
      setDownloading(prediction.batch_id);
      console.log('[PredictionsHistory] Downloading:', prediction);
      
      const blob = await predictionHistoryAPI.downloadResults(
        prediction.batch_id,
        prediction.minio_path
      );
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `predictions_${prediction.batch_id}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('[PredictionsHistory] Download complete');
    } catch (error) {
      console.error('[PredictionsHistory] Download failed:', error);
      alert('Failed to download predictions: ' + error.message);
    } finally {
      setDownloading(null);
    }
  };

  // Filter predictions by search query
  const filteredPredictions = predictions.filter(pred => 
    pred.model_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    pred.batch_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    pred.predicted_by.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col" style={{ zoom: 0.75 }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white/60 backdrop-blur-sm border-b border-white/20">
          <div>
            <h1 className="font-syne text-lg font-bold text-black-text">Predictions History</h1>
            <p className="text-xs text-gray-muted mt-0.5">
              View and download all batch predictions
            </p>
          </div>
          <button
            onClick={fetchPredictions}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Stats Bar */}
        <div className="px-6 py-4 bg-white/40 backdrop-blur-sm border-b border-white/20">
          <div className="max-w-7xl mx-auto grid grid-cols-4 gap-4">
            <StatCard icon={FileText} label="Total Predictions" value={predictions.length} color="purple" />
            <StatCard 
              icon={Brain} 
              label="Unique Models" 
              value={new Set(predictions.map(p => p.model_name)).size} 
              color="blue" 
            />
            <StatCard 
              icon={Database} 
              label="Total Records" 
              value={predictions.reduce((sum, p) => sum + (p.total_predictions || 0), 0)} 
              color="green" 
            />
            <StatCard 
              icon={User} 
              label="Contributors" 
              value={new Set(predictions.map(p => p.predicted_by)).size} 
              color="amber" 
            />
          </div>
        </div>

        {/* Search Bar */}
        <div className="px-6 py-4 bg-white/40 backdrop-blur-sm border-b border-white/20">
          <div className="max-w-7xl mx-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by model name, batch ID, or user..."
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-primary/20 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {loading ? (
              <div className="text-center py-12">
                <div className="w-12 h-12 border-4 border-purple-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-sm text-gray-muted">Loading predictions...</p>
              </div>
            ) : filteredPredictions.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-gray-muted/40 mx-auto mb-4" />
                <h3 className="font-syne text-lg font-bold text-black-text mb-2">
                  {searchQuery ? 'No predictions found' : 'No predictions yet'}
                </h3>
                <p className="text-sm text-gray-muted max-w-md mx-auto">
                  {searchQuery 
                    ? 'Try adjusting your search query' 
                    : 'Run batch predictions to see them here'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredPredictions.map((prediction) => (
                  <PredictionCard
                    key={prediction.batch_id}
                    prediction={prediction}
                    onDownload={handleDownload}
                    isDownloading={downloading === prediction.batch_id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Stat Card Component
function StatCard({ icon: Icon, label, value, color }) {
  const colorClasses = {
    purple: 'text-purple-primary bg-purple-dim',
    blue: 'text-blue-500 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    amber: 'text-amber-600 bg-amber-50'
  };

  return (
    <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-white/40">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold text-black-text">{value}</div>
          <div className="text-xs text-gray-muted">{label}</div>
        </div>
      </div>
    </div>
  );
}

// Prediction Card Component
function PredictionCard({ prediction, onDownload, isDownloading }) {
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-white/60 hover:border-purple-primary/50 transition-all">
      <div className="flex items-start justify-between">
        {/* Left: Info */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-purple-dim">
              <Brain className="w-5 h-5 text-purple-primary" />
            </div>
            <div>
              <h3 className="font-syne font-bold text-sm text-black-text">
                {prediction.model_name}
                <span className="ml-2 text-xs font-normal text-gray-muted">v{prediction.model_version}</span>
              </h3>
              <p className="text-xs text-gray-muted">Batch ID: {prediction.batch_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 text-xs">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-gray-muted" />
              <div>
                <div className="text-gray-muted">Predictions</div>
                <div className="font-medium text-black-text">{prediction.total_predictions || 0}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-gray-muted" />
              <div>
                <div className="text-gray-muted">Date</div>
                <div className="font-medium text-black-text">{formatDate(prediction.predicted_at)}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <User className="w-3.5 h-3.5 text-gray-muted" />
              <div>
                <div className="text-gray-muted">User</div>
                <div className="font-medium text-black-text">{prediction.predicted_by}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-gray-muted" />
              <div>
                <div className="text-gray-muted">Size</div>
                <div className="font-medium text-black-text">{formatFileSize(prediction.size_bytes)}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Download Button */}
        <button
          onClick={() => onDownload(prediction)}
          disabled={isDownloading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-primary text-white hover:bg-purple-primary/90 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isDownloading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Downloading...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Download CSV
            </>
          )}
        </button>
      </div>
    </div>
  );
}
