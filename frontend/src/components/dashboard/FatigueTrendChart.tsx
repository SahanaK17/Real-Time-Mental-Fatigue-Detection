/**
 * Fatigue Trend Chart — Recharts area chart for fatigue over time
 */
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';

interface HourlyPoint { hour: number; avg_fatigue_score: number; count: number; }
interface DailyPoint { date: string; avg_fatigue_score: number; max_fatigue_score: number; }

interface FatigueTrendChartProps {
  data: HourlyPoint[] | DailyPoint[];
  type: 'hourly' | 'daily';
  height?: number;
}

const CustomTooltip = ({ active, payload, label, type }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card border border-white/10 rounded-xl px-3 py-2 shadow-xl text-xs">
      <p className="text-muted-foreground mb-1">
        {type === 'hourly' ? `${label}:00` : label}
      </p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name === 'avg_fatigue_score' ? 'Avg' : 'Max'}: {(p.value * 100).toFixed(0)}%
        </p>
      ))}
    </div>
  );
};

export function FatigueTrendChart({ data, type, height = 200 }: FatigueTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        No data available yet
      </div>
    );
  }

  const xKey = type === 'hourly' ? 'hour' : 'date';
  const xFormatter = (val: any) =>
    type === 'hourly' ? `${val}:00` : new Date(val).toLocaleDateString('en', { weekday: 'short' });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="fatigueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="maxGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />

        <XAxis
          dataKey={xKey}
          tickFormatter={xFormatter}
          tick={{ fontSize: 10, fill: '#6b7280' }}
          axisLine={false}
          tickLine={false}
        />

        <YAxis
          domain={[0, 1]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tick={{ fontSize: 10, fill: '#6b7280' }}
          axisLine={false}
          tickLine={false}
        />

        <Tooltip content={<CustomTooltip type={type} />} />

        {/* Alert threshold line */}
        <ReferenceLine
          y={0.7}
          stroke="rgba(249,115,22,0.4)"
          strokeDasharray="3 3"
          label={{ value: 'Alert', position: 'right', fontSize: 9, fill: '#f97316' }}
        />

        <Area
          type="monotone"
          dataKey="avg_fatigue_score"
          stroke="#06b6d4"
          strokeWidth={2}
          fill="url(#fatigueGrad)"
          dot={false}
          activeDot={{ r: 4, fill: '#06b6d4', strokeWidth: 0 }}
        />

        {type === 'daily' && (
          <Area
            type="monotone"
            dataKey="max_fatigue_score"
            stroke="#f97316"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            fill="url(#maxGrad)"
            dot={false}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
