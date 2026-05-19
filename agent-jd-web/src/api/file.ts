import { request } from '@/api/http'
import type { FileObject } from '@/types/domain'

export function uploadFileApi(file: File) {
  const data = new FormData()
  data.append('file', file)
  return request<FileObject>({ url: '/api/files/upload', method: 'POST', data })
}
