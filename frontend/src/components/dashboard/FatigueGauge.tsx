/**
 * Fatigue Gauge — Animated radial gauge showing 0-100% fatigue score
 */
import { motion } from 'framer-motion';
import type { FatigueLevel } from '@/types';
import { FATIGUE_LEVELS } from '@/types';

interface FatigueGaugeProps {
  score: number;      // 0-1
  level: FatigueLevel;
  size?: number;
}

export function FatigueGauge({ score, level, size = 180 }: FatigueGaugeProps) {
  const levelInfo = FATIGUE_LEVELS[level] ?? FATIGUE_LEVELS.alert;
  const percentage = Math.round(score * 100);

  // SVG arc calculation
  const radius = 70;
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = 10;
  const startAngle = -225;
  const totalAngle = 270;

  const polarToCartesian = (angle: number) => {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  };

  const describeArc = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(startAngle);
    const end = polarToCartesian(endAngle);
    const largeArc = endAngle - startAngle > 180 ? '1' : '0';
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  const bgPath = describeArc(startAngle, startAngle + totalAngle);
  const endAngle = startAngle + (totalAngle * score);
  const activePath = score > 0 ? describeArc(startAngle, endAngle) : '';

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background track */}
          <path
            d={bgPath}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Active arc */}
          {activePath && (
            <motion.path
              d={activePath}
              fill="none"
              stroke={levelInfo.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, ease: 'easeOut' }}
              filter={`drop-shadow(0 0 6px ${levelInfo.color}80)`}
            />
          )}

          {/* Score ticks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = startAngle + (totalAngle * tick) / 100;
            const inner = { ...polarToCartesian(angle) };
            const tickRadius = radius + strokeWidth * 0.8;
            const outer = {
              x: cx + tickRadius * Math.cos(((angle - 90) * Math.PI) / 180),
              y: cy + tickRadius * Math.sin(((angle - 90) * Math.PI) / 180),
            };
            return (
              <line
                key={tick}
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke="rgba(255,255,255,0.15)"
                strokeWidth="1"
              />
            );
          })}
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            key={percentage}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-4xl font-bold tracking-tight"
            style={{ color: levelInfo.color }}
          >
            {percentage}
          </motion.span>
          <span className="text-xs text-muted-foreground font-medium">%</span>
          <span className="text-xs font-medium mt-0.5" style={{ color: levelInfo.color }}>
            {levelInfo.emoji} {levelInfo.label}
          </span>
        </div>
      </div>
    </div>
  );
}
