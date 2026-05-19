import { request } from '@/api/http'
import type { ChatMessage } from '@/types/domain'

export interface Conversation {
  id: string
  title: string
  scene?: string
  createdAt?: string
  updatedAt?: string
}

export function createConversationApi(payload: {
  title: string
  scene?: string
}) {
  return request<Conversation>({ url: '/api/conversations', method: 'POST', data: payload })
}

export function listConversationsApi() {
  return request<Conversation[]>({ url: '/api/conversations', method: 'GET' })
}

export function addMessageApi(
  conversationId: string,
  payload: ChatMessage & {
    metadata?: Record<string, unknown>
    taskUuid?: string
  }
) {
  return request<ChatMessage>({ url: `/api/conversations/${conversationId}/messages`, method: 'POST', data: payload })
}

export function listMessagesApi(conversationId: string) {
  return request<ChatMessage[]>({ url: `/api/conversations/${conversationId}/messages`, method: 'GET' })
}
