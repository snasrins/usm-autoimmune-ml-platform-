import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import DashboardLayout from '../components/DashboardLayout';
import {
  Upload, Brain, ShieldCheck, Users, BarChart2, FileSearch,
  ArrowRight, Clock, AlertTriangle, ChevronRight, Zap,
  Database, TrendingUp, LayoutDashboard, Activity
} from 'lucide-react';

// ─── Static mock data (to be replaced with API calls) ────────────────────────

const WORKFLOWS = [
  {
    id: 'upload',
    icon: Upload,
    title: 'Upload Clinical Dataset',
    subtitle: 'Ingest new patient data for processing',
    path: '/data-catalog',
    gradient: 'linear-gradient(135deg, #4A1259 0%, #7C2D92 100%)',
    tag: null,
  },
  {
    id: 'training',
    icon: Brain,
    title: 'Continue Model Training',
    subtitle: 'Resume or launch a new training run',
    path: '/training',
    gradient: 'linear-gradient(135deg, #7B1FA2 0%, #9C27B0 100%)',
    tag: { label: 'In Progress', color: '#7B1FA2', bg: 'rgba(123,31,162,0.10)' },
  },
  {
    id: 'quality',
    icon: ShieldCheck,
    title: 'Review Data Quality',
    subtitle: 'Validate datasets before model training',
    path: '/data-quality',
    gradient: 'linear-gradient(135deg, #AD1457 0%, #C2185B 100%)',
    tag: { label: '3 Pending', color: '#C2185B', bg: 'rgba(194,24,91,0.10)' },
  },
  {
    id: 'prediction',
    icon: Users,
    title: 'Run Batch Prediction',
    subtitle: 'Score patient cohorts against trained models',
    path: '/batch-prediction',
    gradient: 'linear-gradient(135deg, #C2185B 0%, #D81B60 100%)',
    tag: { label: '12 Awaiting', color: '#D81B60', bg: 'rgba(216,27,96,0.10)' },
  },
  {
    id: 'compare',
    icon: BarChart2,
    title: 'Compare Model Performance',
    subtitle: 'Evaluate metrics across all experiments',
    path: '/model-comparison',
    gradient: 'linear-gradient(135deg, #6A1478 0%, #8E24AA 100%)',
    tag: null,
  },
  {
    id: 'explain',
    icon: FileSearch,
    title: 'Explainability Report',
    subtitle: 'Review SHAP values and feature contributions',
    path: '/explainability',
    gradient: 'linear-gradient(135deg, #4A1259 0%, #6A1478 100%)',
    tag: null,
  },
];

const RECOMMENDATIONS = [
  {
    id: 1,
    text: '3 datasets require validation before use',
    icon: Database,
    dot: '#C2185B',
    path: '/data-quality',
  },
  {
    id: 2,
    text: 'Training job paused yesterday at epoch 42',
    icon: Brain,
    dot: '#9C27B0',
    path: '/training',
  },
  {
    id: 3,
    text: '12 new predictions awaiting clinical review',
    icon: Users,
    dot: '#7C2D92',
    path: '/batch-prediction',
  },
];

const ATTENTION_ITEMS = [
  { id: 1, text: 'Missing values exceed threshold in SLE_Dataset_2025', level: 'error' },
  { id: 2, text: 'GPU training failed at epoch 38', level: 'error' },
  { id: 3, text: 'Prediction confidence below benchmark (0.71 < 0.80)', level: 'warn' },
];

