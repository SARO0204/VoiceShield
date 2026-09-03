export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ClassificationType = 'GENUINE' | 'SYNTHETIC' | 'UNCERTAIN' | 'MODEL_UNAVAILABLE';
export type ModelModeType = 'TRAINED_INFERENCE' | 'PRETRAINED_INFERENCE' | 'DEMO' | 'MODEL_UNAVAILABLE';

export interface ModelInfo {
  name: string;
  version: string;
  mode: ModelModeType;
  parameters?: number;
}

export interface QualityMetrics {
  snr_db: number;
  clipping_ratio: number;
  rms: number;
  silence_ratio: number;
}

export interface ChunkResult {
  chunk_index: number;
  timestamp_sec: number;
  ai_probability: number;
  genuine_probability: number;
  classification: ClassificationType;
  confidence: number;
  latency_ms: number;
}

export interface AnalysisRecord {
  id: string;
  user_id: string;
  call_id?: string;
  caller_label: string;
  timestamp: string;
  audio_duration_sec: number;
  audio_filename?: string;
  model: ModelInfo;
  prediction: {
    classification: ClassificationType;
    ai_probability: number;
    genuine_probability: number;
    confidence: number;
  };
  risk: {
    score: number;
    level: RiskLevel;
    action_code: string;
    recommended_action: string;
    breakdown?: Record<string, number>;
  };
  scam_context: {
    score: number;
    transcript?: string;
    financial_request: boolean;
    urgency: boolean;
    credential_request: boolean;
    secrecy_coercion?: boolean;
    impersonation?: boolean;
    matched_excerpts?: string[];
  };
  explanation: string[];
  evidence_tags?: string[];
  disclaimer: string;
  verification_status: string;
  chunks?: ChunkResult[];
  performance?: {
    total_processing_ms: number;
    avg_inference_latency_ms: number;
  };
}

export interface CallRecord {
  id: string;
  user_id: string;
  caller_label: string;
  started_at: string;
  ended_at?: string;
  duration_sec: number;
  overall_risk: number;
  risk_level: RiskLevel;
  overall_classification: ClassificationType;
  analysis_count: number;
  status: 'ACTIVE' | 'COMPLETED' | 'BLOCKED' | 'FLAGGED';
  transcript?: string;
  verification_status: string;
}

export interface AlertRecord {
  id: string;
  user_id: string;
  call_id?: string;
  analysis_id?: string;
  severity: RiskLevel | 'INFO';
  title: string;
  message: string;
  ai_probability: number;
  risk_score: number;
  reasons: string[];
  created_at: string;
  resolved: boolean;
  resolution?: string;
  resolved_at?: string;
}

export interface DashboardSummary {
  protection_status: string;
  total_calls_analyzed: number;
  ai_voice_detected: number;
  high_risk_calls: number;
  critical_alerts: number;
  average_risk_score: number;
  empty_state: boolean;
  model_health: {
    model_name: string;
    version: string;
    mode: ModelModeType;
    accuracy: number;
    f1_score: number;
    eer: number;
    device: string;
  };
  risk_distribution: {
    name: string;
    level: RiskLevel;
    count: number;
    color: string;
  }[];
  recent_calls: CallRecord[];
  recent_alerts: AlertRecord[];
}

export interface SystemStatus {
  backend: string;
  version: string;
  mongodb: string;
  ml_model: string;
  model_mode: ModelModeType;
  active_model_name: string;
  active_model_version: string;
  gpu: {
    available: boolean;
    device: string;
    name: string;
    cuda_version?: string;
  };
  websocket: string;
  stt: string;
  storage: {
    status: string;
    free_space_gb: number;
  };
}

export interface TrainingState {
  status: 'NOT_STARTED' | 'PREPARING_DATA' | 'TRAINING' | 'VALIDATING' | 'EVALUATING' | 'COMPLETED' | 'FAILED' | 'NO_DATASET';
  current_epoch: number;
  total_epochs: number;
  progress_percent: number;
  train_loss: number;
  val_loss: number;
  val_f1: number;
  val_eer: number;
  best_f1: number;
  best_eer: number;
  message: string;
  dataset_status: string;
  gpu_status: string;
  logs: string[];
  history: Array<{
    epoch: number;
    train_loss: number;
    train_acc: number;
    val_loss: number;
    val_accuracy: number;
    val_f1: number;
    val_eer: number;
  }>;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}
