import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  Cpu,
  Zap,
  TrendingUp,
  Activity,
  HardDrive,
  Thermometer,
  AlertCircle,
  CheckCircle,
  Clock,
  Calendar
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function GPUMonitoringPage() {
  const navigate = useNavigate();
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [timeRange, setTimeRange] = useState('1h');

  // Mock GPU data
  const [gpuStatus, setGpuStatus] = useState({
    name: 'GPU Device',
    status: 'online',
    utilization: 76,
    temperature: 67,
    powerUsage: 285,
    powerLimit: 350,
    memoryUsed: 18.4,
    memoryTotal: 24,
    fanSpeed: 65,
    clockSpeed: 1695,
    computeMode: 'Default'
  });

  const [quotaUsage, setQuotaUsage] = useState({
    hoursUsed: 23.5,
    hoursLimit: 100,
    weeklyUsed: 5.2,
    weeklyLimit: 8,
    monthlyBudget: 500,
    costPerHour: 2.5
  });

  const activeJobs = [
    {
      id: 1,
      name: 'SLE_classifier_v3_training',
      user: 'Dr. Sarah Chen',
      started: '2h 15m ago',
      gpuUtil: 98,
      vramUsed: 22.1,
      estimatedTime: '1h 30m',
      status: 'running'
    },
    {
      id: 2,
      name: 'hyperparameter_tuning_rf',
      user: 'Dr. Ahmad Rahman',
      started: '45m ago',
      gpuUtil: 65,
      vramUsed: 8.3,
      estimatedTime: '2h 15m',
      status: 'running'
    }
  ];

  const jobHistory = [
    {
      id: 1,
      name: 'disease_activity_model_v2',
      user: 'Dr. Sarah Chen',
      duration: '3h 22m',
      gpuUtil: 'Avg: 89%',
      vramPeak: '21.3GB',
      completed: '2h ago',
      status: 'completed'
    },
    {
      id: 2,
      name: 'data_preprocessing_batch3',
      user: 'Dr. Li Wei',
      duration: '1h 08m',
      gpuUtil: 'Avg: 45%',
      vramPeak: '12.1GB',
      completed: '5h ago',
      status: 'completed'
    },
    {
      id: 3,
      name: 'neural_net_experiment_12',
      user: 'Dr. Ahmad Rahman',
      duration: '0h 34m',
      gpuUtil: 'Avg: 92%',
      vramPeak: '23.8GB',
      completed: '1d ago',
      status: 'failed',
      error: 'CUDA out of memory'
    }
  ];

  const utilizationHistory = [
    { time: '00:00', util: 45, vram: 12.3 },
    { time: '04:00', util: 0, vram: 0 },
    { time: '08:00', util: 67, vram: 15.2 },
    { time: '12:00', util: 89, vram: 21.1 },
    { time: '16:00', util: 98, vram: 22.8 },
    { time: '20:00', util: 76, vram: 18.4 }
  ];

  return (
    <DashboardLayout>
      <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        <div className="p-6">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
            <div>
              <h1 className="font-syne text-[28px] font-bold text-[#0F0F11]">GPU Monitoring</h1>
              <p className="text-[13px] text-[#8585A0] mt-1">Real-time GPU performance and resource tracking</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-xl">
                <Activity className="w-4 h-4 text-[#7B5CF0] animate-pulse" />
                <span className="text-[11px] text-[#8585A0]">Auto-refresh:</span>
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="text-[11px] text-[#0F0F11] font-semibold bg-transparent focus:outline-none"
                >
                  <option value={5}>5s</option>
                  <option value={10}>10s</option>
                  <option value={30}>30s</option>
                  <option value={60}>1m</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* GPU Status Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <GPUStatCard
            icon={Cpu}
            label="GPU Utilization"
            value={`${gpuStatus.utilization}%`}
            subtitle={gpuStatus.name}
            color="purple"
            status="active"
          />
          <GPUStatCard
            icon={HardDrive}
            label="VRAM Usage"
            value={`${gpuStatus.memoryUsed}GB`}
            subtitle={`/ ${gpuStatus.memoryTotal}GB`}
            color="amber"
            percentage={(gpuStatus.memoryUsed / gpuStatus.memoryTotal) * 100}
          />
          <GPUStatCard
            icon={Thermometer}
            label="Temperature"
            value={`${gpuStatus.temperature}°C`}
            subtitle="Within safe range"
            color="green"
          />
          <GPUStatCard
            icon={Zap}
            label="Power Draw"
            value={`${gpuStatus.powerUsage}W`}
            subtitle={`/ ${gpuStatus.powerLimit}W`}
            color="blue"
            percentage={(gpuStatus.powerUsage / gpuStatus.powerLimit) * 100}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {/* Real-time Metrics */}
          <div className="col-span-2 bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Real-time Performance</h2>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="text-[11px] px-3 py-1.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:border-[#7B5CF0]"
              >
                <option value="15m">Last 15 minutes</option>
                <option value="1h">Last hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
              </select>
            </div>
            <div className="p-6">
              {/* Utilization Chart */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[12px] text-[#8585A0] font-medium">GPU Utilization %</span>
                  <span className="text-[13px] text-[#7B5CF0] font-bold">{gpuStatus.utilization}%</span>
                </div>
                <div className="h-32 flex items-end justify-between gap-2">
                  {utilizationHistory.map((point, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full bg-[#7B5CF0]/20 hover:bg-[#7B5CF0]/30 rounded-t transition-colors relative group">
                        <div
                          className="bg-[#7B5CF0] rounded-t transition-all"
                          style={{ height: `${point.util * 1.2}px` }}
                        />
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#0F0F11] text-white text-[10px] px-2 py-1 rounded whitespace-nowrap">
                          {point.util}% · {point.time}
                        </div>
                      </div>
                      <span className="text-[9px] text-[#8585A0]">{point.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* VRAM Chart */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[12px] text-[#8585A0] font-medium">VRAM Usage (GB)</span>
                  <span className="text-[13px] text-[#F59E0B] font-bold">{gpuStatus.memoryUsed}GB</span>
                </div>
                <div className="h-24 flex items-end justify-between gap-2">
                  {utilizationHistory.map((point, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full bg-[#F59E0B]/20 hover:bg-[#F59E0B]/30 rounded-t transition-colors relative group">
                        <div
                          className="bg-[#F59E0B] rounded-t transition-all"
                          style={{ height: `${point.vram * 3}px` }}
                        />
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#0F0F11] text-white text-[10px] px-2 py-1 rounded whitespace-nowrap">
                          {point.vram}GB · {point.time}
                        </div>
                      </div>
                      <span className="text-[9px] text-[#8585A0]">{point.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Quota & Specs */}
          <div className="space-y-4">
            {/* Quota Usage */}
            <div className="bg-[#F5F5F7] rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="font-syne text-[13px] font-bold text-[#0F0F11]">Quota Usage</h3>
              </div>
              <div className="p-4 space-y-4">
                <QuotaBar
                  label="Weekly Limit"
                  used={quotaUsage.weeklyUsed}
                  total={quotaUsage.weeklyLimit}
                  unit="h"
                  color="#EF4444"
                />
                <QuotaBar
                  label="Monthly Budget"
                  used={quotaUsage.hoursUsed}
                  total={quotaUsage.hoursLimit}
                  unit="h"
                  color="#7B5CF0"
                />
                <div className="pt-3 mt-3 border-t border-gray-200 space-y-2">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-[#8585A0]">Cost/hour</span>
                    <span className="text-[#0F0F11] font-semibold">${quotaUsage.costPerHour}</span>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-[#8585A0]">Est. monthly cost</span>
                    <span className="text-[#7B5CF0] font-bold">${(quotaUsage.hoursUsed * quotaUsage.costPerHour).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* GPU Specs */}
            <div className="bg-[#F5F5F7] rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="font-syne text-[13px] font-bold text-[#0F0F11]">GPU Specifications</h3>
              </div>
              <div className="p-4 space-y-2 text-[11px]">
                <SpecRow label="Model" value={gpuStatus.name} />
                <SpecRow label="VRAM" value={`${gpuStatus.memoryTotal}GB GDDR6X`} />
                <SpecRow label="Clock Speed" value={`${gpuStatus.clockSpeed} MHz`} />
                <SpecRow label="Fan Speed" value={`${gpuStatus.fanSpeed}%`} />
                <SpecRow label="Compute Mode" value={gpuStatus.computeMode} />
                <SpecRow label="Driver" value="536.40" />
                <SpecRow label="CUDA" value="12.2" />
              </div>
            </div>
          </div>
        </div>

        {/* Active Jobs */}
        <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md mb-6">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Active Jobs</h2>
            <span className="px-2 py-1 rounded-full bg-[rgba(123,92,240,0.12)] text-[#7B5CF0] text-[10px] font-bold">
              {activeJobs.length} running
            </span>
          </div>
          <div className="p-6 space-y-3">
            {activeJobs.map((job) => (
              <ActiveJobCard key={job.id} job={job} />
            ))}
          </div>
        </div>

        {/* Job History */}
        <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="font-syne text-[15px] font-bold text-[#0F0F11]">Job History</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead className="bg-white/50">
                <tr>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Job Name</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">User</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Duration</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">GPU Util</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">VRAM Peak</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Status</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium text-[#8585A0] border-b border-gray-200">Completed</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {jobHistory.map((job) => (
                  <JobHistoryRow key={job.id} job={job} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    </DashboardLayout>
  );
}

// Components
function GPUStatCard({ icon: Icon, label, value, subtitle, color, status, percentage }) {
  const colors = {
    purple: 'bg-[#7B5CF0]/10 text-[#7B5CF0]',
    amber: 'bg-[#F59E0B]/10 text-[#F59E0B]',
    green: 'bg-[#10B981]/10 text-[#10B981]',
    blue: 'bg-[#3B82F6]/10 text-[#3B82F6]'
  };
  
  return (
    <div className={`${colors[color]} rounded-2xl border border-gray-200 p-4`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-[11px] font-medium opacity-70">{label}</span>
        <Icon className="w-4 h-4" />
      </div>
      <div className="font-syne text-[28px] font-bold leading-none mb-1">{value}</div>
      <div className="text-[10px] opacity-60">{subtitle}</div>
      {percentage && (
        <div className="mt-3 h-1 bg-white/50 rounded-full overflow-hidden">
          <div className="h-full bg-current" style={{ width: `${percentage}%` }} />
        </div>
      )}
      {status === 'active' && (
        <div className="flex items-center gap-1.5 mt-3">
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          <span className="text-[10px] font-semibold">Active</span>
        </div>
      )}
    </div>
  );
}

function QuotaBar({ label, used, total, unit, color }) {
  const percentage = (used / total) * 100;
  
  return (
    <div>
      <div className="flex justify-between items-baseline mb-2">
        <span className="text-[11px] text-[#8585A0]">{label}</span>
        <span className="text-[12px] text-[#0F0F11] font-bold">
          {used}{unit} / {total}{unit}
        </span>
      </div>
      <div className="h-2 bg-[#EFEFF2] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
      <div className="text-[10px] text-[#8585A0] mt-1">
        {percentage >= 80 ? (
          <span className="text-[#EF4444] font-semibold">⚠ {(100 - percentage).toFixed(1)}% remaining</span>
        ) : (
          `${(100 - percentage).toFixed(1)}% available`
        )}
      </div>
    </div>
  );
}

function SpecRow({ label, value }) {
  return (
    <div className="flex justify-between">
      <span className="text-[#8585A0]">{label}</span>
      <span className="text-[#0F0F11] font-semibold">{value}</span>
    </div>
  );
}

function ActiveJobCard({ job }) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-xl bg-white border border-gray-200">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[13px] text-[#0F0F11] font-semibold font-mono">{job.name}</span>
          <span className="px-2 py-0.5 rounded-full bg-[#10B981]/10 text-[#10B981] text-[9px] font-bold">
            RUNNING
          </span>
        </div>
        <div className="text-[11px] text-[#8585A0] mb-3">
          {job.user} · Started {job.started} · ETA: {job.estimatedTime}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#8585A0]">GPU</span>
              <span className="text-[#0F0F11] font-semibold">{job.gpuUtil}%</span>
            </div>
            <div className="h-1 bg-[#EFEFF2] rounded-full overflow-hidden">
              <div className="h-full bg-[#7B5CF0]" style={{ width: `${job.gpuUtil}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#8585A0]">VRAM</span>
              <span className="text-[#0F0F11] font-semibold">{job.vramUsed}GB</span>
            </div>
            <div className="h-1 bg-[#EFEFF2] rounded-full overflow-hidden">
              <div className="h-full bg-[#F59E0B]" style={{ width: `${(job.vramUsed / 24) * 100}%` }} />
            </div>
          </div>
        </div>
      </div>
      <button className="text-[11px] text-[#EF4444] hover:underline font-medium">
        Stop
      </button>
    </div>
  );
}

function JobHistoryRow({ job }) {
  const statusColors = {
    completed: { bg: 'bg-[#10B981]/10', text: 'text-[#10B981]', label: 'COMPLETED' },
    failed: { bg: 'bg-[#EF4444]/10', text: 'text-[#EF4444]', label: 'FAILED' }
  };
  
  const s = statusColors[job.status];
  
  return (
    <tr className="hover:bg-white/50 transition-colors border-b border-gray-200 last:border-0">
      <td className="px-4 py-3 text-[#7B5CF0] font-semibold">{job.name}</td>
      <td className="px-4 py-3 text-[#8585A0]">{job.user}</td>
      <td className="px-4 py-3 text-[#0F0F11]">{job.duration}</td>
      <td className="px-4 py-3 text-[#8585A0]">{job.gpuUtil}</td>
      <td className="px-4 py-3 text-[#0F0F11] font-semibold">{job.vramPeak}</td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full ${s.bg} ${s.text} text-[10px] font-bold`}>
          {s.label}
        </span>
      </td>
      <td className="px-4 py-3 text-[#8585A0]">
        {job.completed}
        {job.error && (
          <div className="text-[10px] text-[#EF4444] mt-0.5">{job.error}</div>
        )}
      </td>
    </tr>
  );
}
