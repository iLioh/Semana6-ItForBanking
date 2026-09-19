import { getAccessToken } from './auth'
import type { Assessment, Category, Metrics, PaginatedAssessments, Prediction } from './types'

const defaultApiUrl = import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin
export const API_URL = import.meta.env.VITE_API_URL || defaultApiUrl

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken()
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Error HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  companies: () => request<{ id: string; name: string; sector: string }[]>('/api/v1/case1/companies'),
  runCase1: (companyId: string) => request<{ batch_id: string; processed: number }>('/api/v1/case1/run', { method: 'POST', body: JSON.stringify({ company_id: companyId }) }),
  assessments: (risk = '') => request<PaginatedAssessments>(`/api/v1/case1/results?page=1&page_size=100${risk ? `&risk_level=${risk}` : ''}`),
  assessment: (id: string) => request<Assessment>(`/api/v1/case1/results/${id}`),
  reviewAssessment: (id: string, humanDecision: string, comment: string) => request<Assessment>(`/api/v1/case1/results/${id}/human-review`, { method: 'PATCH', body: JSON.stringify({ human_decision: humanDecision, comment }) }),
  preparedCases: () => request<{ id: string; text: string; difficulty: string }[]>('/api/v1/case2/cases'),
  classify: (caseId: string, promptVersion: string) => request<Prediction>('/api/v1/case2/classify', { method: 'POST', body: JSON.stringify({ case_id: caseId, prompt_version: promptVersion }) }),
  evaluate: () => request<Metrics>('/api/v1/case2/evaluate', { method: 'POST', body: JSON.stringify({ prompt_versions: ['classification_v1', 'classification_v2'] }) }),
  metrics: () => request<Metrics>('/api/v1/case2/metrics'),
  reviewPrediction: (id: string, decision: string, comment: string, correction: Category | null) => request<Prediction>(`/api/v1/case2/predictions/${id}/human-review`, { method: 'PATCH', body: JSON.stringify({ decision, comment, human_category_correction: correction }) }),
}
