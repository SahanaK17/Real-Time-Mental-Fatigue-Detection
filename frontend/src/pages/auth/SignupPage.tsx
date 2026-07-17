/**
 * Signup Page
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Mail, Lock, User, Building2, ArrowRight, Loader2 } from 'lucide-react';
import { authApi } from '@/api/client';
import { useAuthStore } from '@/store/authStore';

export function SignupPage() {
  const [form, setForm] = useState({
    full_name: '', email: '', username: '', password: '',
    department: '', job_title: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await authApi.signup({ ...form, role: 'employee' });
      await login(form.email, form.password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 rounded-full bg-violet-500/5 blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 rounded-full bg-cyan-500/5 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="text-center mb-8">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-xl shadow-cyan-500/20 mb-4">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold">Create account</h1>
          <p className="text-muted-foreground text-sm mt-1">Join MindGuard for real-time wellness monitoring</p>
        </div>

        <div className="glass-card rounded-2xl p-8 border border-white/8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { field: 'full_name', label: 'Full Name', icon: User, type: 'text', placeholder: 'John Doe' },
              { field: 'email', label: 'Work Email', icon: Mail, type: 'email', placeholder: 'john@company.com' },
              { field: 'username', label: 'Username', icon: User, type: 'text', placeholder: 'johndoe' },
              { field: 'password', label: 'Password', icon: Lock, type: 'password', placeholder: '••••••••' },
              { field: 'department', label: 'Department (optional)', icon: Building2, type: 'text', placeholder: 'Engineering' },
              { field: 'job_title', label: 'Job Title (optional)', icon: Building2, type: 'text', placeholder: 'Software Engineer' },
            ].map(({ field, label, icon: Icon, type, placeholder }) => (
              <div key={field} className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                  <input
                    type={type}
                    value={(form as any)[field]}
                    onChange={update(field)}
                    placeholder={placeholder}
                    required={!['department', 'job_title'].includes(field)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-sm placeholder:text-muted-foreground/40 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all"
                  />
                </div>
              </div>
            ))}

            {error && (
              <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                ⚠️ {error}
              </p>
            )}

            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold py-2.5 rounded-xl transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 mt-2"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Create Account <ArrowRight className="w-4 h-4" /></>}
            </motion.button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
