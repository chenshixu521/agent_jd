import { defineStore } from 'pinia'
import {
  addMessageApi,
  createConversationApi,
  listConversationsApi,
  listMessagesApi,
  type Conversation
} from '@/api/conversation'
import { uploadFileApi } from '@/api/file'
import { createResumeApi } from '@/api/resume'
import { getTaskResultApi, submitTaskApi } from '@/api/task'
import type { AiTask, ChatMessage } from '@/types/domain'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversationId: localStorage.getItem('agent_jd_conversation_id') || '',
    conversations: [] as Conversation[],
    sessionId: localStorage.getItem('agent_jd_session') || '',
    messages: [] as ChatMessage[],
    loading: false
  }),
  actions: {
    async loadHistory() {
      this.conversations = await listConversationsApi()
      if (!this.conversationId) this.conversationId = this.conversations[0]?.id || ''
      if (this.conversationId) {
        localStorage.setItem('agent_jd_conversation_id', this.conversationId)
        this.messages = await listMessagesApi(this.conversationId)
      }
    },
    async selectConversation(id: string) {
      this.conversationId = id
      localStorage.setItem('agent_jd_conversation_id', id)
      this.messages = await listMessagesApi(id)
    },
    async ensureConversation(title: string) {
      if (this.conversationId) return this.conversationId
      const conversation = await createConversationApi({
        title: title.slice(0, 24) || 'Agent 对话',
        scene: 'chat'
      })
      this.conversationId = conversation.id
      this.conversations.unshift(conversation)
      localStorage.setItem('agent_jd_conversation_id', conversation.id)
      return conversation.id
    },
    async newConversation() {
      const conversation = await createConversationApi({
        title: `新对话 ${new Date().toLocaleString()}`,
        scene: 'chat'
      })
      this.conversationId = conversation.id
      this.conversations.unshift(conversation)
      this.messages = []
      this.sessionId = ''
      localStorage.setItem('agent_jd_conversation_id', conversation.id)
      localStorage.removeItem('agent_jd_session')
    },
    async uploadAndAnalyze(file: File) {
      if (!/\.(pdf|docx|txt)$/i.test(file.name)) {
        this.messages.push({
          role: 'assistant',
          content: '当前对话上传先支持 PDF / DOCX / TXT。图片需要 OCR 能力，暂时不能直接识别图片内容。',
          createdAt: new Date().toISOString()
        })
        return
      }
      this.loading = true
      try {
        const conversationId = await this.ensureConversation(`分析文件：${file.name}`)
        const uploaded = await uploadFileApi(file)
        const resume = await createResumeApi({ title: uploaded.originalName, fileId: uploaded.id })
        const message = `我上传了文件「${uploaded.originalName}」，请分析这份文档内容。`
        const userMessage: ChatMessage = {
          role: 'user',
          content: message,
          createdAt: new Date().toISOString()
        }
        this.messages.push(userMessage)
        await addMessageApi(conversationId, userMessage)
        const task = await submitTaskApi({
          capability: 'chat',
          action: 'message',
          input: {
            message: `${message}\n\n文档内容：\n${resume.rawText || ''}`,
            sessionId: this.sessionId
          }
        })
        const result = await waitForTaskResult(task)
        const output = result.output || {}
        if (output.session_id) {
          this.sessionId = output.session_id
          localStorage.setItem('agent_jd_session', this.sessionId)
        }
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: output.advice || output.answer || result.errorMsg || 'AI 暂时没有返回内容，请稍后重试。',
          createdAt: new Date().toISOString()
        }
        this.messages.push(assistantMessage)
        await addMessageApi(conversationId, { ...assistantMessage, taskUuid: result.taskUuid })
      } finally {
        this.loading = false
      }
    },
    async send(content: string) {
      const text = content.trim()
      if (!text) return
      const conversationId = await this.ensureConversation(text)
      const userMessage: ChatMessage = {
        role: 'user',
        content: text,
        createdAt: new Date().toISOString()
      }
      this.messages.push(userMessage)
      this.loading = true
      try {
        await addMessageApi(conversationId, userMessage)
        const task = await submitTaskApi({
          capability: 'chat',
          action: 'message',
          input: { message: text, sessionId: this.sessionId }
        })
        const result = await waitForTaskResult(task)
        const output = result.output || {}
        if (output.session_id) {
          this.sessionId = output.session_id
          localStorage.setItem('agent_jd_session', this.sessionId)
        }
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: output.advice || output.answer || result.errorMsg || 'AI 暂时没有返回内容，请稍后重试。',
          createdAt: new Date().toISOString()
        }
        this.messages.push(assistantMessage)
        await addMessageApi(conversationId, { ...assistantMessage, taskUuid: result.taskUuid })
      } finally {
        this.loading = false
      }
    }
  }
})

async function waitForTaskResult(initialTask: AiTask) {
  let task = initialTask
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (
      task.status === 2 ||
      task.status === 3 ||
      task.status === 4
    ) {
      return task
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1500))
    task = await getTaskResultApi(initialTask.taskUuid)
  }
  return task
}
