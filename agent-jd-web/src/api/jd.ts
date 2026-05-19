import { request } from '@/api/http'
import type { Jd } from '@/types/domain'

export interface JdCreatePayload {
  title: string
  company?: string
  city?: string
  rawText: string
  sourceUrl?: string
}

export function listJdsApi() {
  return request<Jd[]>({ url: '/api/jds', method: 'GET' })
}

export function createJdApi(payload: JdCreatePayload) {
  return request<Jd>({ url: '/api/jds', method: 'POST', data: payload })
}
