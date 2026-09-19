export type Category = 'FRAUDE' | 'SERVICIO' | 'PRODUCTO'
export type Decision = 'APROBAR' | 'EVALUAR' | 'RECHAZAR'

export type Assessment = {
  id: string
  batch_id: string
  company_code: string
  company_name: string
  public_variables: Record<string, unknown>
  synthetic_variables: Record<string, unknown>
  kyc: { status: string; justification: string; detected_risks: string[]; missing_or_pending_information: string[]; confidence: string }
  scoring: { score: number; risk_level: string; recommendation: Decision; payment_capacity_analysis: string; detected_risks: string[]; calculation_breakdown: string[]; requires_human_review: boolean }
  xai: { explanation: string; key_variables: string[]; possible_biases: string[]; limitations: string[]; transparency_assessment: string; confidence: string }
  reference_score: number
  scoring_discrepancy: boolean
  requires_human_review: boolean
  kyc_reference: string
  kyc_discrepancy: boolean
  score: number
  risk_level: 'BAJO' | 'MEDIO' | 'ALTO'
  recommendation: Decision
  prompt_versions: Record<string, string>
  model: string
  executed_at: string
  review_status: 'PENDIENTE' | 'REVISADA'
  human_decision: Decision | null
  analyst_comment: string | null
}

export type PaginatedAssessments = { items: Assessment[]; page: number; page_size: number; total: number }

export type Prediction = {
  id: string
  case_id: string
  category: Category
  confidence: 'BAJA' | 'MEDIA' | 'ALTA'
  priority: 'BAJA' | 'MEDIA' | 'ALTA'
  summary: string
  rationale: string
  secondary_category: Category | 'NINGUNA'
  ambiguity_detected: boolean
  requires_human_review: boolean
  draft_response: string
  prompt_version: string
  response_prompt_version: string
  model: string
  latency_ms: number
  executed_at: string
  review_status: 'PENDIENTE' | 'REVISADA'
  analyst_decision: string | null
  human_category_correction: Category | null
  analyst_comment: string | null
}

export type PromptMetrics = {
  prompt_version: string
  provider: string
  model: string
  dataset: string
  accuracy: number
  precision_macro: number
  recall_macro: number
  f1_macro: number
  per_class: Record<Category, { precision: number; recall: number; f1: number; support: number }>
  confusion_matrix: Record<Category, Record<Category, number>>
  errors: Array<{ case_id: string; text: string; difficulty: string; category_golden: Category; category_predicted: Category; prompt_version: string; confidence: string; rationale: string; secondary_category: string; ambiguity_detected: boolean }>
}

export type Metrics = { evaluations: PromptMetrics[]; generated_at: string }
