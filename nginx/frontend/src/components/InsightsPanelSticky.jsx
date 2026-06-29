/**
 * Insights Panel - Phase 3 (The Differentiator!)
 * AI-driven recommendations and next best actions
 * Sticky on the right side of dashboard
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Sparkles, AlertTriangle, CheckCircle, Info, 
  ArrowRight, Zap, TrendingUp, Brain 
} from 'lucide-react';
import axios from 'axios';

export default function InsightsPanelSticky() {
  const navigate = useNavigate();
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights();
    // Refresh insights every 30 seconds
    const interval = setInterval(fetchInsights, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchInsights = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('http://localhost:8000/api/v1/ml/insights', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInsights(response.data);
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="sticky top-6 bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-2/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (!insights) return null;

  const getSystemHealthColor = () => {
    if (insights.system_health === 'healthy') return 'bg-green-100 text-green-700';
    if (insights.system_health === 'warning') return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'critical') return <AlertTriangle className="w-4 h-4 text-red-500" />;
    if (severity === 'error') return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    if (severity === 'warning') return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    return <Info className="w-4 h-4 text-blue-500" />;
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      high: 'bg-red-100 text-red-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700'
    };
    return colors[priority] || colors.medium;
  };

  return (
    <div className="sticky top-6 bg-gradient-to-br from-purple-50 to-white rounded-xl border border-purple-200 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 bg-gradient-to-r from-purple-600 to-purple-700 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-syne text-lg font-bold">System Insights</h3>
            <p className="text-xs text-purple-100">AI-powered recommendations</p>
          </div>
        </div>
        
        {/* System Health Badge */}
        <div className="flex items-center gap-2 mt-3">
          <span className="text-xs text-purple-100">System Health:</span>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getSystemHealthColor()}`}>
            {insights.system_health.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Warnings Section */}
      {insights.warnings && insights.warnings.length > 0 && (
        <div className="px-5 py-4 border-b border-purple-100">
          <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            Attention Required
          </h4>
          <div className="space-y-2">
            {insights.warnings.map((warning, idx) => (
              <div
                key={idx}
                className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
              >
                <div className="flex items-start gap-2">
                  {getSeverityIcon(warning.severity)}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-900">{warning.message}</p>
                    {warning.recommendation && (
                      <p className="text-xs text-gray-600 mt-1">→ {warning.recommendation}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights Section */}
      {insights.insights && insights.insights.length > 0 && (
        <div className="px-5 py-4 border-b border-purple-100">
          <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-500" />
            Key Insights
          </h4>
          <div className="space-y-2">
            {insights.insights.map((insight, idx) => (
              <div
                key={idx}
                className="bg-purple-50 rounded-lg p-3 border border-purple-100"
              >
                <div className="flex items-start gap-2">
                  {insight.type === 'success' && <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />}
                  {insight.type === 'info' && <Info className="w-4 h-4 text-blue-500 mt-0.5" />}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-900">{insight.message}</p>
                    {insight.recommendation && (
                      <p className="text-xs text-gray-600 mt-1">→ {insight.recommendation}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Best Actions */}
      {insights.next_actions && insights.next_actions.length > 0 && (
        <div className="px-5 py-4">
          <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-purple-600" />
            Recommended Next Steps
          </h4>
          <div className="space-y-2">
            {insights.next_actions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => navigate(action.route)}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-lg p-3 transition-all hover:shadow-lg group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getPriorityBadge(action.priority)}`}>
                      {action.priority?.toUpperCase()}
                    </span>
                    <span className="text-sm font-medium">{action.action}</span>
                  </div>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <div className="text-xs text-gray-500">Datasets</div>
            <div className="text-lg font-bold text-gray-900">{insights.summary.total_datasets}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Labeled</div>
            <div className="text-lg font-bold text-gray-900">{insights.summary.labeled_records}</div>
          </div>
        </div>
      </div>

      {/* Last Updated */}
      <div className="px-5 py-2 bg-purple-50 text-center">
        <p className="text-[10px] text-gray-500">
          Updated: {new Date(insights.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
