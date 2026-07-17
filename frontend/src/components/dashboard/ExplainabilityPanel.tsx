/**
 * Explainability Panel — SHAP feature importance visualization
 */
import { motion } from 'framer-motion';
import type { FeatureImpact } from '@/types';

interface ExplainabilityPanelProps {
  topFeatures: FeatureImpact[];
  explanation?: string;
}

const FEATURE_LABELS: Record<string, string> = {
  typing_speed_wpm: 'Typing Speed',
  key_hold_time_ms: 'Key Hold Duration',
  flight_time_ms: 'Key Flight Time',
  error_rate: 'Error Rate',
  idle_time_keyboard_s: 'Keyboard Idle',
  typing_rhythm_variance: 'Rhythm Variance',
  mouse_speed_px_s: 'Mouse Speed',
  direction_changes: 'Mouse Jitter',
  idle_time_mouse_s: 'Mouse Idle',
  click_frequency: 'Click Rate',
  hover_duration_ms: 'Hover Duration',
  backspace_count: 'Backspace Count',
  scroll_speed: 'Scroll Speed',
};

export function ExplainabilityPanel({ topFeatures, explanation }: ExplainabilityPanelProps) {
  if (!topFeatures || topFeatures.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-center">
        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-3">
          <span className="text-lg">🔍</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Waiting for enough data to generate insights...
        </p>
      </div>
    );
  }

  const maxAbsShap = Math.max(...topFeatures.map((f) => Math.abs(f.shap_value)));

  return (
    <div className="space-y-4">
      {explanation && (
        <p className="text-xs text-muted-foreground leading-relaxed bg-white/3 rounded-lg p-3 border border-white/5">
          {explanation}
        </p>
      )}

      <div className="space-y-2.5">
        {topFeatures.slice(0, 5).map((feature, idx) => {
          const label = FEATURE_LABELS[feature.feature] || feature.feature.replace(/_/g, ' ');
          const barWidth = Math.abs(feature.shap_value) / maxAbsShap;
          const isPositive = feature.impact === 'increases';

          return (
            <motion.div
              key={feature.feature}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.06 }}
              className="space-y-1"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground font-medium">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground/60">
                    val: {feature.feature_value.toFixed(2)}
                  </span>
                  <span
                    className="font-semibold"
                    style={{ color: isPositive ? '#f97316' : '#10b981' }}
                  >
                    {isPositive ? '↑' : '↓'} {isPositive ? 'fatigue' : 'fatigue'}
                  </span>
                </div>
              </div>

              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${barWidth * 100}%` }}
                  transition={{ duration: 0.6, delay: idx * 0.06 }}
                  className="h-full rounded-full"
                  style={{
                    backgroundColor: isPositive ? '#f97316' : '#10b981',
                    opacity: 0.8,
                  }}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      <p className="text-[10px] text-muted-foreground/50 text-center">
        Powered by SHAP values · Tree-based ML explanation
      </p>
    </div>
  );
}
