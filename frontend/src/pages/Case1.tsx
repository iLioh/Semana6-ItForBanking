import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { HumanReview } from '../components/HumanReview'
import type { Assessment } from '../types'

export function Case1() {
  const [companies, setCompanies] = useState<{ id: string; name: string; sector: string }[]>([])
  const [companyId, setCompanyId] = useState('')
  const [items, setItems] = useState<Assessment[]>([])
  const [selected, setSelected] = useState<Assessment | null>(null)
  const [risk, setRisk] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => { setItems((await api.assessments(risk)).items) }, [risk])
  useEffect(() => {
    void api.companies().then((rows) => { setCompanies(rows); setCompanyId(rows[0]?.id ?? '') }).catch((reason) => setError(String(reason)))
  }, [])
  useEffect(() => { void load().catch((reason) => setError(String(reason))) }, [load])

  async function execute() {
    setLoading(true); setError('')
    try {
      await api.runCase1(companyId)
      await load()
    } catch (reason) { setError(String(reason)) }
    finally { setLoading(false) }
  }

  async function review(decision: string, comment: string) {
    if (!selected) return
    const updated = await api.reviewAssessment(selected.id, decision, comment)
    setSelected(updated)
    await load()
  }

  return <main>
    <header className="page-heading"><p className="eyebrow">CASO 1</p><h1>Onboarding y Scoring Empresarial</h1>
      <p>Selecciona una de 15 empresas simuladas. La IA ejecuta KYC, calcula el score y explica el resultado; una persona decide al final.</p></header>
    <section className="toolbar card"><div><h2>1 · Seleccionar empresa</h2><p>Datos totalmente simulados del dataset definitivo.</p></div>
      <div className="actions"><label>Empresa<select value={companyId} onChange={(event) => setCompanyId(event.target.value)}>
        {companies.map((company) => <option key={company.id} value={company.id}>{company.name} · {company.id}</option>)}
      </select></label><button disabled={loading || !companyId} onClick={() => void execute()}>{loading ? 'Ejecutando tres prompts…' : 'Ejecutar flujo'}</button></div>
    </section>
    {error && <p className="error">{error}</p>}
    <section className="card"><div className="section-title"><div><h2>Resultados guardados</h2><p>Selecciona un resultado para ver sus cuatro fases.</p></div>
      <label>Riesgo<select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="">Todos</option><option>BAJO</option><option>MEDIO</option><option>ALTO</option></select></label></div>
      {!items.length && <p className="state">Aún no hay resultados. Ejecuta una empresa.</p>}
      {!!items.length && <div className="table-wrap"><table><thead><tr><th>Empresa</th><th>KYC</th><th>Score IA</th><th>Riesgo</th><th>Recomendación</th><th>Revisión</th></tr></thead>
        <tbody>{items.map((item) => <tr key={item.id} onClick={() => setSelected(item)}><td>{item.company_name}</td><td>{item.kyc.status}</td><td>{item.score}</td><td>{item.risk_level}</td><td>{item.recommendation}</td><td>{item.review_status}</td></tr>)}</tbody></table></div>}
    </section>
    {selected && <section className="detail card"><button className="close" onClick={() => setSelected(null)}>Cerrar</button>
      <p className="eyebrow">{selected.company_code} · {selected.company_name}</p><h2>Flujo completo</h2>
      <div className="detail-grid">
        <article><h3>Fase 1 · KYC / Onboarding</h3><p><strong>{selected.kyc.status}</strong> · confianza {selected.kyc.confidence}</p><p>{selected.kyc.justification}</p><p>Riesgos: {selected.kyc.detected_risks.join(', ') || 'ninguno señalado'}</p><p>Referencia académica: {selected.kyc_reference}{selected.kyc_discrepancy && ' · discrepancia'}</p></article>
        <article><h3>Fase 2 · Scoring IA</h3><p><strong>{selected.score}/100</strong> · {selected.risk_level} · {selected.recommendation}</p><p>{selected.scoring.payment_capacity_analysis}</p><ul>{selected.scoring.calculation_breakdown.map((part) => <li key={part}>{part}</li>)}</ul><p>Referencia académica: {selected.reference_score}/100 · {selected.scoring_discrepancy ? 'discrepancia: revisar' : 'coincide'}</p></article>
        <article><h3>Fase 3 · Explicabilidad</h3><p>{selected.xai.explanation}</p><p>Variables clave: {selected.xai.key_variables.join(', ')}</p><p>Sesgos posibles: {selected.xai.possible_biases.join(', ')}</p><p>Limitaciones: {selected.xai.limitations.join(', ')}</p><p>Transparencia: {selected.xai.transparency_assessment} · confianza {selected.xai.confidence}</p></article>
        <article><h3>Fase 4 · Decisión humana</h3><p>Recomendación IA: <strong>{selected.recommendation}</strong></p><p>Decisión humana: <strong>{selected.human_decision ?? 'Pendiente'}</strong></p><p>Estado: {selected.review_status}</p></article>
      </div>
      <HumanReview kind="case1" resourceId={selected.id} reviewStatus={selected.review_status} initialDecision={selected.human_decision} onSubmit={review} />
      <p className="meta">Prompts: {Object.values(selected.prompt_versions).join(' · ')} · modelo {selected.model}</p>
    </section>}
  </main>
}
