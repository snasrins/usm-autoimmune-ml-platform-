import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import myAriaLogo from '../assets/myaria-logo.png';
import { User, Lock, ArrowRight, Check, Copyright } from 'lucide-react';
import { authAPI } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the message after 5 seconds
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(formData.username, formData.password);
      
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Fetch and store user data
      try {
        const userData = await authAPI.getCurrentUser();
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (userError) {
        console.error('Failed to fetch user data:', userError);
      }
      
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-gray-900 to-purple-900/50 overflow-hidden flex items-center justify-center p-6" style={{ zoom: 0.9 }}>
      
      {/* Blurred gradient blobs - Medical AI aesthetic */}
      <div className="absolute top-[-150px] left-[-150px] w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-[-100px] right-[-100px] w-[400px] h-[400px] bg-blue-400/15 rounded-full blur-3xl"></div>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-purple-300/10 rounded-full blur-3xl"></div>
      
      <div className="relative z-10 w-full max-w-6xl animate-fade-up">
        <div className="bg-white/95 backdrop-blur-xl rounded-card shadow-2xl overflow-hidden">
          <div className="grid md:grid-cols-2 min-h-[600px]">
            
            {/* Left Panel - Dark with DNA theme */}
            <div className="relative bg-black-cta p-panel overflow-hidden">
              {/* DNA Blobs */}
              <div className="dna-blob dna-blob-1"></div>
              <div className="dna-blob dna-blob-2"></div>
              
              {/* Logo */}
              <div className="relative z-10 flex items-center gap-3 mb-12">
                <img src={myAriaLogo} alt="MyAria-i Logo" className="w-16 h-16 object-contain" />
                <span className="font-syne text-2xl font-bold text-white flex items-center gap-2">
                  MyAria-i
                  <Copyright className="w-4 h-4" />
                </span>
              </div>
              
              {/* Headline */}
              <div className="relative z-10 mb-12">
                <h1 className="font-syne text-4xl md:text-5xl font-bold text-white leading-tight mb-4">
                  Your autoimmune,<br />
                  <span className="text-purple-light">decoded.</span>
                </h1>
                <p className="text-purple-light/70 text-lg leading-relaxed">
                  Sign in to access your personalized ML analysis, health insights, and research tools.
                </p>
              </div>
              
              {/* Feature List */}
              <div className="relative z-10 space-y-4">
                <div className="flex items-start gap-3 animate-feature-1">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">Real-time ML analysis & prediction</h3>
                    <p className="text-purple-light/60 text-sm">Advanced machine learning models for autoimmune disease detection</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 animate-feature-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">Biomarker & risk tracking</h3>
                    <p className="text-purple-light/60 text-sm">Track lab results and longitudinal health data</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 animate-feature-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">AI-powered research tools</h3>
                    <p className="text-purple-light/60 text-sm">Exploratory data analysis and model training</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right Panel - Light with Form */}
            <div className="bg-white p-panel flex flex-col justify-center">
              <div className="max-w-md mx-auto w-full">
                
                {/* Header */}
                <div className="text-right mb-8">
                  <span className="text-gray-muted text-sm">No account? </span>
                  <button 
                    onClick={() => navigate('/signup')}
                    className="text-purple-primary font-medium text-sm hover:underline"
                  >
                    Sign up
                  </button>
                </div>
                
                <h2 className="font-syne text-3xl font-bold text-black-cta mb-2">Welcome back</h2>
                <p className="text-gray-muted mb-8">Sign in to your MyAria-i account.</p>
                
                {/* Success Message */}
                {successMessage && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-green-600">{successMessage}</p>
                  </div>
                )}
                
                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}
                
                {/* Login Form */}
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Username
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        placeholder="Username123"
                        className="input-field w-full pl-12"
                        required
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="••••••••"
                        className="input-field w-full pl-12"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.rememberMe}
                        onChange={(e) => setFormData({ ...formData, rememberMe: e.target.checked })}
                        className="w-4 h-4 border-gray-300 rounded text-purple-primary focus:ring-purple-primary"
                      />
                      <span className="text-sm text-gray-muted">Keep me signed in</span>
                    </label>
                    
                    <button
                      type="button"
                      onClick={() => navigate('/forgot-password')}
                      className="text-sm text-purple-primary hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full group"
                  >
                    {loading ? (
                      <span>Signing in...</span>
                    ) : (
                      <>
                        <span>Sign in to MyAria-i</span>
                        <ArrowRight className="w-5 h-5 arrow-icon transition-transform duration-150" />
                      </>
                    )}
                  </button>
                </form>
                
                <p className="text-caption text-center mt-8">
                  By signing in, you agree to our{' '}
                  <a href="/terms" className="text-purple-primary hover:underline">Terms of Service</a>
                  {' '}and{' '}
                  <a href="/privacy" className="text-purple-primary hover:underline">Privacy Policy</a>
                </p>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
}
