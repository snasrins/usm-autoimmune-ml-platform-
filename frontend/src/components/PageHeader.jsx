import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Search, Bell, ChevronRight, X } from 'lucide-react';

/**
 * Standardized Page Header Component
 * Used across all pages for consistent navigation and branding
 * 
 * @param {string} title - Page title (e.g., "Dashboard", "Data Preparation")
 * @param {string} subtitle - Page subtitle for breadcrumb (defaults to title if not provided)
 * @param {object} user - User object with username property
 */
export default function PageHeader({ title, subtitle, user }) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);

  // Searchable pages
  const searchablePages = [
    { title: 'Dashboard', route: '/dashboard', keywords: ['home', 'overview', 'stats', 'metrics'] },
    { title: 'Data Preparation', route: '/data-preparation', keywords: ['prep', 'preprocessing', 'labeling', 'label', 'transform'] },
    { title: 'ML Queue', route: '/ml-preparation', keywords: ['ml', 'queue', 'preparation', 'preprocessing'] },
    { title: 'Training Jobs', route: '/training', keywords: ['train', 'model', 'ml', 'machine learning', 'algorithms'] },
    { title: 'Model Registry', route: '/models', keywords: ['models', 'registry', 'deployed', 'versions'] },
    { title: 'Model Comparison', route: '/model-comparison', keywords: ['compare', 'performance', 'metrics', 'accuracy'] },
    { title: 'Explainability', route: '/explainability', keywords: ['shap', 'explain', 'interpret', 'why', 'feature importance'] },
    { title: 'Predictions', route: '/batch-prediction', keywords: ['predict', 'inference', 'forecast', 'test', 'batch', 'bulk'] },
    { title: 'Patient Scoring', route: '/scorecard', keywords: ['scorecard', 'scoring', 'patient', 'clinical'] },
    { title: 'Clinical Review', route: '/data-catalog', keywords: ['clinical', 'review', 'data', 'catalog'] },
  ];

  // Search handler
  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.trim() === '') {
      setSearchResults([]);
      return;
    }

    const lowerQuery = query.toLowerCase();
    const results = searchablePages.filter(page => 
      page.title.toLowerCase().includes(lowerQuery) ||
      page.keywords.some(keyword => keyword.includes(lowerQuery))
    );
    setSearchResults(results);
  };

  const navigateToPage = (route) => {
    navigate(route);
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  return (
    <div className="h-[70px] flex items-center gap-8 px-6 bg-white border-b border-[#e2e8f0] flex-shrink-0 backdrop-blur-md transition-colors relative z-10">
      <div className="flex flex-col gap-1">
        <h1 className="font-syne text-[18px] font-bold text-[#1a0a2e] leading-none">{title}</h1>
        <div className="flex items-center gap-3 text-[12px] text-[#4a5568]">
          <span>USM Autoimmune ML Platform</span>
          <ChevronRight className="w-4 h-4" />
          <span className="text-[#6b46c1]">{subtitle || title}</span>
        </div>
      </div>
      
      {/* Right side: Search + Actions */}
      <Tooltip.Provider delayDuration={300}>
        <div className="ml-auto flex items-center gap-3">
          {/* Search button/input */}
          <button
            onClick={() => setShowSearch(true)}
            className="relative z-10 flex items-center gap-2 px-3 py-1.5 rounded-md bg-white border border-[#e2e8f0] transition-all hover:border-[#6b46c1]/50 w-64"
          >
            <Search className="w-3.5 h-3.5 text-[#4a5568] flex-shrink-0" />
            <span className="text-[12px] text-[#4a5568]">Search pages...</span>
            <kbd className="ml-auto px-1.5 py-0.5 text-[10px] font-semibold text-gray-500 bg-gray-100 border border-gray-200 rounded">⌘K</kbd>
          </button>
          
          {/* Search Modal - Fixed positioning */}
          {showSearch && (
            <>
              {/* Backdrop */}
              <div 
                className="fixed inset-0 z-[9998] bg-black/20"
                onClick={() => {
                  setShowSearch(false);
                  setSearchQuery('');
                  setSearchResults([]);
                }}
              />
              
              {/* Search Panel - Centered in viewport */}
              <div className="fixed top-24 left-1/2 transform -translate-x-1/2 z-[9999] w-[600px] bg-white border border-gray-200 rounded-2xl shadow-2xl">
                  {/* Search Input */}
                  <div className="flex items-center p-4 border-b border-gray-200">
                    <Search className="w-4 h-4 text-gray-400 mr-3" />
                    <input
                      type="text"
                      placeholder="Search for pages, settings, or features..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      className="flex-1 outline-none text-sm"
                      autoFocus
                    />
                    <button
                      onClick={() => {
                        setShowSearch(false);
                        setSearchQuery('');
                        setSearchResults([]);
                      }}
                      className="ml-2 p-1 hover:bg-gray-100 rounded"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                  
                  {/* Search Results */}
                  <div className="max-h-96 overflow-y-auto">
                    {searchQuery === '' ? (
                      <div className="p-4 text-sm text-gray-500">
                        <p className="font-medium mb-2">Quick Access</p>
                        {searchablePages.slice(0, 6).map((page, i) => (
                          <button
                            key={i}
                            onClick={() => navigateToPage(page.route)}
                            className="w-full text-left px-3 py-2 hover:bg-purple-50 rounded-lg flex items-center justify-between group"
                          >
                            <span className="text-gray-700">{page.title}</span>
                            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600" />
                          </button>
                        ))}
                      </div>
                    ) : searchResults.length > 0 ? (
                      <div className="p-2">
                        {searchResults.map((result, i) => (
                          <button
                            key={i}
                            onClick={() => navigateToPage(result.route)}
                            className="w-full text-left px-4 py-3 hover:bg-purple-50 rounded-lg flex items-center justify-between group transition-colors"
                          >
                            <div>
                              <div className="font-medium text-gray-900">{result.title}</div>
                              <div className="text-xs text-gray-500 mt-0.5">{result.route}</div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600" />
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="p-8 text-center">
                        <div className="text-gray-400 mb-2">
                          <Search className="w-8 h-8 mx-auto" />
                        </div>
                        <p className="text-sm text-gray-500">No results found for "{searchQuery}"</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          
          <Tooltip.Root>
            <Tooltip.Trigger asChild>
              <button className="relative w-8 h-8 rounded-lg bg-[#f7f7f7] border border-[#e2e8f0] flex items-center justify-center hover:border-[#6b46c1]/30 transition-all">
                <Bell className="w-3.5 h-3.5 text-[#4a5568]" />
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-[#DC2626] rounded-full border-2 border-white"></span>
              </button>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
                Notifications (3)
                <Tooltip.Arrow className="fill-gray-900" />
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>

          {/* Separator */}
          <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

          <Tooltip.Root>
            <Tooltip.Trigger asChild>
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-2 h-10 rounded-lg hover:bg-[#f7f7f7] transition-all"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#6b46c1] to-[#9f7aea] flex items-center justify-center text-white font-bold text-sm shadow-md">
                  {(user?.username || user?.full_name || 'U').substring(0, 2).toUpperCase()}
                </div>
                <span className="text-sm font-medium text-[#1a0a2e]">
                  {user?.username || user?.full_name || 'User'}
                </span>
              </button>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
                Open Profile
                <Tooltip.Arrow className="fill-gray-900" />
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        </div>
      </Tooltip.Provider>
    </div>
  );
}