const LAST_ACTIVITY = {
  name: 'AAM-SLE-E Model Training',
  detail: 'Epoch 42 / 100 — 68% complete',
  time: 'Paused 18h ago',
  path: '/training',
  progress: 42,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function timeGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatDate() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  });
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function WorkflowCard({ workflow, hovered, onHover, onLeave, onClick }) {
  const Icon = workflow.icon;
  const isHovered = hovered === workflow.id;

  return (
    <motion.button
      className="relative w-full text-left rounded-2xl p-5 border transition-all duration-300 overflow-hidden group"
      style={{
        background: isHovered
          ? 'rgba(255,255,255,0.92)'
          : 'rgba(255,255,255,0.72)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
        border: isHovered
          ? '1px solid rgba(156,39,176,0.28)'
          : '1px solid rgba(255,255,255,0.65)',
        boxShadow: isHovered
          ? 'inset 0 1px 0 rgba(255,255,255,0.8), 0 20px 60px rgba(74,18,89,0.14)'
          : 'inset 0 1px 0 rgba(255,255,255,0.7), 0 4px 16px rgba(15,23,42,0.05)',
      }}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.4 }}
      onMouseEnter={() => onHover(workflow.id)}
      onMouseLeave={onLeave}
      onClick={() => onClick(workflow.path)}
    >
      {/* Icon block */}
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center mb-3 transition-all duration-300"
        style={{
          background: isHovered ? workflow.gradient : 'rgba(74,18,89,0.08)',
        }}
      >
        <Icon
          className="w-5 h-5 transition-colors duration-300"
          style={{ color: isHovered ? '#fff' : '#7C2D92' }}
        />
      </div>

      {/* Title row */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <p
          className="text-sm font-semibold leading-snug"
          style={{ color: isHovered ? '#1a0a2e' : '#2D1B3D' }}
        >
          {workflow.title}
        </p>
        {workflow.tag && (
          <span
            className="flex-shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full"
            style={{
              background: workflow.tag.bg,
              color: workflow.tag.color,
            }}
          >
            {workflow.tag.label}
          </span>
        )}
      </div>

      {/* Subtitle */}
      <p className="text-xs text-slate-500 leading-relaxed">{workflow.subtitle}</p>

      {/* Arrow hint */}
      <motion.div
        className="absolute right-4 bottom-4 flex items-center gap-1"
        initial={{ opacity: 0, x: -4 }}
        animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : -4 }}
        transition={{ duration: 0.2 }}
      >
        <span className="text-[11px] font-semibold" style={{ color: '#9C27B0' }}>
          Go
        </span>
        <ArrowRight className="w-3 h-3" style={{ color: '#9C27B0' }} />
      </motion.div>
    </motion.button>
  );
}

function RecommendationItem({ item, onClick }) {
  const Icon = item.icon;
  return (
    <button
      className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-white/60 transition-all duration-200 text-left group"
      onClick={() => onClick(item.path)}
    >
      <div
        className="w-2 h-2 rounded-full flex-shrink-0 mt-0.5"
        style={{ background: item.dot }}
      />
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: `${item.dot}14` }}
      >
        <Icon className="w-3.5 h-3.5" style={{ color: item.dot }} />
      </div>
      <span className="text-xs text-slate-600 group-hover:text-slate-900 transition-colors leading-snug">
        {item.text}
      </span>
      <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-500 ml-auto flex-shrink-0 transition-colors" />
    </button>
  );
}

function AttentionItem({ item }) {
  return (
    <div className="flex items-start gap-2.5 py-2.5 border-b border-red-50 last:border-0">
      <AlertTriangle
        className="w-3.5 h-3.5 mt-0.5 flex-shrink-0"
        style={{ color: item.level === 'error' ? '#DC2626' : '#D97706' }}
      />
      <span className="text-xs text-slate-600 leading-snug">{item.text}</span>
    </div>
  );
}

// ─── Ambient Background (same formula as DashboardPage) ──────────────────────

