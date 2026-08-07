import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Brain, ShieldCheck, Users, BarChart2, FileSearch,
  ArrowRight, Clock, ChevronRight, Zap, Database, X,
} from 'lucide-react';

// ─── Static data (replace with API calls when ready) ─────────────────────────

const WORKFLOWS = [
  {
    id: 'upload',
    icon: Upload,
    title: 'Upload Clinical Dataset',
    subtitle: 'Ingest new patient data',
    path: '/data-catalog',
    gradient: 'linear-gradient(135deg, #4A1259 0%, #7C2D92 100%)',
    tag: null,
  },
  {
    id: 'training',
    icon: Brain,
    title: 'Continue Model Training',
    subtitle: 'Resume or launch a training run',
    path: '/training',
    gradient: 'linear-gradient(135deg, #7B1FA2 0%, #9C27B0 100%)',
    tag: { label: 'In Progress', color: '#CE93D8', bg: 'rgba(206,147,216,0.15)' },
  },
  {
    id: 'quality',
    icon: ShieldCheck,
    title: 'Review Data Quality',
    subtitle: 'Validate before model training',
    path: '/data-quality',
    gradient: 'linear-gradient(135deg, #AD1457 0%, #C2185B 100%)',
    tag: { label: '3 Pending', color: '#F48FB1', bg: 'rgba(244,143,177,0.15)' },
  },
  {
    id: 'prediction',
    icon: Users,
    title: 'Run Batch Prediction',
    subtitle: 'Score patient cohorts',
    path: '/batch-prediction',
    gradient: 'linear-gradient(135deg, #C2185B 0%, #D81B60 100%)',
    tag: { label: '12 Awaiting', color: '#F48FB1', bg: 'rgba(244,143,177,0.15)' },
  },
  {
    id: 'compare',
    icon: BarChart2,
    title: 'Compare Models',
    subtitle: 'Evaluate across experiments',
    path: '/model-comparison',
    gradient: 'linear-gradient(135deg, #6A1478 0%, #8E24AA 100%)',
    tag: null,
  },
  {
    id: 'explain',
    icon: FileSearch,
    title: 'Explainability Report',
    subtitle: 'SHAP values & feature analysis',
    path: '/explainability',
    gradient: 'linear-gradient(135deg, #4A1259 0%, #6A1478 100%)',
    tag: null,
  },
];

const RECOMMENDATIONS = [
  { id: 1, text: '3 datasets require validation before use', icon: Database, accent: '#C2185B', path: '/data-quality' },
  { id: 2, text: 'Training job paused at epoch 42', icon: Brain, accent: '#9C27B0', path: '/training' },
  { id: 3, text: '12 predictions awaiting clinical review', icon: Users, accent: '#7C2D92', path: '/batch-prediction' },
];

const LAST_ACTIVITY = {
  name: 'AAM-SLE-E Model Training',
  detail: 'Epoch 42 / 100 — 68% complete',
  time: 'Paused 18h ago',
  path: '/training',
  progress: 42,
};

// ─── Hook: live sidebar width ─────────────────────────────────────────────────

function useSidebarWidth() {
  const [width, setWidth] = useState(() => {
    const exp = JSON.parse(localStorage.getItem('sidebarExpanded') || 'false');
    return exp ? 200 : 45;
  });

  useEffect(() => {
    const handle = (e) => setWidth(e.detail.expanded ? 200 : 45);
    window.addEventListener('sidebar-toggle', handle);
    return () => window.removeEventListener('sidebar-toggle', handle);
  }, []);

  return width;
}

// ─── WorkflowCard ─────────────────────────────────────────────────────────────

