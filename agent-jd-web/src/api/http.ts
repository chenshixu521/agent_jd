import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import type { ApiResponse } from '@/types/api'
import { clearToken, getToken } from '@/utils/token'

const http = axios.create({
  baseURL: '',
  timeout: 120000
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.headers['X-Trace-Id'] = crypto.randomUUID?.() || `${Date.now()}`
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse<unknown>
    if (typeof body?.code === 'number' && body.code !== 0) {
      if (body.code === 40101 || body.code === 40102) {
        clearToken()
        router.push('/login')
      }
      return Promise.reject(new Error(body.message || body.msg || '请求失败'))
    }
    return body?.data ?? response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      clearToken()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    return await http.request<unknown, T>(config)
  } catch (error: any) {
    ElMessage.error(error?.message || '网络异常')
    throw error
  }
}

export default http