function AmbientOrbs() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 overflow-hidden"
      style={{ zIndex: 0 }}
    >
      <div
        className="absolute rounded-full"
        style={{
          width: 600, height: 600,
          top: -120, left: -160,
          background: 'radial-gradient(circle, rgba(156,39,176,0.09) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: 500, height: 500,
          top: '30%', right: -100,
          background: 'radial-gradient(circle, rgba(194,24,91,0.07) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: 400, height: 400,
          bottom: 80, left: '30%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      {/* Dot grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(74,18,89,0.06) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function MissionControlPage() {
  const navigate = useNavigate();
  const [hoveredCard, setHoveredCard] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Slight mount delay for dramatic entrance
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  const goTo = (path) => navigate(path);

  return (
    <DashboardLayout>
      <AmbientOrbs />

      <div className="relative min-h-screen px-8 py-8" style={{ zIndex: 1 }}>

        {/* ── Top bar: date chip + skip link ── */}
        <motion.div
          className="flex items-center justify-between mb-10"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: 'rgba(74,18,89,0.07)',
              color: '#7C2D92',
              border: '1px solid rgba(74,18,89,0.12)',
            }}
          >
            <div
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: '#9C27B0' }}
            />
            {formatDate()}
          </div>

          <button
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 transition-colors duration-200"
            onClick={() => navigate('/dashboard')}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Go to full dashboard
            <ArrowRight className="w-3 h-3" />
          </button>
        </motion.div>

        {/* ── Hero greeting ── */}
        <motion.div
          className="mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15 }}
        >
          <p
            className="text-sm font-medium mb-1"
            style={{ color: '#9C27B0' }}
          >
            {timeGreeting()} —
          </p>
          <h1
            className="text-3xl font-bold mb-2 tracking-tight"
            style={{ color: '#1a0a2e' }}
          >
            Welcome back, Nasrin.
          </h1>
          <p className="text-base text-slate-500 font-normal">
            What would you like to do today?
          </p>
        </motion.div>

        {/* ── Main 2-col layout ── */}
        <div className="grid gap-6" style={{ gridTemplateColumns: 'minmax(0,1fr) 340px' }}>

          {/* ─ Left: Workflow grid ─ */}
          <div>
            <motion.p
              className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.25 }}
            >
              Choose your workflow
            </motion.p>

            <div className="grid grid-cols-2 gap-3">
              {WORKFLOWS.map((wf, i) => (
                <motion.div
                  key={wf.id}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.45, delay: 0.28 + i * 0.06 }}
                >
                  <WorkflowCard
                    workflow={wf}
                    hovered={hoveredCard}
                    onHover={setHoveredCard}
                    onLeave={() => setHoveredCard(null)}
                    onClick={goTo}
                  />
                </motion.div>
              ))}
            </div>
          </div>

          {/* ─ Right: Intel panel ─ */}
          <div className="flex flex-col gap-4">

            {/* Recommended for You */}
            <motion.div
              className="rounded-2xl p-4 border"
              style={{
                background: 'rgba(255,255,255,0.72)',
                backdropFilter: 'blur(18px)',
                WebkitBackdropFilter: 'blur(18px)',
                border: '1px solid rgba(255,255,255,0.65)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7), 0 6px 24px rgba(15,23,42,0.05)',
              }}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.35 }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-6 h-6 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(156,39,176,0.10)' }}
                >
                  <Zap className="w-3.5 h-3.5" style={{ color: '#9C27B0' }} />
                </div>
                <h3 className="text-xs font-semibold text-[#1a0a2e] uppercase tracking-widest">
                  Recommended for You
                </h3>
              </div>

              <div className="flex flex-col">
                {RECOMMENDATIONS.map((rec) => (
                  <RecommendationItem key={rec.id} item={rec} onClick={goTo} />
                ))}
              </div>
            </motion.div>

            {/* Fast Resume */}
            <motion.div
              className="rounded-2xl p-5 border relative overflow-hidden cursor-pointer group"
              style={{
                background: 'linear-gradient(135deg, #1a0a2e 0%, #2D1055 60%, #3D1070 100%)',
                border: '1px solid rgba(156,39,176,0.25)',
                boxShadow: '0 8px 32px rgba(74,18,89,0.25)',
              }}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              whileHover={{ y: -2 }}
              transition={{ duration: 0.5, delay: 0.42 }}
              onClick={() => navigate(LAST_ACTIVITY.path)}
            >
              {/* Subtle glow blob */}
              <div
                className="absolute -top-12 -right-12 w-32 h-32 rounded-full pointer-events-none"
                style={{
                  background: 'radial-gradient(circle, rgba(194,24,91,0.25) 0%, transparent 70%)',
                  filter: 'blur(16px)',
                }}
              />

              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-3.5 h-3.5 text-purple-300" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-purple-300">
                  Continue Where You Left Off
                </span>
              </div>

              <p className="text-sm font-bold text-white mt-2 mb-0.5">
                {LAST_ACTIVITY.name}
              </p>
              <p className="text-xs text-purple-200/70 mb-4">
                {LAST_ACTIVITY.detail}
              </p>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-[10px] text-purple-300/80">Progress</span>
                  <span className="text-[10px] font-semibold text-purple-200">
                    {LAST_ACTIVITY.progress}%
                  </span>
                </div>
                <div
                  className="w-full h-1.5 rounded-full overflow-hidden"
                  style={{ background: 'rgba(255,255,255,0.10)' }}
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${LAST_ACTIVITY.progress}%`,
                      background: 'linear-gradient(to right, #9C27B0, #C2185B)',
                    }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[10px] text-purple-300/60">{LAST_ACTIVITY.time}</span>
                <div className="flex items-center gap-1 text-xs font-semibold text-white/80 group-hover:text-white transition-colors">
                  Resume
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </motion.div>

            {/* Needs Attention */}
            <motion.div
              className="rounded-2xl p-4 border"
              style={{
                background: 'rgba(255,245,245,0.80)',
                backdropFilter: 'blur(18px)',
                WebkitBackdropFilter: 'blur(18px)',
                border: '1px solid rgba(220,38,38,0.12)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7), 0 4px 16px rgba(220,38,38,0.05)',
              }}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.49 }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-6 h-6 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(220,38,38,0.08)' }}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                </div>
                <h3 className="text-xs font-semibold uppercase tracking-widest text-red-700">
                  Needs Attention
                </h3>
                <span
                  className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(220,38,38,0.10)', color: '#DC2626' }}
                >
                  {ATTENTION_ITEMS.length}
                </span>
              </div>

              <div>
                {ATTENTION_ITEMS.map((item) => (
                  <AttentionItem key={item.id} item={item} />
                ))}
              </div>
            </motion.div>

          </div>
        </div>

        {/* ── Footer spacer ── */}
        <div className="h-10" />
      </div>
    </DashboardLayout>
  );
}