function WorkflowCard({ workflow, hovered, onHover, onLeave, onClick }) {
  const Icon = workflow.icon;
  const active = hovered === workflow.id;

  return (
    <button
      className="relative w-full h-full text-left rounded-xl px-3 py-3 flex flex-col justify-between transition-all duration-200"
      style={{
        background: active ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.04)',
        border: active ? '1px solid rgba(255,255,255,0.18)' : '1px solid rgba(255,255,255,0.07)',
        boxShadow: active ? '0 4px 20px rgba(0,0,0,0.25)' : 'none',
        transform: active ? 'translateY(-1px)' : 'translateY(0)',
      }}
      onMouseEnter={() => onHover(workflow.id)}
      onMouseLeave={onLeave}
      onClick={() => onClick(workflow.path)}
    >
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200"
        style={{ background: active ? workflow.gradient : 'rgba(255,255,255,0.08)' }}
      >
        <Icon className="w-3.5 h-3.5" style={{ color: active ? '#fff' : 'rgba(255,255,255,0.50)' }} />
      </div>

      <div className="flex-1 flex flex-col justify-center py-1.5">
        <div className="flex items-start gap-1.5 flex-wrap">
          <p className="text-xs font-semibold text-white/90 leading-snug">{workflow.title}</p>
          {workflow.tag && (
            <span
              className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full whitespace-nowrap"
              style={{ background: workflow.tag.bg, color: workflow.tag.color }}
            >
              {workflow.tag.label}
            </span>
          )}
        </div>
        <p className="text-[11px] text-white/35 leading-tight mt-0.5">{workflow.subtitle}</p>
      </div>

      <div className="flex items-center justify-end">
        <ArrowRight
          className="w-3 h-3 transition-all duration-150"
          style={{ color: active ? '#CE93D8' : 'rgba(255,255,255,0.18)' }}
        />
      </div>
    </button>
  );
}

// ─── Main Modal ───────────────────────────────────────────────────────────────

