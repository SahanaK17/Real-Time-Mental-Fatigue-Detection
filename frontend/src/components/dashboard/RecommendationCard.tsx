/**
 * Recommendation Card Component
 */
import { motion } from 'framer-motion';
import { CheckCircle2, X, Clock } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationsApi } from '@/api/client';
import type { Recommendation } from '@/types';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation: rec }: RecommendationCardProps) {
  const qc = useQueryClient();

  const dismiss = useMutation({
    mutationFn: () => recommendationsApi.dismiss(rec.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
  });

  const complete = useMutation({
    mutationFn: () => recommendationsApi.complete(rec.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
  });

  const priorityColors: Record<number, { bg: string; border: string; badge: string }> = {
    1: { bg: 'rgba(6,182,212,0.05)', border: 'rgba(6,182,212,0.15)', badge: '#06b6d4' },
    2: { bg: 'rgba(245,158,11,0.05)', border: 'rgba(245,158,11,0.15)', badge: '#f59e0b' },
    3: { bg: 'rgba(239,68,68,0.05)', border: 'rgba(239,68,68,0.15)', badge: '#ef4444' },
  };
  const colors = priorityColors[rec.priority] ?? priorityColors[1];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2 }}
      className="relative rounded-xl p-4 border"
      style={{ backgroundColor: colors.bg, borderColor: colors.border }}
    >
      {/* Dismiss button */}
      <button
        onClick={() => dismiss.mutate()}
        className="absolute top-2 right-2 p-1 rounded-md text-muted-foreground/50 hover:text-muted-foreground hover:bg-white/5 transition-colors"
      >
        <X className="w-3 h-3" />
      </button>

      <div className="flex items-start gap-3 mb-3">
        <span className="text-2xl">{rec.icon}</span>
        <div className="flex-1 min-w-0 pr-4">
          <h3 className="font-semibold text-sm leading-tight">{rec.title}</h3>
          {rec.duration_minutes && (
            <div className="flex items-center gap-1 mt-0.5">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">{rec.duration_minutes} min</span>
            </div>
          )}
        </div>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed mb-3">
        {rec.description}
      </p>

      <button
        onClick={() => complete.mutate()}
        disabled={complete.isPending}
        className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors w-full justify-center"
        style={{ backgroundColor: colors.border, color: colors.badge }}
      >
        <CheckCircle2 className="w-3.5 h-3.5" />
        {complete.isPending ? 'Marking...' : 'Mark Complete'}
      </button>
    </motion.div>
  );
}
