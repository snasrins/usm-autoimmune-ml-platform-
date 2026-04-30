/**
 * Prediction Widget - Phase 3
 * Embedded patient prediction interface for dashboard
 */
import { useState } from 'react';
import { Brain, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

export default function PredictionWidget() {
  const [patientData, setPatientData] = useState({
    age: '',
    gender: 'Female',
    ana_level: '',
    anti_dsdna: ''
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      
      // Mock prediction for now - replace with real API call
      // const response = await axios.post('http://localhost:8000/api/v1/ml/predict', {
      //   patient_data: patientData
      // }, {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      
      // Mock response
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setPrediction({
        predicted_class: 'SLE',
        probability: 0.82,
        confidence: 'Medium',
        top_factors: [
          { factor: 'ANA Level', impact: '+0.34' },
          { factor: 'Age', impact: '+0.12' },
          { factor: 'Anti-dsDNA', impact: '+0.28' }
        ]
      });
    } catch (error) {
      console.error('Prediction failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence === 'High') return 'text-green-600 bg-green-100';
    if (confidence === 'Medium') return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-white rounded-xl border border-purple-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-purple-200 bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-syne text-lg font-bold text-gray-900">Quick Prediction</h3>
            <p className="text-xs text-gray-500">Test ML model with patient data</p>
          </div>
        </div>
      </div>

      <div className="p-5">
        {/* Input Form */}
        <div className="space-y-3 mb-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Age</label>
              <input
                type="number"
                value={patientData.age}
                onChange={(e) => setPatientData({...patientData, age: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="34"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Gender</label>
              <select
                value={patientData.gender}
                onChange={(e) => setPatientData({...patientData, gender: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option>Female</option>
                <option>Male</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">ANA Level</label>
            <input
              type="number"
              step="0.1"
              value={patientData.ana_level}
              onChange={(e) => setPatientData({...patientData, ana_level: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="1.5"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Anti-dsDNA</label>
            <input
              type="number"
              step="0.1"
              value={patientData.anti_dsdna}
              onChange={(e) => setPatientData({...patientData, anti_dsdna: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="0.8"
            />
          </div>
        </div>

        {/* Predict Button */}
        <button
          onClick={handlePredict}
          disabled={loading || !patientData.age || !patientData.ana_level}
          className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Predicting...
            </span>
          ) : (
            'Run Prediction'
          )}
        </button>

        {/* Prediction Result */}
        {prediction && (
          <div className="mt-4 pt-4 border-t border-purple-200">
            <div className="bg-white rounded-lg p-4 border border-purple-200 shadow-sm">
              {/* Prediction */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-xs text-gray-500">Prediction</span>
                  <div className="text-2xl font-bold text-purple-700">{prediction.predicted_class}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">Probability</span>
                  <div className="text-2xl font-bold text-gray-900">{(prediction.probability * 100).toFixed(0)}%</div>
                </div>
              </div>

              {/* Confidence */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs text-gray-600">Confidence:</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getConfidenceColor(prediction.confidence)}`}>
                  {prediction.confidence}
                </span>
              </div>

              {/* Top Factors */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <h4 className="text-xs font-semibold text-gray-700 mb-2">Top Influencing Factors</h4>
                <div className="space-y-1.5">
                  {prediction.top_factors.map((factor, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">{factor.factor}</span>
                      <span className={`font-semibold ${factor.impact.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                        {factor.impact}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
