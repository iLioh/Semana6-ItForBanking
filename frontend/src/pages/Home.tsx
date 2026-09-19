import { Link } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'

export function Home() {
  return <main>
    <section className="hero"><p className="eyebrow">IT FOR BANKING · LABORATORIO 06</p>
      <h1>IA bancaria explicable con revisión humana</h1>
      <p className="lead">Dos ejercicios con datos simulados: onboarding y scoring empresarial; clasificación de quejas y comparación de prompts.</p>
      <div className="actions"><Link className="button" to="/caso-1">Iniciar Caso 1</Link><Link className="button secondary" to="/caso-2">Iniciar Caso 2</Link></div>
    </section>
    <Disclaimer />
    <section className="card-grid">
      <article className="card"><span className="number">01</span><h2>Onboarding y Scoring Empresarial</h2><p>Elige una de 15 empresas simuladas. Prompt KYC → Prompt Scoring → Prompt Explainability → decisión humana.</p></article>
      <article className="card"><span className="number">02</span><h2>Quejas bancarias</h2><p>Clasifica 30 quejas simuladas como fraude, servicio o producto. Compara V1/V2 con golden humano y revisa el borrador.</p></article>
      <article className="card"><span className="number">03</span><h2>Control y trazabilidad</h2><p>Las referencias humanas se mantienen fuera del prompt. Cada resultado registra versión, modelo y revisión.</p></article>
    </section>
  </main>
}
