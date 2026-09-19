import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api'
import { HumanReview } from '../components/HumanReview'
import type { Category, Metrics, Prediction } from '../types'

const labels: Category[] = ['FRAUDE', 'SERVICIO', 'PRODUCTO']

export function Case2() {
  const [cases, setCases] = useState<{ id: string; text: string; difficulty: string }[]>([])
  const [caseId, setCaseId] = useState('')
  const [version, setVersion] = useState('classification_v2')
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    void api.preparedCases().then((rows) => { setCases(rows); setCaseId(rows[0]?.id ?? '') }).catch((reason) => setError(String(reason)))
    void api.metrics().then(setMetrics).catch(() => {})
  }, [])

  async function classify(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError('')
    try { setPrediction(await api.classify(caseId, version)) }
    catch (reason) { setError(String(reason)) }
    finally { setLoading(false) }
  }

  async function evaluate() {
    setLoading(true); setError('')
    try { setMetrics(await api.evaluate()) }
    catch (reason) { setError(String(reason)) }
    finally { setLoading(false) }
  }

  async function review(decision: string, comment: string, correction: Category | null) {
    if (prediction) setPrediction(await api.reviewPrediction(prediction.id, decision, comment, correction))
  }

  const realEvaluations = metrics?.evaluations.filter((item) => item.provider === 'azure') ?? []

  return <main>
    <header className="page-heading"><p className="eyebrow">CASO 2</p><h1>Clasificación de Quejas Bancarias</h1>
      <p>30 quejas simuladas. Compara dos prompts con el mismo golden humano y revisa la respuesta propuesta.</p></header>
    <section className="split">
      <form className="card" onSubmit={classify}><h2>1 · Clasificar una queja</h2>
        <label>Caso<select value={caseId} onChange={(event) => setCaseId(event.target.value)}>{cases.map((item) => <option key={item.id} value={item.id}>{item.id} · {item.difficulty}</option>)}</select></label>
        <p>{cases.find((item) => item.id === caseId)?.text}</p>
        <label>Prompt<select value={version} onChange={(event) => setVersion(event.target.value)}><option value="classification_v1">V1 · baseline</option><option value="classification_v2">V2 · reglas mejoradas</option></select></label>
        <button disabled={loading || !caseId}>{loading ? 'Procesando…' : 'Clasificar y redactar borrador'}</button>
        <p className="meta">La etiqueta golden no se envía a la IA ni aparece antes de clasificar.</p>
      </form>
      <article className="card result"><h2>2 · Resultado IA</h2>
        {!prediction ? <p className="state">Selecciona una queja para ver la predicción.</p> : <>
          <p><strong>{prediction.category}</strong> · confianza {prediction.confidence} · prioridad {prediction.priority}</p>
          <p>{prediction.summary}</p><p>{prediction.rationale}</p>
          <p>Categoría secundaria: {prediction.secondary_category} · ambigüedad: {prediction.ambiguity_detected ? 'sí' : 'no'}</p>
          <h3>3 · Borrador de respuesta</h3><blockquote>{prediction.draft_response}</blockquote>
          <p>Revisión humana: {prediction.requires_human_review ? 'obligatoria' : 'disponible'}</p>
          <HumanReview kind="case2" resourceId={prediction.id} reviewStatus={prediction.review_status} initialDecision={prediction.analyst_decision} initialCorrection={prediction.human_category_correction} onSubmit={review} />
          <p className="meta">{prediction.prompt_version} · {prediction.response_prompt_version} · {prediction.model}</p>
        </>}
      </article>
    </section>
    {error && <p className="error">{error}</p>}
    <section className="card"><div className="section-title"><div><h2>4 · Comparación V1 vs V2</h2><p>Ambos prompts se evalúan sobre las mismas 30 quejas y el golden humano 10/10/10.</p></div>
      <button disabled={loading || !cases.length} onClick={() => void evaluate()}>Ejecutar evaluación</button></div>
      {!realEvaluations.length && <p className="state">PENDIENTE DE EVALUACIÓN real con Azure OpenAI. Los mocks locales no producen métricas publicables.</p>}
      {realEvaluations.map((evaluation) => <article className="metrics" key={evaluation.prompt_version}>
        <div className="metric-head"><h3>{evaluation.prompt_version}</h3><strong>Accuracy {(evaluation.accuracy * 100).toFixed(1)}%</strong></div>
        <p>Macro: Precision {evaluation.precision_macro.toFixed(2)} · Recall {evaluation.recall_macro.toFixed(2)} · F1 {evaluation.f1_macro.toFixed(2)}</p>
        <div className="metric-grid">{labels.map((label) => <div key={label}><span>{label}</span><b>F1 {evaluation.per_class[label].f1.toFixed(2)}</b><small>P {evaluation.per_class[label].precision.toFixed(2)} · R {evaluation.per_class[label].recall.toFixed(2)}</small></div>)}</div>
        <h4>Matriz de confusión</h4><table className="matrix"><thead><tr><th>Golden ↓ / IA →</th>{labels.map((label) => <th key={label}>{label}</th>)}</tr></thead>
          <tbody>{labels.map((expected) => <tr key={expected}><th>{expected}</th>{labels.map((actual) => <td key={actual}>{evaluation.confusion_matrix[expected][actual]}</td>)}</tr>)}</tbody></table>
        <details><summary>Errores por caso ({evaluation.errors.length})</summary>{!evaluation.errors.length ? <p>Sin errores registrados.</p> :
          <div className="table-wrap"><table><thead><tr><th>Caso</th><th>Texto</th><th>Dificultad</th><th>Golden</th><th>Predicha</th><th>Confianza</th><th>Razón</th><th>Secundaria</th><th>Ambigüedad</th></tr></thead>
            <tbody>{evaluation.errors.map((item) => <tr key={item.case_id}><td>{item.case_id}</td><td>{item.text}</td><td>{item.difficulty}</td><td>{item.category_golden}</td><td>{item.category_predicted}</td><td>{item.confidence}</td><td>{item.rationale}</td><td>{item.secondary_category}</td><td>{item.ambiguity_detected ? 'Sí' : 'No'}</td></tr>)}</tbody></table></div>}</details>
      </article>)}
    </section>
  </main>
}
