/**
 * AI Gateway Client Service
 * 
 * TypeScript client for the CareerTrojan AI Gateway.
 * Provides typed access to all AI operations:
 *   - Generate (LLM text generation)
 *   - Score (candidate/resume scoring)
 *   - Classify (category classification)
 *   - Extract (entity extraction)
 *   - Match (job-candidate matching)
 *   - Feedback (ground truth collection)
 * 
 * Usage:
 *   import { aiGateway } from '@/services/aiGateway';
 *   
 *   const response = await aiGateway.generate({ prompt: 'Improve this bullet...' });
 *   const score = await aiGateway.scoreCandidate({ resumeText: '...' });
 */

import { API } from '../lib/apiConfig';

// ══════════════════════════════════════════════════════════════════════════
// Types
// ══════════════════════════════════════════════════════════════════════════

export interface GatewayResponse<T = unknown> {
  requestId: string;
  taskType: string;
  result: T;
  confidence: number;
  calibratedConfidence: number;
  routeTaken: string;
  enginesConsulted: string[];
  groundTruthId: string | null;
  driftFlags: string[];
  warnings: string[];
  success: boolean;
  error: string | null;
  latencyMs: number;
}

export interface GenerateRequest {
  prompt: string;
  provider?: 'openai' | 'anthropic' | 'gemini' | 'ollama';
  maxTokens?: number;
  temperature?: number;
  context?: Record<string, unknown>;
}

export interface ScoreRequest {
  resumeText: string;
  skills?: string[];
  experienceYears?: number;
  education?: string;
  jobDescription?: string;
}

export interface ScoreResult {
  matchScore: number;
  predictedIndustry: string;
  predictedSeniority: string;
  qualityTier: string;
  dimensionScores: Record<string, number>;
  recommendations: string[];
  warnings: string[];
}

export interface ClassifyRequest {
  text: string;
  categoryType?: 'industry' | 'job_level' | 'job_function';
}

export interface ClassifyResult {
  industry?: string;
  jobLevel?: string;
  jobFunction?: string;
  confidence: number;
}

export interface ExtractRequest {
  text: string;
  extractionType?: 'skills' | 'entities' | 'contact' | 'experience';
}

export interface ExtractResult {
  skills?: string[];
  entities?: Array<{ name: string; type: string }>;
  emails?: string[];
  phones?: string[];
  experience?: Array<{ company: string; role: string; duration: string }>;
}

export interface MatchRequest {
  candidate: {
    resumeText?: string;
    skills?: string[];
    experienceYears?: number;
  };
  job: {
    description?: string;
    requiredSkills?: string[];
    minExperience?: number;
  };
}

export interface MatchResult {
  matchScore: number;
  skillGaps: string[];
  recommendations: string[];
}

export interface FeedbackRequest {
  groundTruthId: string;
  outcomeType: 'interview' | 'ats_pass' | 'user_accepted' | 'hired';
  outcomeValue: boolean | number | string;
  metadata?: Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  backends: {
    llmGateway: boolean;
    unifiedAiEngine: boolean;
  };
  metrics: {
    totalRequests: number;
    totalErrors: number;
    errorRate: number;
    avgLatencyMs: number;
  };
  drift: {
    status: string;
    samples?: number;
    currentConfidenceMean?: number;
    currentErrorRate?: number;
    baselineSet?: boolean;
  };
}

// ══════════════════════════════════════════════════════════════════════════
// Utility Functions
// ══════════════════════════════════════════════════════════════════════════

const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
};

// Convert snake_case response to camelCase
const toCamelCase = (obj: unknown): unknown => {
  if (Array.isArray(obj)) {
    return obj.map(toCamelCase);
  }
  if (obj !== null && typeof obj === 'object') {
    return Object.entries(obj as Record<string, unknown>).reduce((acc, [key, value]) => {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      acc[camelKey] = toCamelCase(value);
      return acc;
    }, {} as Record<string, unknown>);
  }
  return obj;
};

// Convert camelCase request to snake_case
const toSnakeCase = (obj: unknown): unknown => {
  if (Array.isArray(obj)) {
    return obj.map(toSnakeCase);
  }
  if (obj !== null && typeof obj === 'object') {
    return Object.entries(obj as Record<string, unknown>).reduce((acc, [key, value]) => {
      const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
      acc[snakeKey] = toSnakeCase(value);
      return acc;
    }, {} as Record<string, unknown>);
  }
  return obj;
};

// ══════════════════════════════════════════════════════════════════════════
// AI Gateway Client
// ══════════════════════════════════════════════════════════════════════════

class AIGatewayClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API.aiGateway || '/api/ai';
  }

  /**
   * Generate text using LLM.
   * 
   * Use cases:
   *   - Resume bullet improvement
   *   - Cover letter generation
   *   - Interview question suggestions
   */
  async generate(request: GenerateRequest): Promise<GatewayResponse<string>> {
    const response = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return toCamelCase(await handleResponse(response)) as GatewayResponse<string>;
  }

  /**
   * Score a candidate/resume using ensemble ML models.
   * 
   * Returns:
   *   - matchScore (0-100)
   *   - predictedIndustry
   *   - predictedSeniority
   *   - qualityTier
   *   - recommendations
   */
  async scoreCandidate(request: ScoreRequest): Promise<GatewayResponse<ScoreResult>> {
    const response = await fetch(`${this.baseUrl}/score`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return toCamelCase(await handleResponse(response)) as GatewayResponse<ScoreResult>;
  }

  /**
   * Classify text into categories.
   * 
   * Category types:
   *   - industry: Tech, Finance, Healthcare, etc.
   *   - job_level: Entry, Mid, Senior, Executive
   *   - job_function: Engineering, Sales, Marketing, etc.
   */
  async classify(request: ClassifyRequest): Promise<GatewayResponse<ClassifyResult>> {
    const response = await fetch(`${this.baseUrl}/classify`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return toCamelCase(await handleResponse(response)) as GatewayResponse<ClassifyResult>;
  }

  /**
   * Extract structured data from text.
   * 
   * Extraction types:
   *   - skills: Technical and soft skills
   *   - entities: Named entities (companies, locations)
   *   - contact: Emails, phones
   *   - experience: Job history
   */
  async extract(request: ExtractRequest): Promise<GatewayResponse<ExtractResult>> {
    const response = await fetch(`${this.baseUrl}/extract`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return toCamelCase(await handleResponse(response)) as GatewayResponse<ExtractResult>;
  }

  /**
   * Match a candidate to job requirements.
   * 
   * Returns:
   *   - matchScore
   *   - skillGaps
   *   - recommendations
   */
  async match(request: MatchRequest): Promise<GatewayResponse<MatchResult>> {
    const response = await fetch(`${this.baseUrl}/match`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return toCamelCase(await handleResponse(response)) as GatewayResponse<MatchResult>;
  }

  /**
   * Record outcome feedback for ground truth loop.
   * 
   * Call this when you learn the actual outcome of a prediction:
   *   - User accepted/rejected suggestion
   *   - Resume passed ATS
   *   - Candidate got interview
   *   - Candidate got hired
   * 
   * This feedback improves model calibration over time.
   */
  async recordFeedback(request: FeedbackRequest): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/feedback`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(toSnakeCase(request)),
    });
    return handleResponse(response);
  }

  /**
   * Get gateway health and metrics.
   * 
   * Returns:
   *   - Backend availability
   *   - Request/error counts
   *   - Average latency
   *   - Drift detection status
   */
  async health(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: getAuthHeaders(),
    });
    return toCamelCase(await handleResponse(response)) as HealthStatus;
  }

  /**
   * Set drift detection baseline.
   * 
   * Call this during healthy operation to capture baseline metrics.
   * Future requests will be compared against this baseline to detect drift.
   */
  async setBaseline(): Promise<{ success: boolean; baseline: Record<string, number> }> {
    const response = await fetch(`${this.baseUrl}/baseline`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  }

  /**
   * Batch score multiple candidates.
   * 
   * More efficient than individual calls for bulk operations.
   */
  async batchScore(candidates: ScoreRequest[]): Promise<{
    total: number;
    successful: number;
    results: Array<{ success: boolean; data?: GatewayResponse<ScoreResult>; error?: string }>;
  }> {
    const response = await fetch(`${this.baseUrl}/batch/score`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(candidates.map(c => toSnakeCase(c))),
    });
    return toCamelCase(await handleResponse(response)) as {
      total: number;
      successful: number;
      results: Array<{ success: boolean; data?: GatewayResponse<ScoreResult>; error?: string }>;
    };
  }

  /**
   * Get current routing configuration.
   */
  async getRoutes(): Promise<{
    defaultRoutes: Record<string, string>;
    costWeights: Record<string, number>;
  }> {
    const response = await fetch(`${this.baseUrl}/routes`, {
      headers: getAuthHeaders(),
    });
    return toCamelCase(await handleResponse(response)) as {
      defaultRoutes: Record<string, string>;
      costWeights: Record<string, number>;
    };
  }

  /**
   * Get drift detection statistics.
   */
  async getDriftStats(): Promise<{
    samples: number;
    currentConfidenceMean: number | null;
    currentErrorRate: number;
    baselineSet: boolean;
  }> {
    const response = await fetch(`${this.baseUrl}/drift/stats`, {
      headers: getAuthHeaders(),
    });
    return toCamelCase(await handleResponse(response)) as {
      samples: number;
      currentConfidenceMean: number | null;
      currentErrorRate: number;
      baselineSet: boolean;
    };
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Export singleton
// ══════════════════════════════════════════════════════════════════════════

export const aiGateway = new AIGatewayClient();
export default aiGateway;
