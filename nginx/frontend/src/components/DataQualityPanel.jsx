/**
 * Data Quality Panel - Phase 3
 * Shows platform-wide data quality metrics
 */
import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, TrendingUp, Database, BarChart3 } from 'lucide-react';
import axios from 'axios';

export default function DataQualityPanel() {
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDataQuality();
  }, []);

  const fetchDataQuality = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('http://localhost:8000/api/v1/data-quality/summary', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuality(response.data);
    } catch (error) {
      console.error('Failed to fetch data quality:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (!quality) return null;

  const getQualityColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityBg = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-syne text-lg font-bold text-gray-900">Data Quality Overview</h3>
              <p className="text-xs text-gray-500">Platform-wide metrics</p>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full ${getQualityBg(quality.average_quality_score)}`}>
            <span className={`text-sm font-semibold ${getQualityColor(quality.average_quality_score)}`}>
              {quality.average_quality_score}% Quality
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-6 grid grid-cols-2 gap-4">
        {/* Total Datasets */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-medium text-gray-500">Total Datasets</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{quality.total_datasets}</div>
          <div className="text-xs text-gray-500 mt-1">
            {quality.datasets_by_status.ready} ready • {quality.datasets_by_status.processing} processing
          </div>
        </div>

        {/* Missing Values */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-yellow-500" />
            <span className="text-xs font-medium text-gray-500">Missing Values</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{quality.missing_values_percentage}%</div>
          <div className="text-xs text-gray-500 mt-1">
            {quality.missing_values_percentage < 10 ? 'Low' : quality.missing_values_percentage < 20 ? 'Medium' : 'High'}
          </div>
        </div>

        {/* Class Imbalance */}
        {quality.class_imbalance_ratio && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              <span className="text-xs font-medium text-gray-500">Class Imbalance</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{quality.class_imbalance_ratio}:1</div>
            <div className="text-xs text-gray-500 mt-1">
              {quality.class_imbalance_ratio > 3 ? 'Significant' : 'Balanced'}
            </div>
          </div>
        )}

        {/* Data Sources */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-xs font-medium text-gray-500">Data Sources</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{Object.keys(quality.data_sources).length}</div>
          <div className="text-xs text-gray-500 mt-1">
            {Object.keys(quality.data_sources).length} types
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {quality.recommendations && quality.recommendations.length > 0 && (
        <div className="px-6 pb-6 pt-2">
          <h4 className="text-xs font-semibold text-gray-700 mb-3">Recommendations</h4>
          <div className="space-y-2">
            {quality.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 text-xs text-gray-600 bg-purple-50 rounded-lg p-3"
              >
                <span className="mt-0.5">{rec.startsWith('✅') ? '✅' : rec.startsWith('⚠️') ? '⚠️' : '💡'}</span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
