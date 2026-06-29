import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Check, AlertCircle, Copyright } from 'lucide-react';
import { authAPI } from '../services/api';

export default function SignUpPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    agreeToTerms: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});

  const validateForm = () => {
    const errors = {};
    
    // Username validation
    if (!formData.username) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, and underscores';
    }
    
    // Email validation
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])/.test(formData.password)) {
      errors.password = 'Password must include uppercase, lowercase, number, and special character';
    }
    
    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    // Full name validation
    if (!formData.fullName || formData.fullName.trim().length < 2) {
      errors.fullName = 'Full name is required';
    }
    
    // Terms validation
    if (!formData.agreeToTerms) {
      errors.agreeToTerms = 'You must agree to the Terms and Privacy Policy';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);

    try {
      await authAPI.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName
      });
      
      // Redirect to login page with success message
      navigate('/login', { state: { message: 'Account created! Please sign in.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors({ ...validationErrors, [field]: '' });
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-purple-900/50 overflow-hidden flex items-center justify-center p-6" style={{ zoom: 0.75 }}>
      
      {/* Blurred gradient blobs - Medical AI aesthetic */}
      <div className="absolute top-[-150px] left-[-150px] w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-[-100px] right-[-100px] w-[400px] h-[400px] bg-blue-400/15 rounded-full blur-3xl"></div>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-purple-300/10 rounded-full blur-3xl"></div>
      
      <div className="relative z-10 w-full max-w-6xl animate-fade-up">
        <div className="bg-white/95 backdrop-blur-xl rounded-card shadow-2xl overflow-hidden">
          <div className="grid md:grid-cols-2 min-h-[700px]">
            
            {/* Left Panel - Dark with DNA theme */}
            <div className="relative bg-black-cta p-panel overflow-hidden">
              {/* DNA Blobs */}
              <div className="dna-blob dna-blob-1"></div>
              <div className="dna-blob dna-blob-2"></div>
              
              {/* Logo */}
              <div className="relative z-10 flex items-center gap-3 mb-12">
                <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center p-1.5">
                  <img src="/Logo/MyAria-I Logo.png" alt="MyAria-i Logo" className="w-full h-full object-contain" />
                </div>
                <span className="font-syne text-2xl font-bold text-white flex items-center gap-2">
                  MyAria-i
                  <Copyright className="w-4 h-4" />
                </span>
              </div>
              
              {/* Headline */}
              <div className="relative z-10 mb-12">
                <h1 className="font-syne text-4xl md:text-5xl font-bold text-white leading-tight mb-4">
                  Join the future of<br />
                  <span className="text-purple-light">autoimmune research.</span>
                </h1>
                <p className="text-purple-light/70 text-lg leading-relaxed">
                  Create your MyAria-i account and start leveraging AI-powered insights for autoimmune disease analysis.
                </p>
              </div>
              
              {/* Feature List */}
              <div className="relative z-10 space-y-4">
                <div className="flex items-start gap-3 animate-feature-1">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">Secure</h3>
                    <p className="text-purple-light/60 text-sm">Your research data is protected with enterprise-grade security</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 animate-feature-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">Role-based access control</h3>
                    <p className="text-purple-light/60 text-sm">Collaborate with your team with appropriate permissions</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 animate-feature-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-5 h-5 text-purple-light" />
                  </div>
                  <div>
                    <h3 className="font-syne font-semibold text-white mb-1">Advanced ML models</h3>
                    <p className="text-purple-light/60 text-sm">Access cutting-edge machine learning for disease prediction</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right Panel - Light with Form */}
            <div className="bg-white p-panel flex flex-col justify-center">
              <div className="max-w-md mx-auto w-full">
                
                {/* Header */}
                <div className="text-right mb-8">
                  <span className="text-gray-muted text-sm">Already have an account? </span>
                  <button 
                    onClick={() => navigate('/login')}
                    className="text-purple-primary font-medium text-sm hover:underline"
                  >
                    Log in
                  </button>
                </div>
                
                <h2 className="font-syne text-3xl font-bold text-black-cta mb-2">Create your account</h2>
                <p className="text-gray-muted mb-8">Get started with MyAria-i today.</p>
                
                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}
                
                {/* Sign Up Form */}
                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* Full Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Full name*
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="text"
                        value={formData.fullName}
                        onChange={(e) => handleInputChange('fullName', e.target.value)}
                        placeholder="Dr. Jane Smith"
                        className={`input-field w-full pl-12 ${validationErrors.fullName ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {validationErrors.fullName && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.fullName}</p>
                    )}
                  </div>
                  
                  {/* Username */}
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Username*
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => handleInputChange('username', e.target.value)}
                        placeholder="janesmith"
                        className={`input-field w-full pl-12 ${validationErrors.username ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {validationErrors.username && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.username}</p>
                    )}
                  </div>
                  
                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Email address*
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="researcher@myaria.com"
                        className={`input-field w-full pl-12 ${validationErrors.email ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {validationErrors.email && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.email}</p>
                    )}
                  </div>
                  
                  {/* Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Password*
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="password"
                        value={formData.password}
                        onChange={(e) => handleInputChange('password', e.target.value)}
                        placeholder="••••••••"
                        className={`input-field w-full pl-12 ${validationErrors.password ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {validationErrors.password && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.password}</p>
                    )}
                    {!validationErrors.password && (
                      <p className="text-xs text-gray-muted mt-1">
                        Min 8 chars with uppercase, lowercase, number & special character
                      </p>
                    )}
                  </div>
                  
                  {/* Confirm Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Confirm password*
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="password"
                        value={formData.confirmPassword}
                        onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                        placeholder="••••••••"
                        className={`input-field w-full pl-12 ${validationErrors.confirmPassword ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {validationErrors.confirmPassword && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.confirmPassword}</p>
                    )}
                  </div>
                  
                  {/* Terms Agreement */}
                  <div>
                    <label className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={formData.agreeToTerms}
                        onChange={(e) => handleInputChange('agreeToTerms', e.target.checked)}
                        className={`w-4 h-4 mt-0.5 border-gray-300 rounded text-purple-primary focus:ring-purple-primary ${validationErrors.agreeToTerms ? 'border-red-500' : ''}`}
                      />
                      <span className="text-sm text-gray-muted">
                        I agree to the{' '}
                        <a href="#" className="text-purple-primary hover:underline font-medium">Terms of Service</a>
                        {' '}and{' '}
                        <a href="#" className="text-purple-primary hover:underline font-medium">Privacy Policy</a>
                      </span>
                    </label>
                    {validationErrors.agreeToTerms && (
                      <p className="text-xs text-red-600 mt-1">{validationErrors.agreeToTerms}</p>
                    )}
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full group"
                  >
                    {loading ? (
                      <span>Creating account...</span>
                    ) : (
                      <>
                        <span>Create account</span>
                        <ArrowRight className="w-5 h-5 arrow-icon transition-transform duration-150" />
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
}
