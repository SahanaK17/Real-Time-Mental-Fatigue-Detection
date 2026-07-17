/** Settings & 404 pages */
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { Link } from 'react-router-dom';

export function SettingsPage() {
  const { user } = useAuthStore();
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="glass-card rounded-2xl p-6 border border-white/8 space-y-4">
        <h2 className="font-semibold">Profile</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          {[
            ['Full Name', user?.full_name],
            ['Email', user?.email],
            ['Username', user?.username],
            ['Role', user?.role],
            ['Department', user?.department || '—'],
            ['Job Title', user?.job_title || '—'],
          ].map(([label, value]) => (
            <div key={label}>
              <p className="text-muted-foreground text-xs mb-0.5">{label}</p>
              <p className="font-medium capitalize">{String(value)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 border border-white/8">
        <h2 className="font-semibold mb-4">Notifications</h2>
        <div className="space-y-3">
          {[
            { label: 'Browser notifications', sublabel: 'Get alerts in browser when fatigue is high' },
            { label: 'Email alerts', sublabel: 'Receive daily summary emails' },
            { label: 'Break reminders', sublabel: 'Notify when a break is recommended' },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
              <div>
                <p className="text-sm font-medium">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.sublabel}</p>
              </div>
              <div className="w-9 h-5 rounded-full bg-cyan-500/20 border border-cyan-500/30 cursor-pointer relative">
                <div className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-cyan-400 shadow-sm transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 border border-white/8">
        <h2 className="font-semibold mb-2">Privacy</h2>
        <p className="text-sm text-muted-foreground">
          MindGuard is privacy-first. No keystrokes, screenshots, or personal content is ever stored.
          Only anonymized timing metrics are processed. All data is encrypted in transit and at rest.
        </p>
      </div>
    </motion.div>
  );
}
