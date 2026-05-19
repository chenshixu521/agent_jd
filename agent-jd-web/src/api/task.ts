import { request } from '@/api/http'
import type { AiTask } from '@/types/domain'

export interface TaskSubmitPayload {
  capability: string
  action: string
  bizId?: string
  input?: Record<string, unknown>
}

export function submitTaskApi(payload: TaskSubmitPayload) {
  return request<AiTask>({ url: '/api/tasks', method: 'POST', data: payload })
}

export function listTasksApi() {
  return request<AiTask[]>({ url: '/api/tasks', method: 'GET' })
}

export function getTaskApi(taskUuid: string) {
  return request<AiTask>({ url: `/api/tasks/${taskUuid}`, method: 'GET' })
}

export function getTaskResultApi(taskUuid: string) {
  return request<AiTask>({ url: `/api/tasks/${taskUuid}/result`, method: 'GET' })
}
