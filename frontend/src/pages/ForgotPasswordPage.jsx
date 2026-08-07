import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import myAriaLogo from '../assets/myaria-logo.png';
import { Mail, ArrowRight, ArrowLeft, Check, Copyright } from 'lucide-react';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: Implement forgot password API call
      // await authAPI.forgotPassword(email);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
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
                  <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center p-1.5">
                    <img src={myAriaLogo} alt="MyAria-i Logo" className="w-full h-full object-contain" />
                  </div>
                  <span className="font-syne text-2xl font-bold text-white flex items-center gap-2">
                    MyAria-i
                    <Copyright className="w-4 h-4" />
                  </span>
                </div>
                
                {/* Success Icon */}
                <div className="relative z-10 flex justify-center mb-8">
                  <div className="w-24 h-24 rounded-full bg-purple-primary/20 flex items-center justify-center">
                    <div className="w-20 h-20 rounded-full bg-purple-primary flex items-center justify-center">
                      <Check className="w-12 h-12 text-white" strokeWidth={3} />
                    </div>
                  </div>
                </div>
                
                {/* Headline */}
                <div className="relative z-10 text-center mb-12">
                  <h1 className="font-syne text-4xl font-bold text-white leading-tight mb-4">
                    Check your email
                  </h1>
                  <p className="text-purple-light/70 text-lg leading-relaxed">
                    We've sent password reset instructions to your email address.
                  </p>
                </div>
              </div>
              
              {/* Right Panel - Light with Success Message */}
              <div className="bg-white p-panel flex flex-col justify-center">
                <div className="max-w-md mx-auto w-full text-center">
                  
                  <div className="mb-8">
                    <div className="w-16 h-16 rounded-full bg-purple-dim mx-auto mb-6 flex items-center justify-center">
                      <Mail className="w-8 h-8 text-purple-primary" />
                    </div>
                    
                    <h2 className="font-syne text-2xl font-bold text-black-cta mb-3">
                      Reset link sent!
                    </h2>
                    <p className="text-gray-muted mb-2">
                      We sent an email to:
                    </p>
                    <p className="font-medium text-black-cta mb-6">
                      {email}
                    </p>
                    <p className="text-sm text-gray-muted mb-8">
                      Click the link in the email to reset your password. The link will expire in 1 hour.
                    </p>
                  </div>
                  
                  <div className="space-y-4">
                    <button
                      onClick={() => navigate('/login')}
                      className="btn-primary w-full group"
                    >
                      <ArrowLeft className="w-5 h-5" />
                      <span>Back to login</span>
                    </button>
                    
                    <button
                      onClick={() => {
                        setSubmitted(false);
                        setEmail('');
                      }}
                      className="w-full text-purple-primary font-medium hover:underline"
                    >
                      Didn't receive the email? Resend
                    </button>
                  </div>
                  
                  <p className="text-caption mt-8">
                    Check your spam folder if you don't see the email within a few minutes.
                  </p>
                </div>
              </div>
              
            </div>
          </div>
        </div>
      </div>
    );
  }

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
                <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center p-1.5">
                  <img src={myAriaLogo} alt="MyAria-i Logo" className="w-full h-full object-contain" />
                </div>
                <span className="font-syne text-2xl font-bold text-white flex items-center gap-2">
                  MyAria-i
                  <Copyright className="w-4 h-4" />
                </span>
              </div>
              
              {/* Headline */}
              <div className="relative z-10 mb-12">
                <h1 className="font-syne text-4xl md:text-5xl font-bold text-white leading-tight mb-4">
                  Reset your<br />
                  <span className="text-purple-light">password.</span>
                </h1>
                <p className="text-purple-light/70 text-lg leading-relaxed">
                  Enter your email address and we'll send you instructions to reset your password.
                </p>
              </div>
              
              {/* Security Note */}
              <div className="relative z-10 bg-purple-primary/10 border border-purple-primary/20 rounded-lg p-6">
                <h3 className="font-syne font-semibold text-white mb-2">Secure Reset</h3>
                <p className="text-purple-light/60 text-sm leading-relaxed">
                  For your security, the reset link will expire after 1 hour and can only be used once.
                </p>
              </div>
            </div>
            
            {/* Right Panel - Light with Form */}
            <div className="bg-white p-panel flex flex-col justify-center">
              <div className="max-w-md mx-auto w-full">
                
                {/* Back Button */}
                <button
                  onClick={() => navigate('/login')}
                  className="flex items-center gap-2 text-gray-muted hover:text-purple-primary transition-colors mb-8"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="text-sm font-medium">Back to login</span>
                </button>
                
                <h2 className="font-syne text-3xl font-bold text-black-cta mb-2">Forgot password?</h2>
                <p className="text-gray-muted mb-8">No worries, we'll send you reset instructions.</p>
                
                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}
                
                {/* Reset Form */}
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-muted mb-2">
                      Email address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-muted input-icon transition-colors duration-[180ms]" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="researcher@myaria.com"
                        className="input-field w-full pl-12"
                        required
                      />
                    </div>
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full group"
                  >
                    {loading ? (
                      <span>Sending...</span>
                    ) : (
                      <>
                        <span>Send reset instructions</span>
                        <ArrowRight className="w-5 h-5 arrow-icon transition-transform duration-150" />
                      </>
                    )}
                  </button>
                </form>
                
                <p className="text-caption text-center mt-8">
                  Remember your password?{' '}
                  <button 
                    onClick={() => navigate('/login')}
                    className="text-purple-primary hover:underline font-medium"
                  >
                    Sign in
                  </button>
                </p>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
}
