const TOKEN_KEY = 'agent_jd_token'
const USER_KEY = 'agent_jd_user'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function setStoredUser(user: unknown): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getStoredUser<T>(): T | null {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) as T : null
}
