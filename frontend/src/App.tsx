import { lazy, Suspense, useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { API_URL } from './api'
import { authIsRequired, initializeAuth, isSignedIn, signIn } from './auth'
import { Home } from './pages/Home'

const Case1 = lazy(() => import('./pages/Case1').then((module) => ({ default: module.Case1 })))
const Case2 = lazy(() => import('./pages/Case2').then((module) => ({ default: module.Case2 })))

export default function App() {
  const [ready, setReady] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { initializeAuth(API_URL).then(() => { setAuthenticated(isSignedIn() || !authIsRequired()); setReady(true) }).catch((reason) => { setError(String(reason)); setReady(true) }) }, [])
  async function login() { try { await signIn(); setAuthenticated(true) } catch (reason) { setError(String(reason)) } }
  if (!ready) return <div className="splash">Preparando el laboratorio…</div>
  if (error) return <div className="splash error">{error}</div>
  if (!authenticated) return <div className="splash"><h1>Acceso para analistas</h1><p>Inicia sesión con Microsoft Entra ID.</p><button onClick={() => void login()}>Iniciar sesión</button></div>
  return <BrowserRouter><header className="topbar"><NavLink className="brand" to="/"><span>BA</span><div>Banco Andino<small>Laboratorio de IA</small></div></NavLink><nav><NavLink to="/">Inicio</NavLink><NavLink to="/caso-1">Caso 1 · Empresas</NavLink><NavLink to="/caso-2">Caso 2 · Quejas</NavLink></nav><span className="secure">Acceso restringido para demostración</span></header><Suspense fallback={<p className="state">Cargando vista…</p>}><Routes><Route path="/" element={<Home />} /><Route path="/caso-1" element={<Case1 />} /><Route path="/caso-2" element={<Case2 />} /></Routes></Suspense><footer>IBLaboratorio06 · Datos simulados · Decisión humana obligatoria</footer></BrowserRouter>
}
