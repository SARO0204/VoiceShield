import type {
  AnalysisRecord,
  CallRecord,
  AlertRecord,
  DashboardSummary,
  SystemStatus,
  TrainingState,
  UserProfile,
} from '../types';

const API_BASE = '/api';

function getAuthHeader(): HeadersInit {
  const token = localStorage.getItem('voiceshield_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  async register(name: string, email: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  async getMe(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
  },

  // Dashboard
  async getDashboard(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch dashboard');
    return res.json();
  },

  // Audio Analysis
  async analyzeAudio(
    audioBlobOrFile: Blob | File,
    filename: string,
    transcript?: string,
    callerLabel?: string,
    hints?: { financial?: boolean; urgency?: boolean; otp?: boolean }
  ): Promise<AnalysisRecord> {
    const formData = new FormData();
    formData.append('file', audioBlobOrFile, filename);
    if (transcript) formData.append('transcript', transcript);
    if (callerLabel) formData.append('caller_label', callerLabel);
    if (hints?.financial) formData.append('financial_hint', 'true');
    if (hints?.urgency) formData.append('urgency_hint', 'true');
    if (hints?.otp) formData.append('otp_hint', 'true');

    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Audio analysis failed');
    }
    return res.json();
  },

  // Analyses History
  async getAnalyses(limit = 50, offset = 0, riskLevel?: string, classification?: string): Promise<{ total: number; items: AnalysisRecord[] }> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (riskLevel) params.append('risk_level', riskLevel);
    if (classification) params.append('classification', classification);

    const res = await fetch(`${API_BASE}/analyses?${params.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch analyses');
    return res.json();
  },

  async getAnalysisById(id: string): Promise<AnalysisRecord> {
    const res = await fetch(`${API_BASE}/analyses/${id}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Analysis record not found');
    return res.json();
  },

  // Calls
  async getCalls(limit = 50, offset = 0, status?: string): Promise<{ total: number; items: CallRecord[] }> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.append('status', status);

    const res = await fetch(`${API_BASE}/calls?${params.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch calls');
    return res.json();
  },

  async getCallDetail(callId: string): Promise<{ call: CallRecord; analyses: AnalysisRecord[]; timeline_events: any[] }> {
    const res = await fetch(`${API_BASE}/calls/${callId}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Call detail not found');
    return res.json();
  },

  // Alerts
  async getAlerts(severity?: string, resolved?: boolean): Promise<{ total: number; items: AlertRecord[] }> {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (resolved !== undefined) params.append('resolved', String(resolved));

    const res = await fetch(`${API_BASE}/alerts?${params.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async resolveAlert(alertId: string, resolution: string, notes?: string): Promise<AlertRecord> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
      method: 'PATCH',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution, notes }),
    });
    if (!res.ok) throw new Error('Failed to resolve alert');
    return res.json();
  },

  // Verification
  async createVerification(callId?: string, callerName?: string, secretQuestion?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/verification`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ call_id: callId, caller_name: callerName, secret_question: secretQuestion }),
    });
    if (!res.ok) throw new Error('Failed to create verification challenge');
    return res.json();
  },

  async submitVerificationAnswer(verificationId: string, answer: string): Promise<any> {
    const res = await fetch(`${API_BASE}/verification/${verificationId}/respond`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer }),
    });
    if (!res.ok) throw new Error('Failed to submit verification answer');
    return res.json();
  },

  // Analytics
  async getAnalytics(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  // System & Model Status
  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE}/system/status`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async getModelMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE}/model/metrics`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch model metrics');
    return res.json();
  },

  // Training API
  async getTrainingStatus(): Promise<TrainingState> {
    const res = await fetch(`${API_BASE}/training/status`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch training status');
    return res.json();
  },

  async startTraining(epochs = 20, batchSize = 16, lr = 0.0001): Promise<any> {
    const res = await fetch(`${API_BASE}/training/start`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ epochs, batch_size: batchSize, learning_rate: lr }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to start training');
    }
    return res.json();
  },

  async getTrainingLogs(): Promise<{ status: string; logs: string[] }> {
    const res = await fetch(`${API_BASE}/training/logs`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch training logs');
    return res.json();
  },

  async downloadReportPdf(analysisId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/analyses/${analysisId}/report`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to download forensic report');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `VoiceShield_Forensic_Report_${analysisId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
