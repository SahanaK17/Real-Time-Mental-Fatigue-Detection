/**
 * Fatigue Heatmap — Hour of day × Day of week fatigue intensity
 */
interface HeatmapPoint { hour: number; day_of_week: number; avg_fatigue_score: number; }

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function scoreToColor(score: number): string {
  if (score < 0.25) return 'rgba(16,185,129,0.7)';
  if (score < 0.50) return 'rgba(6,182,212,0.7)';
  if (score < 0.70) return 'rgba(245,158,11,0.7)';
  if (score < 0.85) return 'rgba(249,115,22,0.7)';
  return 'rgba(239,68,68,0.7)';
}

export function FatigueHeatmap({ data }: { data: HeatmapPoint[] }) {
  const dataMap = new Map<string, number>();
  data.forEach((d) => dataMap.set(`${d.day_of_week}-${d.hour}`, d.avg_fatigue_score));

  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
        No heatmap data yet — needs at least 7 days of monitoring
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px]">
        {/* Hour labels */}
        <div className="flex mb-1 ml-10">
          {HOURS.filter(h => h % 3 === 0).map(h => (
            <div key={h} className="flex-1 text-center text-[10px] text-muted-foreground">{h}:00</div>
          ))}
        </div>

        {DAYS.map((day, dayIdx) => (
          <div key={day} className="flex items-center gap-1 mb-1">
            <span className="w-8 text-[11px] text-muted-foreground text-right pr-1 flex-shrink-0">{day}</span>
            <div className="flex gap-0.5 flex-1">
              {HOURS.map((hour) => {
                const score = dataMap.get(`${dayIdx}-${hour}`) ?? -1;
                return (
                  <div
                    key={hour}
                    className="flex-1 h-5 rounded-sm transition-opacity hover:opacity-80 cursor-default"
                    style={{
                      backgroundColor: score >= 0 ? scoreToColor(score) : 'rgba(255,255,255,0.04)',
                    }}
                    title={score >= 0 ? `${day} ${hour}:00 — ${(score * 100).toFixed(0)}% fatigue` : 'No data'}
                  />
                );
              })}
            </div>
          </div>
        ))}

        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 ml-10">
          <span className="text-[10px] text-muted-foreground">Low</span>
          {['rgba(16,185,129,0.7)', 'rgba(6,182,212,0.7)', 'rgba(245,158,11,0.7)', 'rgba(249,115,22,0.7)', 'rgba(239,68,68,0.7)'].map((color, i) => (
            <div key={i} className="w-6 h-3 rounded-sm" style={{ backgroundColor: color }} />
          ))}
          <span className="text-[10px] text-muted-foreground">High</span>
        </div>
      </div>
    </div>
  );
}
