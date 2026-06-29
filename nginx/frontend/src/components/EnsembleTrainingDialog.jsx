/**
 * Ensemble Training Dialog
 * Configure and start stacking ensemble training
 */
import { useState } from 'react';
import { X, Layers, CheckCircle, Sparkles, Brain, TrendingUp } from 'lucide-react';

// Available meta-learner types
const META_LEARNERS = [
  { id: 'logistic_regression', name: 'Logistic Regression', icon: TrendingUp, description: 'Fast, interpretable, works well with small datasets', recommended: true },
  { id: 'xgboost', name: 'XGBoost', icon: Sparkles, description: 'Powerful gradient boosting, handles complex patterns' },
  { id: 'lightgbm', name: 'LightGBM', icon: Sparkles, description: 'Fast gradient boosting, memory efficient' },
  { id: 'random_forest', name: 'Random Forest', icon: Brain, description: 'Robust ensemble learner, reduces overfitting' },
  { id: 'mlp', name: 'Neural Network (MLP)', icon: Brain, description: 'Deep learning, captures non-linear patterns' },
];

export default function EnsembleTrainingDialog({ completedModels, activeRun, onStart, onClose, isLoading, loadingStatus }) {
  const [selectedMetaLearner, setSelectedMetaLearner] = useState('logistic_regression');
  
  const handleStart = () => {
    onStart({
      metaLearnerType: selectedMetaLearner
    });
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="font-syne text-xl font-bold text-black-text flex items-center gap-2">
              <Layers className="w-6 h-6 text-purple-primary" />
              Train Stacking Ensemble
            </h2>
            <p className="text-sm text-gray-muted mt-1">Combine multiple base models into a powerful ensemble</p>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-muted" />
          </button>
        </div>

        {/* Base Models Section */}
        <div className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-4 h-4 text-purple-primary" />
            <h3 className="font-syne font-bold text-sm text-black-text">Base Models to Combine</h3>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {completedModels.map(model => (
              <div key={model.modelId} className="p-2 bg-white rounded-lg border border-purple-200">
                <div className="text-xs font-medium text-black-text">{model.modelName}</div>
                <div className="text-[10px] text-gray-muted mt-1">
                  AUC: {(model.oof_auc || 0).toFixed(3)}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-purple-700">
            <span className="font-medium">✨ Stacking Strategy:</span> The ensemble will learn optimal weights for combining these {completedModels.length} models' predictions using a meta-learner.
          </div>
        </div>

        {/* Meta-Learner Selection */}
        <div className="mb-6">
          <h3 className="font-syne text-sm font-bold text-black-text mb-3">Select Meta-Learner</h3>
          <p className="text-xs text-gray-muted mb-3">
            The meta-learner will learn how to optimally combine base model predictions
          </p>
          
          <div className="space-y-2">
            {META_LEARNERS.map(learner => {
              const Icon = learner.icon;
              const isSelected = selectedMetaLearner === learner.id;
              
              return (
                <button
                  key={learner.id}
                  onClick={() => setSelectedMetaLearner(learner.id)}
                  disabled={isLoading}
                  className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                    isSelected
                      ? 'border-purple-primary bg-purple-dim'
                      : 'border-gray-200 hover:border-purple-primary/50 hover:bg-purple-primary/5'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={`w-5 h-5 mt-0.5 ${isSelected ? 'text-purple-primary' : 'text-gray-muted'}`} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-black-text">{learner.name}</span>
                        {learner.recommended && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700">
                            Recommended
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-muted mt-1">{learner.description}</p>
                    </div>
                    {isSelected && (
                      <CheckCircle className="w-5 h-5 text-purple-primary flex-shrink-0" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Info Box */}
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-xs text-blue-700">
            <div className="font-medium mb-2">📚 What is Stacking Ensemble?</div>
            <ul className="space-y-1 text-[11px]">
              <li>• Uses out-of-fold predictions from base models as training data</li>
              <li>• Meta-learner learns optimal weights for combining predictions</li>
              <li>• Often outperforms individual models and simple averaging</li>
              <li>• Provides calibrated probabilities for clinical decision-making</li>
            </ul>
          </div>
        </div>

        {/* Loading Status */}
        {isLoading && (
          <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-purple-primary border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs text-purple-700">{loadingStatus}</span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 rounded-lg border-2 border-gray-200 hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-primary to-blue-500 text-white hover:opacity-90 transition-opacity text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Starting Ensemble...' : `Train Ensemble with ${completedModels.length} Models`}
          </button>
        </div>
      </div>
    </div>
  );
}
