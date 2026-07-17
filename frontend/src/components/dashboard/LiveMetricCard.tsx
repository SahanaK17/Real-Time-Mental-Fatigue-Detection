/**
 * Live Metric Card — Animated stat card with trend indicator
 */
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

const colorMap = {
  cyan: {
    bg: 'rgba(6,182,212,0.1)',
    border: 'rgba(6,182,212,0.2)',
    text: '#06b6d4',
    icon: 'rgba(6,182,212,0.2)',
  },
  violet: {
    bg: 'rgba(139,92,246,0.1)',
    border: 'rgba(139,92,246,0.2)',
    text: '#8b5cf6',
    icon: 'rgba(139,92,246,0.2)',
  },
  emerald: {
    bg: 'rgba(16,185,129,0.1)',
    border: 'rgba(16,185,129,0.2)',
    text: '#10b981',
    icon: 'rgba(16,185,129,0.2)',
  },
  amber: {
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.2)',
    text: '#f59e0b',
    icon: 'rgba(245,158,11,0.2)',
  },
  red: {
    bg: 'rgba(239,68,68,0.1)',
    border: 'rgba(239,68,68,0.2)',
    text: '#ef4444',
    icon: 'rgba(239,68,68,0.2)',
  },
};

interface LiveMetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  color?: keyof typeof colorMap;
  trend?: 'up' | 'down' | 'neutral';
}

export function LiveMetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'cyan',
  trend,
}: LiveMetricCardProps) {
  const colors = colorMap[color];

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: 'spring', damping: 20 }}
      className="glass-card rounded-xl p-4 border"
      style={{ borderColor: colors.border }}
    >
      <div className="flex items-start justify-between mb-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: colors.icon }}
        >
          <Icon className="w-4.5 h-4.5" style={{ color: colors.text }} />
        </div>
      </div>

      <motion.div
        key={value}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold tracking-tight"
      >
        {value}
      </motion.div>

      <div className="mt-1">
        <p className="text-xs font-medium text-muted-foreground">{title}</p>
        {subtitle && (
          <p className="text-[11px] text-muted-foreground/70 mt-0.5">{subtitle}</p>
        )}
      </div>
    </motion.div>
  );
}