export default function MissionControlModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const sidebarWidth = useSidebarWidth();
  const [hoveredCard, setHoveredCard] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const goTo = (path) => {
    onClose();
    navigate(path);
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const firstName = user?.full_name?.split(' ')[0] || user?.username || 'there';

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop — starts at sidebar right edge */}
          <motion.div
            className="fixed top-0 bottom-0 right-0"
            style={{
              left: sidebarWidth,
              zIndex: 50,
              background: 'rgba(4, 1, 14, 0.72)',
              backdropFilter: 'blur(14px)',
              WebkitBackdropFilter: 'blur(14px)',
              transition: 'left 300ms ease-out',
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={onClose}
          />

          {/* Panel — centered within main content area */}
          <motion.div
            className="fixed top-0 bottom-0 right-0 flex items-center justify-center"
            style={{
              left: sidebarWidth,
              zIndex: 51,
              pointerEvents: 'none',
              padding: '16px',
              transition: 'left 300ms ease-out',
            }}
          >
            <motion.div
              className="relative w-full rounded-3xl overflow-hidden flex flex-col"
              style={{
                maxWidth: 900,
                height: 'calc(100vh - 80px)',
                pointerEvents: 'all',
                background: 'rgba(12, 4, 32, 0.80)',
                backdropFilter: 'blur(32px)',
                WebkitBackdropFilter: 'blur(32px)',
                border: '1px solid rgba(255,255,255,0.09)',
                boxShadow: '0 40px 100px rgba(0,0,0,0.70), inset 0 1px 0 rgba(255,255,255,0.07)',
              }}
              initial={{ opacity: 0, y: 28, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 18, scale: 0.97 }}
              transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* Ambient blobs */}
              <div className="absolute inset-0 overflow-hidden pointer-events-none rounded-3xl">
                <div style={{
                  position: 'absolute', top: -80, left: -80, width: 320, height: 320,
                  background: 'radial-gradient(circle, rgba(156,39,176,0.18) 0%, transparent 70%)',
                  filter: 'blur(40px)',
                }} />
                <div style={{
                  position: 'absolute', bottom: -60, right: -60, width: 280, height: 280,
                  background: 'radial-gradient(circle, rgba(194,24,91,0.14) 0%, transparent 70%)',
                  filter: 'blur(40px)',
                }} />
                <div style={{
                  position: 'absolute', inset: 0,
                  backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)',
                  backgroundSize: '28px 28px',
                }} />
              </div>

              {/* Top gradient accent */}
              <div className="absolute top-0 left-0 right-0 h-[2px] rounded-t-3xl" style={{
                background: 'linear-gradient(to right, transparent, #9C27B0, #C2185B, transparent)',
              }} />

              {/* X button */}
              <button
                className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 z-10"
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.10)',
                  color: 'rgba(255,255,255,0.45)',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; e.currentTarget.style.color = 'rgba(255,255,255,0.85)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.45)'; }}
                onClick={onClose}
                aria-label="Dismiss"
              >
                <X className="w-3.5 h-3.5" />
              </button>

              <div className="p-5 relative flex-1 flex flex-col min-h-0">

                {/* Header — compact centered */}
                <div className="text-center mb-4 flex-shrink-0">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] mb-0.5" style={{ color: 'rgba(206,147,216,0.75)' }}>
                    Welcome to MyAria-i
                  </p>
                  <p className="text-sm" style={{ color: 'rgba(255,255,255,0.40)' }}>
                    What would you like to do today?
                  </p>
                </div>

                {/* Recommended — full width horizontal */}
                <div className="mb-3 flex-shrink-0">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Zap className="w-3 h-3" style={{ color: '#CE93D8' }} />
                    <p className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.35)' }}>
                      Recommended for You
                    </p>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {RECOMMENDATIONS.map((rec) => {
                      const Icon = rec.icon;
                      return (
                        <button
                          key={rec.id}
                          className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all duration-200"
                          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
                          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.borderColor = rec.accent + '35'; }}
                          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)'; }}
                          onClick={() => goTo(rec.path)}
                        >
                          <div className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: rec.accent + '22' }}>
                            <Icon className="w-3 h-3" style={{ color: rec.accent }} />
                          </div>
                          <p className="text-[11px] text-white/65 leading-snug flex-1 min-w-0">{rec.text}</p>
                          <ChevronRight className="w-3 h-3 flex-shrink-0" style={{ color: 'rgba(255,255,255,0.15)' }} />
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Divider */}
                <div className="mb-3 flex-shrink-0" style={{ height: 1, background: 'rgba(255,255,255,0.06)' }} />

                {/* Workflow grid — flex-1 so it fills remaining space */}
                <div className="flex-1 flex flex-col min-h-0 mb-3">
                  <p className="text-[10px] font-semibold uppercase tracking-widest mb-2 flex-shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>
                    Choose Your Workflow
                  </p>
                  <div className="grid grid-cols-3 gap-2 flex-1">
                    {WORKFLOWS.map((wf) => (
                      <WorkflowCard
                        key={wf.id}
                        workflow={wf}
                        hovered={hoveredCard}
                        onHover={setHoveredCard}
                        onLeave={() => setHoveredCard(null)}
                        onClick={goTo}
                      />
                    ))}
                  </div>
                </div>

                {/* Continue Where You Left Off */}
                <button
                  className="w-full text-left rounded-xl px-4 py-3 relative overflow-hidden transition-all duration-200 group flex items-center gap-4 flex-shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, rgba(74,18,89,0.55) 0%, rgba(45,16,85,0.55) 60%, rgba(61,16,112,0.55) 100%)',
                    border: '1px solid rgba(156,39,176,0.25)',
                    boxShadow: '0 4px 20px rgba(74,18,89,0.18)',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(156,39,176,0.45)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(74,18,89,0.30)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(156,39,176,0.25)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(74,18,89,0.18)'; }}
                  onClick={() => goTo(LAST_ACTIVITY.path)}
                >
                  <div className="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center" style={{
                    background: 'rgba(156,39,176,0.25)', border: '1px solid rgba(156,39,176,0.35)',
                  }}>
                    <Clock className="w-4 h-4 text-purple-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'rgba(206,147,216,0.70)' }}>Continue Where You Left Off</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <p className="text-xs font-bold text-white truncate">{LAST_ACTIVITY.name}</p>
                      <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.38)' }}>{LAST_ACTIVITY.detail}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5">
                      <div className="w-28 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.10)' }}>
                        <div className="h-full rounded-full" style={{ width: LAST_ACTIVITY.progress + '%', background: 'linear-gradient(to right, #9C27B0, #C2185B)' }} />
                      </div>
                      <span className="text-[10px] font-semibold text-white/50">{LAST_ACTIVITY.progress}%</span>
                      <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>{LAST_ACTIVITY.time}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs font-semibold flex-shrink-0 transition-colors" style={{ color: 'rgba(206,147,216,0.70)' }}>
                    Resume <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </button>

                {/* Footer */}
                <div className="flex items-center justify-between mt-3 pt-2.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.20)' }}>
                    <kbd className="px-1 py-0.5 rounded text-[10px] font-mono mr-0.5" style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.35)' }}>Esc</kbd> to dismiss
                  </span>
                  <button
                    className="text-[11px] font-medium transition-colors"
                    style={{ color: 'rgba(255,255,255,0.25)' }}
                    onMouseEnter={e => { e.currentTarget.style.color = 'rgba(255,255,255,0.60)'; }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'rgba(255,255,255,0.25)'; }}
                    onClick={onClose}
                  >
                    Go to dashboard →
                  </button>
                </div>

              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
