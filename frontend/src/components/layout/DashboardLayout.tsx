/**
 * Dashboard Layout — Sidebar + Header + Content
 */
import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, BarChart2, Lightbulb, Settings,
  ShieldCheck, Bell, LogOut, Menu, X, Brain,
  Wifi, WifiOff, User,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useFatigueStore } from '@/store/fatigueStore';
import type { WsMessage } from '@/types';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/recommendations', icon: Lightbulb, label: 'Recommendations' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const adminNavItems = [
  { to: '/admin', icon: ShieldCheck, label: 'Admin Panel' },
];

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const setFatigueData = useFatigueStore((s) => s.setLiveData);

  const handleWsMessage = (msg: WsMessage) => {
    if (msg.type === 'fatigue_update') {
      setFatigueData({
        fatigueScore: msg.fatigue_score ?? 0,
        fatigueLevel: msg.fatigue_level ?? 'alert',
        confidence: msg.confidence ?? 0,
        topFeatures: msg.top_features ?? [],
        timestamp: msg.timestamp,
      });
    }
  };

  const { isConnected } = useWebSocket({
    userId: user?.id ?? null,
    onMessage: handleWsMessage,
    enabled: !!user,
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-y-0 left-0 z-50 w-64 flex flex-col glass-card border-r border-white/5"
          >
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-sm text-white leading-tight">MindGuard</h1>
                <p className="text-[10px] text-muted-foreground">Fatigue Detection</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              {navItems.map(({ to, icon: Icon, label }) => (
                <NavLink key={to} to={to}>
                  {({ isActive }) => (
                    <motion.div
                      whileHover={{ x: 4 }}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                      }`}
                    >
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      {label}
                      {isActive && (
                        <motion.div
                          layoutId="active-pill"
                          className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400"
                        />
                      )}
                    </motion.div>
                  )}
                </NavLink>
              ))}

              {user?.role === 'admin' && (
                <>
                  <div className="px-3 pt-4 pb-1">
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                      Admin
                    </p>
                  </div>
                  {adminNavItems.map(({ to, icon: Icon, label }) => (
                    <NavLink key={to} to={to}>
                      {({ isActive }) => (
                        <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                          isActive
                            ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                            : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                        }`}>
                          <Icon className="w-4 h-4" />
                          {label}
                        </div>
                      )}
                    </NavLink>
                  ))}
                </>
              )}
            </nav>

            {/* User + Connection Status */}
            <div className="px-3 py-4 border-t border-white/5 space-y-2">
              {/* WS Connection indicator */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
                isConnected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
              }`}>
                {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                {isConnected ? 'Live monitoring' : 'Disconnected'}
                {isConnected && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </div>

              {/* User info */}
              <div className="flex items-center gap-3 px-3 py-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user?.full_name}</p>
                  <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Main Content ──────────────────────────────────── */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
        {/* Top bar */}
        <header className="sticky top-0 z-40 h-14 flex items-center gap-4 px-6 border-b border-white/5 glass-card">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="flex-1" />

          <NotificationsButton />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function NotificationsButton() {
  return (
    <button className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors">
      <Bell className="w-4 h-4" />
      <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400" />
    </button>
  );
}
