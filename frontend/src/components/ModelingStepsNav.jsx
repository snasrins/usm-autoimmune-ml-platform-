/**
 * ModelingStepsNav — horizontal workflow step indicator for Modeling pages
 * Shows: Training Jobs → Registry → Comparison → Explainability
 */
import { useNavigate, useLocation } from 'react-router-dom';
import { Zap, Layers, BarChart3, Eye, ChevronRight } from 'lucide-react';

const STEPS = [
  { label: 'Training Jobs', path: '/training',          icon: Zap      },
  { label: 'Registry',      path: '/models',            icon: Layers   },
  { label: 'Comparison',    path: '/model-comparison',  icon: BarChart3 },
  { label: 'Explainability',path: '/explainability',    icon: Eye      },
];

export default function ModelingStepsNav() {
  const navigate   = useNavigate();
  const { pathname } = useLocation();

  const currentIdx = STEPS.findIndex(s => pathname.startsWith(s.path));

  return (
    <div className="flex items-center gap-1 px-6 pt-4 pb-0 flex-wrap">
      {STEPS.map((step, idx) => {
        const Icon      = step.icon;
        const isCurrent = idx === currentIdx;
        const isDone    = idx < currentIdx;

        return (
          <div key={step.path} className="flex items-center gap-1">
            <button
              onClick={() => navigate(step.path)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                isCurrent
                  ? 'bg-purple-primary text-white shadow-sm'
                  : isDone
                  ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                  : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
              }`}
            >
              <Icon className="w-3 h-3" />
              {step.label}
            </button>
            {idx < STEPS.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );
}
