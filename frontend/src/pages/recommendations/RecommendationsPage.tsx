/** Recommendations Page */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { recommendationsApi } from '@/api/client';
import { RecommendationCard } from '@/components/dashboard/RecommendationCard';
import { Lightbulb, CheckCircle2 } from 'lucide-react';

export function RecommendationsPage() {
  const qc = useQueryClient();
  const { data: recs, isLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: recommendationsApi.getActive,
    refetchInterval: 30_000,
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Smart Recommendations</h1>
          <p className="text-muted-foreground text-sm mt-1">
            AI-generated wellness suggestions based on your current fatigue state
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          {recs?.length ?? 0} active
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card rounded-xl p-4 h-40 animate-shimmer" />
          ))}
        </div>
      ) : recs?.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <CheckCircle2 className="w-16 h-16 text-emerald-400 mb-4" />
          <h2 className="text-xl font-semibold mb-2">You're doing great!</h2>
          <p className="text-muted-foreground max-w-sm">
            No active recommendations. Your fatigue levels are within the healthy range.
          </p>
        </div>
      ) : (
        <AnimatePresence>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recs.map((rec: any) => (
              <RecommendationCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        </AnimatePresence>
      )}

      {/* Wellness tips section */}
      <div className="glass-card rounded-2xl p-6 mt-8">
        <h2 className="font-semibold mb-4">General Wellness Tips</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { icon: '🍅', title: 'Pomodoro Technique', desc: '25 min focus, 5 min break — maximizes sustained concentration' },
            { icon: '💧', title: 'Stay Hydrated', desc: 'Dehydration significantly impacts cognitive performance' },
            { icon: '👁️', title: '20-20-20 Rule', desc: 'Every 20 min, look 20 feet away for 20 seconds' },
            { icon: '🚶', title: 'Micro-Walks', desc: '5-minute walks every hour improve focus and mood' },
            { icon: '🌬️', title: 'Deep Breathing', desc: 'Box breathing (4-4-4-4) quickly reduces stress hormones' },
            { icon: '🧘', title: 'Desk Stretches', desc: 'Neck rolls and shoulder stretches prevent tension buildup' },
          ].map((tip) => (
            <div key={tip.title} className="flex gap-3 p-3 rounded-xl bg-white/3 border border-white/5">
              <span className="text-xl">{tip.icon}</span>
              <div>
                <h3 className="text-sm font-semibold">{tip.title}</h3>
                <p className="text-xs text-muted-foreground">{tip.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
