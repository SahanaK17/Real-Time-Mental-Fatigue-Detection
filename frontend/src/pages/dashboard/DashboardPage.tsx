/**
 * Dashboard Page — Live fatigue monitoring with real-time charts
 * The primary view for employees monitoring their mental state.
 */
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { analyticsApi } from '@/api/client';
import { useFatigueStore } from '@/store/fatigueStore';
import { useAuthStore } from '@/store/authStore';
import { FatigueGauge } from '@/components/dashboard/FatigueGauge';
import { LiveMetricCard } from '@/components/dashboard/LiveMetricCard';
import { FatigueTrendChart } from '@/components/dashboard/FatigueTrendChart';
import { ExplainabilityPanel } from '@/components/dashboard/ExplainabilityPanel';
import { RecommendationCard } from '@/components/dashboard/RecommendationCard';
import { FATIGUE_LEVELS } from '@/types';
import {
  Keyboard, Mouse, AlertTriangle, Timer,
  TrendingUp, TrendingDown, Activity, Zap,
} from 'lucide-react';
import { recommendationsApi } from '@/api/client';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', damping: 20 } },
};

export function DashboardPage() {
  const { user } = useAuthStore();
  const liveData = useFatigueStore((s) => s.liveData);
  const history = useFatigueStore((s) => s.history);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.getSummary,
    refetchInterval: 30_000,
  });

  const { data: daily } = useQuery({
    queryKey: ['analytics-daily'],
    queryFn: analyticsApi.getDaily,
    refetchInterval: 60_000,
  });

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations'],
    queryFn: recommendationsApi.getActive,
    refetchInterval: 60_000,
  });

  const currentScore = liveData?.fatigueScore ?? summary?.current?.fatigue_score ?? 0;
  const currentLevel = liveData?.fatigueLevel ?? summary?.current?.fatigue_level ?? 'alert';
  const levelInfo = FATIGUE_LEVELS[currentLevel] ?? FATIGUE_LEVELS.alert;
  const topFeatures = liveData?.topFeatures ?? summary?.current?.top_features ?? [];

  // Build mini live chart from WS history
  const liveChartData = history.slice(0, 60).reverse().map((d, i) => ({
    t: i,
    score: d.fatigueScore,
  }));

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-7xl mx-auto"
    >
      {/* ── Header ───────────────────────────────────────── */}
      <motion.div variants={itemVariants} className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {getGreeting()}, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Your mental wellness dashboard · Real-time monitoring active
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border`}
            style={{
              backgroundColor: levelInfo.bgColor,
              borderColor: levelInfo.color + '40',
              color: levelInfo.color,
            }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: levelInfo.color }} />
            {levelInfo.label}
          </span>
        </div>
      </motion.div>

      {/* ── Primary Row: Gauge + Stats ───────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Fatigue Gauge */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <div className={`glass-card rounded-2xl p-6 h-full glow-${currentLevel}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                Fatigue Index
              </h2>
              <span className="text-xs text-muted-foreground">
                {liveData ? 'Live' : summary?.current?.predicted_at
                  ? new Date(summary.current.predicted_at).toLocaleTimeString()
                  : '—'}
              </span>
            </div>
            <FatigueGauge score={currentScore} level={currentLevel} />
            <div className="mt-4 text-center">
              <p className="text-xs text-muted-foreground leading-relaxed">
                {levelInfo.description}
              </p>
              {liveData?.confidence !== undefined && (
                <p className="text-xs text-muted-foreground mt-1">
                  Confidence: {(liveData.confidence * 100).toFixed(0)}%
                </p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Metric Cards Grid */}
        <motion.div variants={itemVariants} className="lg:col-span-2 grid grid-cols-2 gap-4">
          <LiveMetricCard
            title="Today's Avg Fatigue"
            value={summaryLoading ? '—' : `${((summary?.today?.avg_fatigue_score ?? 0) * 100).toFixed(0)}%`}
            subtitle="vs yesterday"
            icon={Activity}
            color="cyan"
          />
          <LiveMetricCard
            title="Peak Fatigue Today"
            value={summaryLoading ? '—' : `${((summary?.today?.max_fatigue_score ?? 0) * 100).toFixed(0)}%`}
            subtitle="max recorded"
            icon={AlertTriangle}
            color={summary?.today?.max_fatigue_score > 0.7 ? 'red' : 'amber'}
          />
          <LiveMetricCard
            title="Weekly Avg Fatigue"
            value={summaryLoading ? '—' : `${((summary?.week?.avg_fatigue_score ?? 0) * 100).toFixed(0)}%`}
            subtitle="last 7 days"
            icon={TrendingUp}
            color="violet"
          />
          <LiveMetricCard
            title="Predictions Today"
            value={summaryLoading ? '—' : String(summary?.today?.prediction_count ?? 0)}
            subtitle="data points"
            icon={Zap}
            color="emerald"
          />
        </motion.div>
      </div>

      {/* ── Live Score Chart + Explainability ────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Today's Hourly Trend */}
        <motion.div variants={itemVariants}>
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Today's Fatigue Trend</h2>
              <span className="text-xs text-muted-foreground">Hourly average</span>
            </div>
            <FatigueTrendChart data={daily?.hourly ?? []} type="hourly" />
          </div>
        </motion.div>

        {/* AI Explainability Panel */}
        <motion.div variants={itemVariants}>
          <div className="glass-card rounded-2xl p-6 h-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Why This Score?</h2>
              <span className="text-xs bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 rounded-full">
                AI Insights
              </span>
            </div>
            <ExplainabilityPanel
              topFeatures={topFeatures}
              explanation={summary?.current?.explanation}
            />
          </div>
        </motion.div>
      </div>

      {/* ── Recommendations ───────────────────────────────── */}
      {recommendations && recommendations.length > 0 && (
        <motion.div variants={itemVariants}>
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Smart Recommendations</h2>
              <span className="text-xs text-muted-foreground">{recommendations.length} active</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {recommendations.map((rec: any) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
