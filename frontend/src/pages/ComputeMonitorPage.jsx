import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Cpu,
  Server,
  HardDrive,
  Wifi,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  Users,
  BarChart3,
  Gauge,
  ThermometerSun,
  RefreshCw,
  Download,
  Settings
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

export default function ComputeMonitorPage() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('1h');
  const [selectedMetric, setSelectedMetric] = useState('cpu');

  // Mock compute cluster data
  const clusterStatus = {
    totalNodes: 12,
    activeNodes: 11,
    standbyNodes: 1,
    failedNodes: 0,
    totalCPU: 288,
    usedCPU: 187,
    totalRAM: 1536, // GB
    usedRAM: 892,
    totalStorage: 48, // TB
    usedStorage: 31.2,
    networkThroughput: 8.7, // GB/s
    powerConsumption: 4.8 // kW
  };

  const nodes = [
    {
      id: 'NODE-01',
      name: 'compute-ml-01',
      status: 'active',
      cpu: { cores: 24, usage: 78, temp: 62 },
      ram: { total: 128, used: 94 },
      storage: { total: 4, used: 2.8 },
      network: { rx: 1.2, tx: 0.8 },
      uptime: '47d 12h',
      jobs: 3,
      location: 'Rack A-01'
    },
    {
      id: 'NODE-02',
      name: 'compute-ml-02',
      status: 'active',
      cpu: { cores: 24, usage: 92, temp: 68 },
      ram: { total: 128, used: 112 },
      storage: { total: 4, used: 3.2 },
      network: { rx: 2.1, tx: 1.5 },
      uptime: '47d 12h',
      jobs: 4,
      location: 'Rack A-02'
    },
    {
      id: 'NODE-03',
      name: 'compute-ml-03',
      status: 'active',
      cpu: { cores: 24, usage: 45, temp: 54 },
      ram: { total: 128, used: 67 },
      storage: { total: 4, used: 1.9 },
      network: { rx: 0.8, tx: 0.5 },
      uptime: '32d 8h',
      jobs: 2,
      location: 'Rack A-03'
    },
    {
      id: 'NODE-04',
      name: 'compute-ml-04',
      status: 'standby',
      cpu: { cores: 24, usage: 3, temp: 42 },
      ram: { total: 128, used: 8 },
      storage: { total: 4, used: 0.5 },
      network: { rx: 0.1, tx: 0.05 },
      uptime: '12d 3h',
      jobs: 0,
      location: 'Rack A-04'
    },
    {
      id: 'NODE-05',
      name: 'compute-ml-05',
      status: 'active',
      cpu: { cores: 24, usage: 67, temp: 59 },
      ram: { total: 128, used: 89 },
      storage: { total: 4, used: 2.4 },
      network: { rx: 1.5, tx: 1.1 },
      uptime: '28d 15h',
      jobs: 3,
      location: 'Rack B-01'
    }
  ];

  const activeJobs = [
    {
      id: 'JOB-2024-0087',
      name: 'SLE Ensemble Training - Stage 2',
      user: 'Dr. Sarah Chen',
      nodes: ['NODE-01', 'NODE-02'],
      cpuUsage: 85,
      ramUsage: 94,
      runtime: '2h 34m',
      priority: 'high',
      status: 'running'
    },
    {
      id: 'JOB-2024-0086',
      name: 'Feature Engineering Pipeline',
      user: 'Dr. Michael Torres',
      nodes: ['NODE-03'],
      cpuUsage: 45,
      ramUsage: 52,
      runtime: '45m',
      priority: 'normal',
      status: 'running'
    },
    {
      id: 'JOB-2024-0085',
      name: 'Data Validation - Batch 12',
      user: 'Dr. Emily Watson',
      nodes: ['NODE-05'],
      cpuUsage: 67,
      ramUsage: 69,
      runtime: '1h 18m',
      priority: 'normal',
      status: 'running'
    }
  ];

  const statusColors = {
    active: { bg: 'bg-green-dim', text: 'text-green', border: 'border-green/20' },
    standby: { bg: 'bg-amber-dim', text: 'text-amber', border: 'border-amber/20' },
    failed: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' }
  };

  const priorityColors = {
    high: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' },
    normal: { bg: 'bg-purple-dim', text: 'text-purple-primary', border: 'border-purple-primary/20' },
    low: { bg: 'bg-gray-100', text: 'text-gray-muted', border: 'border-gray-300' }
  };

  const cpuUtilization = (clusterStatus.usedCPU / clusterStatus.totalCPU) * 100;
  const ramUtilization = (clusterStatus.usedRAM / clusterStatus.totalRAM) * 100;
  const storageUtilization = (clusterStatus.usedStorage / clusterStatus.totalStorage) * 100;

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        {/* Header */}
        <div className="bg-white/60 backdrop-blur-sm border-b border-white/40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-primary to-purple-primary/80 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-syne text-2xl font-bold text-black-text">Compute Monitor</h1>
                  <p className="text-xs text-gray-muted">Real-time cluster resource monitoring</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-white/40 bg-white/90 text-xs focus:outline-none focus:border-purple-primary"
                >
                  <option value="1h">Last Hour</option>
                  <option value="6h">Last 6 Hours</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                </select>
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/40 bg-white/80 hover:bg-white text-gray-muted hover:text-black-text text-sm transition-all">
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-primary to-purple-primary/90 text-white hover:shadow-lg transition-all text-sm font-medium">
                  <Download className="w-4 h-4" />
                  Export Metrics
                </button>
              </div>
            </div>

            {/* Cluster Overview Stats */}
            <div className="grid grid-cols-6 gap-4">
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Total Nodes</span>
                  <Server className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">{clusterStatus.totalNodes}</div>
                <div className="text-xs text-green mt-1">
                  {clusterStatus.activeNodes} active • {clusterStatus.standbyNodes} standby
                </div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">CPU Usage</span>
                  <Cpu className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-purple-primary">{cpuUtilization.toFixed(1)}%</div>
                <div className="text-xs text-gray-muted mt-1">{clusterStatus.usedCPU}/{clusterStatus.totalCPU} cores</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">RAM Usage</span>
                  <HardDrive className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-purple-primary">{ramUtilization.toFixed(1)}%</div>
                <div className="text-xs text-gray-muted mt-1">{clusterStatus.usedRAM}/{clusterStatus.totalRAM} GB</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Storage</span>
                  <HardDrive className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-black-text">{storageUtilization.toFixed(1)}%</div>
                <div className="text-xs text-gray-muted mt-1">{clusterStatus.usedStorage}/{clusterStatus.totalStorage} TB</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Network</span>
                  <Wifi className="w-4 h-4 text-purple-primary" />
                </div>
                <div className="font-syne text-2xl font-bold text-green">{clusterStatus.networkThroughput}</div>
                <div className="text-xs text-gray-muted mt-1">GB/s throughput</div>
              </div>
              <div className="bg-white/80 rounded-xl p-4 border border-white/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-muted uppercase">Power</span>
                  <Zap className="w-4 h-4 text-amber" />
                </div>
                <div className="font-syne text-2xl font-bold text-amber">{clusterStatus.powerConsumption}</div>
                <div className="text-xs text-gray-muted mt-1">kW consumption</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Active Jobs */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/40 bg-white/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-primary" />
                  <h3 className="font-syne text-base font-bold text-black-text">Active Jobs</h3>
                  <span className="px-2 py-0.5 rounded-full bg-purple-dim text-purple-primary text-xs font-bold">
                    {activeJobs.length}
                  </span>
                </div>
                <button className="text-xs font-medium text-purple-primary hover:underline">
                  View All Jobs
                </button>
              </div>
              <div className="p-5 space-y-3">
                {activeJobs.map((job) => {
                  const priorityStyle = priorityColors[job.priority];
                  return (
                    <div key={job.id} className="bg-white/60 rounded-xl p-4 border border-white/40 hover:shadow-md transition-all">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-sm text-black-text">{job.name}</h4>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${priorityStyle.bg} ${priorityStyle.text} ${priorityStyle.border}`}>
                              {job.priority.toUpperCase()}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-muted">
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {job.user}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {job.runtime}
                            </span>
                            <span>•</span>
                            <span>Nodes: {job.nodes.join(', ')}</span>
                          </div>
                        </div>
                        <span className="px-2 py-1 rounded bg-green-dim text-green text-xs font-medium">
                          {job.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-gray-muted">CPU Usage</span>
                            <span className="font-bold text-purple-primary">{job.cpuUsage}%</span>
                          </div>
                          <div className="relative h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-primary to-purple-primary/80 rounded-full"
                              style={{ width: `${job.cpuUsage}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-gray-muted">RAM Usage</span>
                            <span className="font-bold text-purple-primary">{job.ramUsage}%</span>
                          </div>
                          <div className="relative h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-primary to-purple-primary/80 rounded-full"
                              style={{ width: `${job.ramUsage}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Node Status Grid */}
            <div className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/40 bg-white/60">
                <div className="flex items-center gap-2">
                  <Server className="w-5 h-5 text-purple-primary" />
                  <h3 className="font-syne text-base font-bold text-black-text">Compute Nodes</h3>
                </div>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-2 gap-4">
                  {nodes.map((node) => {
                    const statusStyle = statusColors[node.status];
                    const cpuPercent = (node.cpu.usage).toFixed(0);
                    const ramPercent = ((node.ram.used / node.ram.total) * 100).toFixed(0);
                    const storagePercent = ((node.storage.used / node.storage.total) * 100).toFixed(0);

                    return (
                      <div key={node.id} className="bg-white/60 rounded-xl p-4 border border-white/40">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-sm text-black-text mb-1">{node.name}</h4>
                            <p className="text-xs text-gray-muted">{node.id} • {node.location}</p>
                          </div>
                          <span className={`px-2 py-1 rounded text-[10px] font-bold border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                            {node.status.toUpperCase()}
                          </span>
                        </div>

                        <div className="space-y-2 mb-3">
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-gray-muted flex items-center gap-1">
                                <Cpu className="w-3 h-3" />
                                CPU ({node.cpu.cores} cores)
                              </span>
                              <span className="font-bold text-black-text">{cpuPercent}%</span>
                            </div>
                            <div className="relative h-1 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="absolute inset-y-0 left-0 bg-purple-primary rounded-full"
                                style={{ width: `${cpuPercent}%` }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-gray-muted flex items-center gap-1">
                                <HardDrive className="w-3 h-3" />
                                RAM ({node.ram.total}GB)
                              </span>
                              <span className="font-bold text-black-text">{ramPercent}%</span>
                            </div>
                            <div className="relative h-1 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="absolute inset-y-0 left-0 bg-green rounded-full"
                                style={{ width: `${ramPercent}%` }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-gray-muted flex items-center gap-1">
                                <HardDrive className="w-3 h-3" />
                                Storage ({node.storage.total}TB)
                              </span>
                              <span className="font-bold text-black-text">{storagePercent}%</span>
                            </div>
                            <div className="relative h-1 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="absolute inset-y-0 left-0 bg-amber rounded-full"
                                style={{ width: `${storagePercent}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-white/40">
                          <div className="text-center">
                            <div className="text-[10px] text-gray-muted mb-0.5">Temp</div>
                            <div className="text-xs font-bold text-black-text">{node.cpu.temp}°C</div>
                          </div>
                          <div className="text-center">
                            <div className="text-[10px] text-gray-muted mb-0.5">Jobs</div>
                            <div className="text-xs font-bold text-purple-primary">{node.jobs}</div>
                          </div>
                          <div className="text-center">
                            <div className="text-[10px] text-gray-muted mb-0.5">Uptime</div>
                            <div className="text-xs font-bold text-black-text">{node.uptime}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
