import type { AccountInfo, PublicClientApplication } from '@azure/msal-browser'

type PublicConfig = {
  authRequired: boolean
  entraClientId: string
  entraAuthority: string
  entraScope: string
  apiAudience: string
}

let msal: PublicClientApplication | null = null
let config: PublicConfig | null = null
let account: AccountInfo | null = null

export async function initializeAuth(apiUrl: string): Promise<PublicConfig> {
  const response = await fetch(`${apiUrl}/api/v1/public-config`)
  if (!response.ok) throw new Error('No se pudo cargar la configuracion publica')
  config = (await response.json()) as PublicConfig
  if (!config.authRequired) return config
  const { PublicClientApplication } = await import('@azure/msal-browser')
  msal = new PublicClientApplication({
    auth: {
      clientId: config.entraClientId,
      authority: config.entraAuthority,
      redirectUri: window.location.origin,
    },
    cache: { cacheLocation: 'sessionStorage' },
  })
  await msal.initialize()
  await msal.handleRedirectPromise()
  account = msal.getAllAccounts()[0] ?? null
  return config
}

export async function signIn(): Promise<void> {
  if (!msal || !config) return
  const result = await msal.loginPopup({ scopes: [config.entraScope] })
  account = result.account
}

export async function getAccessToken(): Promise<string | null> {
  if (!config?.authRequired) return null
  if (!msal || !account) throw new Error('Debe iniciar sesion con Microsoft Entra ID')
  const result = await msal.acquireTokenSilent({ account, scopes: [config.entraScope] })
  return result.accessToken
}

export function authIsRequired(): boolean {
  return config?.authRequired ?? false
}

export function isSignedIn(): boolean {
  return Boolean(account)
}
