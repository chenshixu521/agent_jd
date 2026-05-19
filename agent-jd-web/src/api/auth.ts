import { request } from '@/api/http'
import type { AuthResult, UserInfo } from '@/types/domain'

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  email?: string
  phone?: string
}

export function loginApi(payload: LoginPayload) {
  return request<AuthResult>({ url: '/api/auth/login', method: 'POST', data: payload })
}

export function registerApi(payload: RegisterPayload) {
  return request<AuthResult>({ url: '/api/auth/register', method: 'POST', data: payload })
}

export function meApi() {
  return request<UserInfo>({ url: '/api/auth/me', method: 'GET' })
}
