import { useEffect, useState, type FormEvent } from 'react'
import type { Category } from '../types'

type Props = {
  kind: 'case1' | 'case2'
  resourceId: string
  reviewStatus: string
  initialDecision: string | null
  initialCorrection?: Category | null
  onSubmit: (decision: string, comment: string, correction: Category | null) => Promise<void>
}

export function HumanReview({ kind, resourceId, reviewStatus, initialDecision, initialCorrection, onSubmit }: Props) {
  const [decision, setDecision] = useState(initialDecision ?? (kind === 'case1' ? 'EVALUAR' : 'VALIDAR'))
  const [comment, setComment] = useState('Revision humana completada.')
  const [correction, setCorrection] = useState<Category | ''>(initialCorrection ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setDecision(initialDecision ?? (kind === 'case1' ? 'EVALUAR' : 'VALIDAR'))
    setCorrection(initialCorrection ?? '')
  }, [resourceId, kind, initialDecision, initialCorrection])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true); setError('')
    try { await onSubmit(decision, comment, correction || null) }
    catch (reason) { setError(String(reason)) }
    finally { setSaving(false) }
  }

  return <form className="review-form" onSubmit={submit}>
    <h3>Fase final · decisión humana</h3>
    <p>Estado: {reviewStatus}. La recomendación IA no cambia al guardar.</p>
    <label>Decisión humana
      <select value={decision} onChange={(event) => setDecision(event.target.value)}>
        {kind === 'case1' ? <><option>APROBAR</option><option>EVALUAR</option><option>RECHAZAR</option></>
          : <><option>VALIDAR</option><option>CORREGIR</option><option>RECHAZAR_BORRADOR</option></>}
      </select>
    </label>
    {kind === 'case2' && <label>Corrección de categoría (opcional)
      <select value={correction} onChange={(event) => setCorrection(event.target.value as Category | '')}>
        <option value="">Sin corrección</option><option>FRAUDE</option><option>SERVICIO</option><option>PRODUCTO</option>
      </select>
    </label>}
    <label>Comentario sin datos personales
      <select value={comment} onChange={(event) => setComment(event.target.value)}>
        <option>Revision humana completada.</option>
        <option>Pendiente de validacion adicional.</option>
        <option>Resultado rechazado por revision humana.</option>
      </select>
    </label>
    <button disabled={saving}>{saving ? 'Guardando…' : 'Guardar revisión'}</button>
    {error && <p className="error">{error}</p>}
  </form>
}
