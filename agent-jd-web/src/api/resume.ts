import { request } from '@/api/http'
import type { Resume } from '@/types/domain'

export interface ResumeCreatePayload {
  title: string
  fileId?: string
  rawText?: string
}

export function listResumesApi() {
  return request<Resume[]>({ url: '/api/resumes', method: 'GET' })
}

export function createResumeApi(payload: ResumeCreatePayload) {
  return request<Resume>({ url: '/api/resumes', method: 'POST', data: payload })
}

export function deleteResumeApi(id: string) {
  return request<void>({ url: `/api/resumes/${id}`, method: 'DELETE' })
}
