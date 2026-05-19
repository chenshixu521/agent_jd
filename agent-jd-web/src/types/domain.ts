export interface UserInfo {
  id: string
  username: string
  email?: string
  phone?: string
  role?: string
}

export interface AuthResult {
  accessToken: string
  tokenType: string
  expiresIn: number
  user: UserInfo
}

export interface FileObject {
  id: string
  originalName: string
  contentType?: string
  sizeBytes: number
  url: string
}

export interface Resume {
  id: string
  title: string
  source?: number
  fileId?: string
  fileUrl?: string
  rawText?: string
  status?: number
  createdAt?: string
  updatedAt?: string
}

export interface Jd {
  id: string
  title: string
  company?: string
  city?: string
  rawText: string
  sourceUrl?: string
  status?: number
  createdAt?: string
  updatedAt?: string
}

export interface AiTask {
  id?: string
  taskUuid: string
  capability: string
  action: string
  bizId?: string
  status: number
  progress: number
  input?: unknown
  output?: any
  errorMsg?: string
  traceId?: string
  createdAt?: string
  startedAt?: string
  finishedAt?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt?: string
}
