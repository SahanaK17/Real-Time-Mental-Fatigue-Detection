/**
 * Analytics Page — Deep dive charts, heatmap, weekly trends
 */
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { analyticsApi } from '@/api/client';
import { FatigueTrendChart } from '@/components/dashboard/FatigueTrendChart';
import { FatigueHeatmap } from '@/components/analytics/FatigueHeatmap';
import { Calendar, TrendingUp, BarChart3 } from 'lucide-react';

export function AnalyticsPage() {
  const { data: weekly } = useQuery({ queryKey: ['weekly'], queryFn: analyticsApi.getWeekly });
  const { data: heatmap } = useQuery({ queryKey: ['heatmap'], queryFn: () => analyticsApi.getHeatmap(30) });
  const { data: daily } = useQuery({ queryKey: ['daily'], queryFn: analyticsApi.getDaily });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">Detailed fatigue trends and patterns over time</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <h2 className="font-semibold">Today — Hourly Trend</h2>
          </div>
          <FatigueTrendChart data={daily?.hourly ?? []} type="hourly" height={220} />
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-violet-400" />
            <h2 className="font-semibold">This Week — Daily Trend</h2>
          </div>
          <FatigueTrendChart data={weekly?.daily ?? []} type="daily" height={220} />
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-amber-400" />
          <h2 className="font-semibold">30-Day Fatigue Heatmap</h2>
          <span className="text-xs text-muted-foreground ml-auto">Hour of day × Day of week</span>
        </div>
        <FatigueHeatmap data={heatmap?.heatmap ?? []} />
      </div>
    </motion.div>
  );
}
