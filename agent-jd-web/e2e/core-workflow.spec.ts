import { expect, request as requestFactory, test, type APIRequestContext, type APIResponse } from '@playwright/test'

interface ApiEnvelope<T> {
  code: number
  message?: string
  msg?: string
  data: T
}

interface TaskResult {
  taskUuid: string
  status: number
  output?: Record<string, any>
  errorMsg?: string
}

async function dataOf<T>(response: APIResponse): Promise<T> {
  expect(response.ok(), await response.text()).toBeTruthy()
  const body = await response.json() as ApiEnvelope<T>
  expect(body.code, body.message || body.msg).toBe(0)
  return body.data
}

async function waitForTask(api: APIRequestContext, taskUuid: string, statuses: Set<number>): Promise<TaskResult> {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    const task = await dataOf<TaskResult>(await api.get(`/api/tasks/${taskUuid}/result`))
    statuses.add(task.status)
    if (task.status === 2) return task
    if (task.status === 3 || task.status === 4) {
      throw new Error(`Task ${taskUuid} failed: ${task.errorMsg || `status ${task.status}`}`)
    }
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  throw new Error(`Task ${taskUuid} did not finish before the E2E timeout`)
}

async function submitAndWait(
  api: APIRequestContext,
  payload: Record<string, unknown>,
  statuses: Set<number>
): Promise<TaskResult> {
  const created = await dataOf<TaskResult>(await api.post('/api/tasks', { data: payload }))
  statuses.add(created.status)
  return waitForTask(api, created.taskUuid, statuses)
}

test('runs the core job-agent workflow with task recovery infrastructure', async ({ page }, testInfo) => {
  const baseURL = testInfo.project.use.baseURL as string
  const username = `e2e_${Date.now()}_${testInfo.workerIndex}`
  const password = 'E2eTest_2026'
  const anonymousApi = await requestFactory.newContext({ baseURL })
  const browserErrors: string[] = []
  page.on('console', message => {
    if (message.type() === 'error') browserErrors.push(`console: ${message.text()}`)
  })
  page.on('pageerror', error => browserErrors.push(`page: ${error.message}`))

  const auth = await dataOf<{ accessToken: string }>(await anonymousApi.post('/api/auth/register', {
    data: {
      username,
      password,
      email: `${username}@example.test`
    }
  }))
  const api = await requestFactory.newContext({
    baseURL,
    extraHTTPHeaders: { Authorization: `Bearer ${auth.accessToken}` }
  })

  try {
    const resumeText = [
      '候选人负责 Java 后端服务开发，使用 Spring Boot、MySQL 和 Redis。',
      '参与 AI 求职 Agent 项目，负责异步任务队列、失败重试和服务恢复验证。',
      '使用 Python、LangGraph、FAISS 与 BM25 构建检索和生成流程。'
    ].join('\n')
    const jdText = '招聘 Java 后端工程师，要求掌握 Spring Boot、MySQL、Redis，具备异步任务和 AI Agent 项目经验。'

    const uploaded = await dataOf<{ id: string; originalName: string }>(await api.post('/api/files/upload', {
      multipart: {
        file: {
          name: 'e2e-resume.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from(resumeText, 'utf8')
        }
      }
    }))
    expect(uploaded.originalName).toBe('e2e-resume.txt')

    const resume = await dataOf<{ id: string; rawText: string }>(await api.post('/api/resumes', {
      data: { title: 'E2E Java Resume', fileId: uploaded.id }
    }))
    expect(resume.rawText).toContain('Spring Boot')

    const jd = await dataOf<{ id: string; rawText: string }>(await api.post('/api/jds', {
      data: { title: 'E2E Java Backend', company: 'E2E Company', city: 'Shanghai', rawText: jdText }
    }))
    expect(jd.rawText).toContain('Redis')

    const observedStatuses = new Set<number>()
    const matchTask = await submitAndWait(api, {
      capability: 'match',
      action: 'analyze',
      bizId: resume.id,
      input: { resume_text: resume.rawText, jd_text: jd.rawText }
    }, observedStatuses)
    expect(matchTask.output?.match?.total_score).toBe(82)
    expect(matchTask.output?.match?.evidence?.length).toBeGreaterThan(0)

    const optimizeTask = await submitAndWait(api, {
      capability: 'resume',
      action: 'optimize',
      bizId: resume.id,
      input: { resume_text: resume.rawText, jd_text: jd.rawText }
    }, observedStatuses)
    expect(optimizeTask.output?.advice).toContain('简历优化建议')
    expect(optimizeTask.output?.validation).toMatchObject({ valid: true, attempts: 1 })

    const rewriteTask = await submitAndWait(api, {
      capability: 'project',
      action: 'rewrite',
      input: {
        project_text: '负责 AI 求职 Agent 的 Java 服务、Redis 任务队列和 Python Agent 对接。',
        jd_text: jd.rawText
      }
    }, observedStatuses)
    expect(rewriteTask.output?.rewrite?.rewritten).toContain('STAR 改写版')
    expect(observedStatuses).toEqual(new Set([0, 1, 2]))

    await page.goto('/login')
    await page.getByPlaceholder('请输入用户名').fill(username)
    await page.getByPlaceholder('请输入密码').fill(password)
    await page.getByRole('button', { name: '进入平台' }).click()
    await expect(page).toHaveURL(`${baseURL}/`)

    const chatInput = page.getByPlaceholder('输入你的问题，例如：帮我分析这个 JD 是否适合我的简历')
    await chatInput.fill('E2E_FIRST：我的项目应该突出什么？')
    await page.getByRole('button', { name: '发送', exact: true }).click()
    await expect(page.getByText('FAKE_E2E_REPLY', { exact: false })).toBeVisible()
    const firstSessionId = await page.evaluate(() => localStorage.getItem('agent_jd_session'))
    expect(firstSessionId).toBeTruthy()

    await chatInput.fill('E2E_SECOND：请结合上一轮继续回答。')
    await page.getByRole('button', { name: '发送', exact: true }).click()
    await expect(page.getByText('FAKE_E2E_CONTEXT_OK', { exact: false })).toBeVisible()
    expect(await page.evaluate(() => localStorage.getItem('agent_jd_session'))).toBe(firstSessionId)

    const conversationId = await page.evaluate(() => localStorage.getItem('agent_jd_conversation_id'))
    expect(conversationId).toBeTruthy()
    const messages = await dataOf<Array<{ role: string; content: string }>>(
      await api.get(`/api/conversations/${conversationId}/messages`)
    )
    expect(messages.map(message => message.role)).toEqual(['user', 'assistant', 'user', 'assistant'])
    expect(messages.at(-1)?.content).toContain('FAKE_E2E_CONTEXT_OK')
    expect(browserErrors).toEqual([])
  } finally {
    await api.dispose()
    await anonymousApi.dispose()
  }
})
