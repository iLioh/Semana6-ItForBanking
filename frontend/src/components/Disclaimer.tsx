export const disclaimer = 'Demostración académica con datos simulados. Los resultados no constituyen decisiones crediticias ni resoluciones reales de una entidad financiera.'

export function Disclaimer() {
  return <aside className="disclaimer" role="note"><span>{disclaimer}</span></aside>
}
