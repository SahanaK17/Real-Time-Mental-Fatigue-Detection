// ============================================================
// TypeScript Types — Mental Fatigue Detector
// ============================================================

// ── Auth ─────────────────────────────────────────────────
export type UserRole = 'admin' | 'employee' | 'researcher';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  department?: string;
  job_title?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
  fatigue_threshold?: number;
  notification_preferences?: NotificationPreferences;
}

export interface NotificationPreferences {
  browser: boolean;
  email: boolean;
  fatigue_threshold: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// ── Sessions ─────────────────────────────────────────────
export type SessionStatus = 'active' | 'completed' | 'interrupted';

export interface TrackerSession {
  id: string;
  user_id: string;
  status: SessionStatus;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  hostname?: string;
  os_platform?: string;
  tracker_version?: string;
  total_keystrokes?: number;
  total_mouse_distance?: number;
  avg_fatigue_score?: number;
  max_fatigue_score?: number;
}

// ── Fatigue ───────────────────────────────────────────────
export type FatigueLevel = 'alert' | 'mild' | 'moderate' | 'high' | 'critical';

export interface FatiguePrediction {
  id: string;
  fatigue_score: number;        // 0-1
  fatigue_level: FatigueLevel;
  confidence: number;
  model_name: string;
  top_features: FeatureImpact[];
  shap_values?: Record<string, number>;
  explanation_text?: string;
  predicted_at: string;
}

export interface FeatureImpact {
  feature: string;
  shap_value: number;
  feature_value: number;
  impact: 'increases' | 'decreases';
}

// ── Analytics ─────────────────────────────────────────────
export interface DashboardSummary {
  today: {
    avg_fatigue_score: number;
    max_fatigue_score: number;
    prediction_count: number;
  };
  week: {
    avg_fatigue_score: number;
  };
  current: {
    fatigue_score?: number;
    fatigue_level?: FatigueLevel;
    confidence?: number;
    predicted_at?: string;
    top_features?: FeatureImpact[];
    explanation?: string;
  };
}

export interface HourlyDataPoint {
  hour: number;
  avg_fatigue_score: number;
  count: number;
}

export interface DailyDataPoint {
  date: string;
  avg_fatigue_score: number;
  max_fatigue_score: number;
  prediction_count: number;
}

export interface HeatmapDataPoint {
  hour: number;
  day_of_week: number;
  avg_fatigue_score: number;
}

// ── Recommendations ───────────────────────────────────────
export interface Recommendation {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  priority: number;
  duration_minutes?: number;
  created_at: string;
}

// ── Notifications ─────────────────────────────────────────
export type NotificationType = 'fatigue_alert' | 'high_risk' | 'break_reminder' | 'daily_summary' | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  is_read: boolean;
  data?: Record<string, unknown>;
  created_at: string;
}

// ── Admin ─────────────────────────────────────────────────
export interface AdminUser extends User {
  avg_fatigue_score?: number;
  max_fatigue_score?: number;
  prediction_count?: number;
}

export interface AdminStats {
  total_users: number;
  active_sessions: number;
  predictions_last_24h: number;
  avg_fatigue_score_last_24h: number;
}

// ── WebSocket ─────────────────────────────────────────────
export interface WsMessage {
  type: 'fatigue_update' | 'notification' | 'system';
  fatigue_score?: number;
  fatigue_level?: FatigueLevel;
  confidence?: number;
  top_features?: FeatureImpact[];
  timestamp?: string;
}

// ── API ───────────────────────────────────────────────────
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
  request_id?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

// ── Fatigue Utilities ─────────────────────────────────────
export const FATIGUE_LEVELS: Record<FatigueLevel, {
  label: string;
  color: string;
  bgColor: string;
  description: string;
  emoji: string;
}> = {
  alert: {
    label: 'Alert',
    color: '#10b981',
    bgColor: 'rgba(16, 185, 129, 0.15)',
    description: 'Fully focused and productive',
    emoji: '✅',
  },
  mild: {
    label: 'Mild Fatigue',
    color: '#06b6d4',
    bgColor: 'rgba(6, 182, 212, 0.15)',
    description: 'Slight decrease in efficiency',
    emoji: '🟡',
  },
  moderate: {
    label: 'Moderate Fatigue',
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.15)',
    description: 'Noticeable performance decline',
    emoji: '🟠',
  },
  high: {
    label: 'High Fatigue',
    color: '#f97316',
    bgColor: 'rgba(249, 115, 22, 0.15)',
    description: 'Significant impairment detected',
    emoji: '🔴',
  },
  critical: {
    label: 'Critical Fatigue',
    color: '#ef4444',
    bgColor: 'rgba(239, 68, 68, 0.15)',
    description: 'Immediate break required',
    emoji: '🚨',
  },
};
