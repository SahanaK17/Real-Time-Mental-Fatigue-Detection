/** Admin Page */
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { adminApi } from '@/api/client';
import { Users, Activity, AlertTriangle, Zap, Download, FileText } from 'lucide-react';

export function AdminPage() {
  const { data: stats } = useQuery({ queryKey: ['admin-stats'], queryFn: adminApi.getStats });
  const { data: highRisk } = useQuery({ queryKey: ['high-risk'], queryFn: () => adminApi.getHighRisk(0.7) });
  const { data: users } = useQuery({ queryKey: ['admin-users'], queryFn: () => adminApi.getUsers() });

  const handleExportCsv = async () => {
    try {
      const blob = await adminApi.exportCsv();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fatigue_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      console.error('Failed to export CSV', e);
    }
  };

  const handleExportPdf = async () => {
    try {
      const blob = await adminApi.exportPdf();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `admin_report_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      console.error('Failed to export PDF', e);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          <p className="text-muted-foreground text-sm mt-1">Platform-wide monitoring and user management</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleExportCsv}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm transition-colors"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button 
            onClick={handleExportPdf}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-violet-500/20 hover:from-cyan-500/30 hover:to-violet-500/30 border border-cyan-500/20 rounded-lg text-sm transition-colors text-cyan-50"
          >
            <FileText className="w-4 h-4" /> Export PDF
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Users', value: stats?.total_users ?? '—', icon: Users, color: 'cyan' },
          { label: 'Active Sessions', value: stats?.active_sessions ?? '—', icon: Activity, color: 'emerald' },
          { label: 'Predictions (24h)', value: stats?.predictions_last_24h ?? '—', icon: Zap, color: 'violet' },
          { label: 'Avg Fatigue (24h)', value: stats ? `${(stats.avg_fatigue_score_last_24h * 100).toFixed(0)}%` : '—', icon: AlertTriangle, color: 'amber' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card rounded-xl p-4 border border-white/8">
            <div className="text-2xl font-bold">{String(stat.value)}</div>
            <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* High Risk Users */}
      {highRisk?.high_risk_users?.length > 0 && (
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <h2 className="font-semibold">High-Risk Users (last 24h)</h2>
            <span className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full ml-auto">
              {highRisk.high_risk_users.length} users
            </span>
          </div>
          <div className="space-y-2">
            {highRisk.high_risk_users.map((u: any) => (
              <div key={u.user_id} className="flex items-center justify-between p-3 rounded-xl bg-red-500/5 border border-red-500/10">
                <div>
                  <p className="font-medium text-sm">{u.full_name}</p>
                  <p className="text-xs text-muted-foreground">{u.email} · {u.department}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-red-400">{(u.avg_fatigue_score * 100).toFixed(0)}%</p>
                  <p className="text-xs text-muted-foreground">avg fatigue</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Users Table */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-4 h-4 text-cyan-400" />
          <h2 className="font-semibold">All Users</h2>
          <span className="text-xs text-muted-foreground ml-auto">{users?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-white/5">
                {['Name', 'Email', 'Role', 'Department', 'Status'].map(h => (
                  <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {(users?.users ?? []).map((u: any) => (
                <tr key={u.id} className="hover:bg-white/3 transition-colors">
                  <td className="py-2.5 pr-4 font-medium">{u.full_name}</td>
                  <td className="py-2.5 pr-4 text-muted-foreground">{u.email}</td>
                  <td className="py-2.5 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      u.role === 'admin' ? 'bg-violet-500/10 text-violet-400' :
                      u.role === 'researcher' ? 'bg-amber-500/10 text-amber-400' :
                      'bg-cyan-500/10 text-cyan-400'
                    }`}>{u.role}</span>
                  </td>
                  <td className="py-2.5 pr-4 text-muted-foreground">{u.department || '—'}</td>
                  <td className="py-2.5">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
