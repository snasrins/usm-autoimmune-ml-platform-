import { AlertTriangle, Brain, Cpu, Activity, CheckCircle2, Database } from 'lucide-react';
import { motion } from 'framer-motion';

export function DatasetStatusCard({ count }) {
  return (
    <div 
      className="h-full min-h-[152px] rounded-3xl p-5 border transition-all flex flex-col justify-between hover:shadow-lg"
      style={{
        background: 'linear-gradient(135deg, #FAF8FF 0%, #F3EEF9 60%, #EDE5F5 100%)',
        border: '1px solid rgba(156,39,176,0.10)',
        boxShadow: '0 4px 16px rgba(74,18,89,0.06), inset 0 1px 0 rgba(255,255,255,0.8)'
      }}
    >
      <div className="flex items-center justify-start mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-semibold">Datasets Ingested</span>
      </div>
      
      <div className="mb-2">
        <div className="text-5xl font-bold text-[#0A0118] mb-2 leading-none">{count}</div>
        <div className="text-sm text-[#4a5568]">Total datasets uploaded</div>
      </div>
    </div>
  );
}

export function DataQualityCard({ issues, missingPercent }) {
  return (
    <div 
      className="h-full min-h-[152px] rounded-3xl p-5 border transition-all flex flex-col justify-between hover:shadow-lg"
      style={{
        background: 'linear-gradient(135deg, #FFF8FE 0%, #F9EDFD 60%, #F3E0F9 100%)',
        border: '1px solid rgba(194,24,91,0.10)',
        boxShadow: '0 4px 16px rgba(156,39,176,0.07), inset 0 1px 0 rgba(255,255,255,0.8)'
      }}
    >
      <div className="flex items-center justify-start mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-semibold">Data Quality Issues</span>
      </div>
      
      <div className="mb-2">
        <div className="text-5xl font-bold text-[#0A0118] mb-2 leading-none">{issues}</div>
        <div className="text-sm text-[#4a5568]">{missingPercent.toFixed(1)}% missing values</div>
      </div>
    </div>
  );
}

export function ModelPerformanceCard({ modelName, accuracy, lastTrained }) {
  return (
    <div className="h-full min-h-[152px] bg-gradient-to-br from-white via-white to-[#e9d8fd]/30 rounded-2xl p-4 border border-[#e2e8f0] shadow-sm hover:shadow transition-all flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-semibold">Model Performance</span>
        <div className="w-4 h-4 rounded-full border-2 border-[#6b46c1] flex items-center justify-center text-[#6b46c1] text-xs">●</div>
      </div>
      
      <div className="mb-2">
        <div className="text-lg font-semibold text-[#1a0a2e]">{modelName}</div>
        <div className="text-sm text-[#4a5568]">Accuracy: <span className="font-bold text-[#6b46c1]">{accuracy}%</span></div>
      </div>
      
      <div className="text-xs text-[#4a5568]">Last trained: {lastTrained}</div>
    </div>
  );
}

export function GPUUsageCard({ percentage, used, total }) {
  const circumference = 2 * Math.PI * 35;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  return (
    <div className="h-full min-h-[152px] bg-gradient-to-br from-white via-white to-[#e9d8fd]/30 rounded-2xl p-4 border border-[#e2e8f0] shadow-sm hover:shadow transition-all flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-medium">GPU Usage</span>
        <Tooltip.Provider>
          <Tooltip.Root>
            <Tooltip.Trigger asChild>
              <button className="w-4 h-4 rounded-full border border-[#e2e8f0] flex items-center justify-center text-[#4a5568] text-xs hover:border-[#6b46c1] transition-colors">i</button>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
                Weekly GPU allocation
                <Tooltip.Arrow className="fill-gray-900" />
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        </Tooltip.Provider>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20">
          <svg className="w-20 h-20 transform -rotate-90">
            <circle
              cx="40"
              cy="40"
              r="35"
              stroke="currentColor"
              className="text-[#e2e8f0]"
              strokeWidth="8"
              fill="none"
            />
            <circle
              cx="40"
              cy="40"
              r="35"
              stroke="url(#gradient)"
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#9f7aea" />
                <stop offset="100%" stopColor="#6b46c1" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-[#1a0a2e]">{percentage}%</span>
          </div>
        </div>
        
        <div>
          <div className="text-[#1a0a2e] font-semibold">{used} / {total}</div>
          <div className="text-xs text-[#4a5568]">hours used</div>
          <div className="text-xs text-[#6b46c1] mt-1">8h this week</div>
        </div>
      </div>
    </div>
  );
}

// New GPU Status Card (Simplified)
export function GPUStatusCard({ percentage, used, total }) {
  return (
    <div 
      className="h-full min-h-[152px] rounded-3xl p-5 border transition-all flex flex-col justify-between hover:shadow-lg"
      style={{
        background: 'linear-gradient(135deg, #FFF5FC 0%, #FAE8F7 60%, #F5DDF4 100%)',
        border: '1px solid rgba(216,27,96,0.10)',
        boxShadow: '0 4px 16px rgba(194,24,91,0.07), inset 0 1px 0 rgba(255,255,255,0.8)'
      }}
    >
      <div className="flex items-center justify-start mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-semibold">GPU Usage</span>
      </div>
      
      <div className="mb-2">
        <div className="text-5xl font-bold text-[#0A0118] mb-2 leading-none">{percentage}%</div>
        <div className="text-sm text-[#4a5568]">{used}h / {total}h used</div>
      </div>
    </div>
  );
}

// New Trained Models Card
export function TrainedModelsCard({ count, training }) {
  return (
    <div 
      className="h-full min-h-[152px] rounded-3xl p-5 border transition-all flex flex-col justify-between hover:shadow-lg"
      style={{
        background: 'linear-gradient(135deg, #F8F5FF 0%, #EEE5FA 60%, #E6D8F5 100%)',
        border: '1px solid rgba(106,20,120,0.10)',
        boxShadow: '0 4px 16px rgba(74,18,89,0.07), inset 0 1px 0 rgba(255,255,255,0.8)'
      }}
    >
      <div className="flex items-center justify-start mb-3">
        <span className="text-xs text-[#4a5568] uppercase tracking-wider font-semibold">Trained Models</span>
      </div>
      
      <div className="mb-2">
        <div className="text-5xl font-bold text-[#0A0118] mb-2 leading-none">{count}</div>
        <div className="text-sm text-[#4a5568]">
          {training > 0 ? `${training} currently training` : 'All models ready'}
        </div>
      </div>
    </div>
  );
}
