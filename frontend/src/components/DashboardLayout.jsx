import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';
import ChatbotWidget from './ChatbotWidget';
import TrainingStatusBar from './TrainingStatusBar';
import {
  LayoutDashboard,
  Database,
  Upload,
  TrendingUp,
  Activity,
  Cpu,
  Layers,
  Zap,
  Users,
  BarChart3,
  FileText,
  HardDrive,
  LogOut,
  Copyright,
  Target,
  Bell,
  Tag,
  Settings,
  PanelLeftOpen,
  PanelLeftClose,
  Award,
  Eye
} from 'lucide-react';

export default function DashboardLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || '{}'));
  const [sidebarExpanded, setSidebarExpanded] = useState(() => {
    const saved = localStorage.getItem('sidebarExpanded');
    return saved ? JSON.parse(saved) : false;
  });

  // Save sidebar state to localStorage and broadcast to modal whenever it changes
  useEffect(() => {
    localStorage.setItem('sidebarExpanded', JSON.stringify(sidebarExpanded));
    window.dispatchEvent(new CustomEvent('sidebar-toggle', { detail: { expanded: sidebarExpanded } }));
  }, [sidebarExpanded]);

  // Refresh user data on mount and route changes
  useEffect(() => {
    const refreshUserData = async () => {
      try {
        const userData = await authAPI.getCurrentUser();
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
      } catch (error) {
        console.error('Failed to refresh user data:', error);
      }
    };
    refreshUserData();
  }, [location.pathname]); // Refresh when route changes

  const handleLogout = async () => {
    try {
      await authAPI.logout();
      localStorage.removeItem('user'); // Clear cached user data
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const navSections = [
    {
      label: 'Platform',
      items: [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', badge: null },
        { icon: Upload, label: 'Data Preparation', path: '/data-preparation', badge: null },
        { icon: Database, label: 'ML Queue', path: '/ml-preparation', badge: null }
      ]
    },
    {
      label: 'Modeling',
      items: [
        { icon: Zap, label: 'Training Jobs', path: '/training', badge: null },
        { icon: Layers, label: 'Registry', path: '/models', badge: null },
        { icon: BarChart3, label: 'Comparison', path: '/model-comparison', badge: null },
        { icon: Eye, label: 'Explainability', path: '/explainability', badge: null }
      ]
    },
    {
      label: 'Clinical Operations',
      items: [
        { icon: Upload, label: 'Predictions', path: '/batch-prediction', badge: null },
        { icon: Award, label: 'Patient Scoring', path: '/scorecard', badge: null },
        { icon: Database, label: 'Clinical Review', path: '/data-catalog', badge: null }
      ]
    }
  ];

  const currentPath = window.location.pathname;

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
      {/* Sidebar */}
      <aside
        className="fixed left-0 top-0 h-screen flex flex-col transition-all duration-300 ease-out overflow-hidden"
        style={{ 
          width: sidebarExpanded ? '200px' : '64px', 
          zIndex: 9999,
          fontSize: '80%',
          background: 'linear-gradient(180deg, #0A0118 0%, #120325 45%, #1A0633 100%)',
          backgroundImage: `
            linear-gradient(180deg, #0A0118 0%, #120325 45%, #1A0633 100%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E")
          `,
          backgroundBlendMode: 'overlay'
        }}
      >
        {/* Soft atmospheric glow at top */}
        <div
          className={`absolute w-[240px] h-[180px] -top-20 -left-10 rounded-full pointer-events-none transition-opacity duration-300 ${
            sidebarExpanded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{ background: 'radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, rgba(124, 58, 237, 0.08) 40%, transparent 70%)' }}
        />

        {/* Brand with Toggle */}
        <div className="h-16 flex items-center justify-center gap-2.5 px-3 border-b border-white/[0.06] relative z-10" style={{ paddingTop: '8px' }}>
          <button
            onClick={() => setSidebarExpanded(!sidebarExpanded)}
            className="group/toggle flex-shrink-0 relative transition-all cursor-pointer"
            title={sidebarExpanded ? 'Close sidebar' : 'Open sidebar'}
          >
            <img src="/Logo/MyAria-I Logo.png" alt="MyAria-i Logo" className="w-8 h-8 object-contain" />
            
            {/* Hover tooltip when collapsed */}
            {!sidebarExpanded && (
              <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap opacity-0 group-hover/toggle:opacity-100 transition-opacity pointer-events-none">
                Open sidebar
                <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
              </div>
            )}
          </button>
          
          <span className={`font-syne font-extrabold text-[15px] text-white tracking-wide transition-opacity duration-200 whitespace-nowrap flex items-center gap-1.5 ${
            sidebarExpanded ? 'opacity-100' : 'opacity-0'
          }`}>
            MyAria-i
            <Copyright className="w-3 h-3" />
          </span>
          
          {/* Close button when expanded */}
          {sidebarExpanded && (
            <button
              onClick={() => setSidebarExpanded(false)}
              className="ml-auto p-1.5 rounded-md hover:bg-white/[0.08] text-white/[0.42] hover:text-white/[0.78] transition-all cursor-pointer"
              title="Close sidebar"
            >
              <PanelLeftClose className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <div className="pt-6 pb-4 overflow-y-auto flex-1 scrollbar-hide" style={{ paddingTop: '24px' }}>
          {navSections.map((section, idx) => (
            <div key={idx} className="mb-1 pb-4">
              <div className={`px-4 pb-2 transition-opacity duration-150 pointer-events-none ${
                sidebarExpanded ? 'opacity-100' : 'opacity-0'
              }`}>
                <span className="text-[9px] font-medium tracking-[0.12em] uppercase text-white/30 whitespace-nowrap">
                  {section.label}
                </span>
              </div>
              <nav className="space-y-0.5 px-2">
                {section.items.map((item, i) => {
                  const Icon = item.icon;
                  const isActive = currentPath === item.path;
                  return (
                    <button
                      key={i}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Clicking:', item.label, item.path);
                        navigate(item.path);
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2.5 transition-all duration-250 relative group/item cursor-pointer rounded-2xl ${
                        isActive
                          ? 'text-white'
                          : 'text-white/70 hover:text-white hover:bg-white/[0.04]'
                      }`}
                      style={{ 
                        pointerEvents: 'auto',
                        backgroundColor: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                        backdropFilter: isActive ? 'blur(12px)' : 'none',
                        border: isActive ? '1px solid rgba(255,255,255,0.08)' : '1px solid transparent',
                        transform: 'translateX(0)',
                        transitionProperty: 'all'
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.transform = 'translateX(4px)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateX(0)';
                      }}
                    >
                      {/* Left glowing indicator for active state */}
                      {isActive && (
                        <div 
                          className="absolute -left-2 top-1/2 -translate-y-1/2 w-1 h-7 rounded-r-full pointer-events-none" 
                          style={{ 
                            background: 'linear-gradient(180deg, #A855F7, #7C3AED)',
                            boxShadow: '0 0 20px rgba(168,85,247,0.4)'
                          }} 
                        />
                      )}
                      <Icon className="w-[15px] h-[15px] flex-shrink-0 pointer-events-none" strokeWidth={1.5} />
                      <span className={`text-[13px] font-normal transition-opacity duration-150 whitespace-nowrap pointer-events-none ${
                        sidebarExpanded ? 'opacity-100' : 'opacity-0'
                      }`}>
                        {item.label}
                      </span>
                      {item.badge && (
                        <span className={`ml-auto text-[8px] font-semibold px-1.5 py-0.5 rounded-full text-white transition-opacity duration-150 pointer-events-none ${
                          sidebarExpanded ? 'opacity-100' : 'opacity-0'
                        }`}
                        style={{ backgroundColor: '#6b46c1' }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        {/* Bottom section: Powered by + User */}
        <div className="px-3 pb-3 mt-auto">
          {/* Powered by */}
          <div className={`mb-3 transition-opacity duration-150 ${
            sidebarExpanded ? 'opacity-100' : 'opacity-0'
          }`}>
            <div className="text-[9px] text-white/[0.28] text-left font-medium">
              powered by
            </div>
            <div
              className="text-[11px] text-left font-bold tracking-wide"
              style={{
                background: 'linear-gradient(90deg, #D4AF37, #FFD700)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Aras Integrasi Sdn. Bhd.
            </div>
          </div>

          {/* Premium Glass User Profile Strip */}
          <div 
            className="rounded-2xl transition-all duration-300 flex items-center justify-center"
            style={{
              background: sidebarExpanded ? 'rgba(255,255,255,0.08)' : 'transparent',
              backdropFilter: sidebarExpanded ? 'blur(12px)' : 'none',
              border: sidebarExpanded ? '1px solid rgba(255,255,255,0.08)' : '1px solid transparent',
              boxShadow: sidebarExpanded ? 'inset 0 1px 0 rgba(255,255,255,0.15), 0 8px 32px rgba(0,0,0,0.12)' : 'none',
              padding: sidebarExpanded ? '10px' : '8px',
              gap: sidebarExpanded ? '10px' : '0',
            }}
          >
            <button
              onClick={() => navigate('/profile')}
              className="relative w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 hover:scale-105 transition-transform cursor-pointer"
              style={{
                background: 'linear-gradient(135deg, #A855F7, #7C3AED)',
                boxShadow: '0 4px 12px rgba(168,85,247,0.3)'
              }}
              title={sidebarExpanded ? user?.full_name : 'Open sidebar to view profile'}
            >
              <span className="font-syne text-[11px] font-bold text-white">
                {user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'U'}
              </span>
              {/* Online indicator */}
              <div 
                className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2"
                style={{
                  background: 'linear-gradient(135deg, #10B981, #059669)',
                  borderColor: '#1A0633',
                  boxShadow: '0 0 8px rgba(16,185,129,0.5)'
                }}
              />
            </button>
            
            <button
              onClick={() => navigate('/profile')}
              className={`overflow-hidden flex-1 text-left cursor-pointer transition-opacity duration-150 ${
                sidebarExpanded ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <div className="text-[11px] font-semibold text-white whitespace-nowrap truncate">{user?.full_name || 'User'}</div>
              <div className="text-[9px] text-white/[0.42] whitespace-nowrap capitalize">{user?.role || 'AI Engineer'}</div>
            </button>
            
            <button
              onClick={handleLogout}
              className={`ml-auto p-1.5 rounded-lg hover:bg-white/[0.08] text-white/[0.42] hover:text-white cursor-pointer transition-all duration-150 ${
                sidebarExpanded ? 'opacity-100' : 'opacity-0'
              }`}
              title="Logout"
            >
              <LogOut className="w-3.5 h-3.5" strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div 
        className="flex-1 flex flex-col transition-all duration-300 ease-out" 
        style={{ marginLeft: sidebarExpanded ? '200px' : '64px' }}
      >
        {/* Global Training Status Bar (appears on all pages when training is active) */}
        <TrainingStatusBar />
        
        <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
        
        {/* Footer */}
        <footer className="bg-white/60 dark:bg-[#0F0F11] backdrop-blur-sm border-t border-white/40 dark:border-white/[0.06] py-3 px-6 transition-colors">
          <div className="max-w-7xl mx-auto flex items-center justify-center gap-4">
            <span className="text-base text-gray-muted dark:text-gray-400 font-semibold">Powered by</span>
            <img 
              src="/Logo/Aras Integrasi - Logo.png" 
              alt="Aras Integrasi Logo" 
              className="h-16 object-contain"
            />
          </div>
        </footer>
      </div>

      {/* AI Assistant Chatbot Widget */}
      <ChatbotWidget />
    </div>
  );
}
