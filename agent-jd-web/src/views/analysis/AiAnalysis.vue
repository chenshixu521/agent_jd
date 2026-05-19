<template>
  <div class="page fade-in">
    <div class="page-title">
      <div>
        <h1>AI 分析</h1>
        <p>基于简历与 JD 生成优化建议。</p>
      </div>
      <el-button type="primary" :loading="task.loading" @click="run">开始分析</el-button>
    </div>

    <el-row :gutter="18">
      <el-col :span="8">
        <el-card>
          <el-form label-position="top">
            <el-form-item label="选择简历">
              <el-select v-model="resumeId" style="width: 100%">
                <el-option v-for="i in resume.items" :key="i.id" :label="i.title" :value="i.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择 JD">
              <el-select v-model="jdId" style="width: 100%">
                <el-option v-for="i in jd.items" :key="i.id" :label="i.title" :value="i.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>
            <b>分析结果</b>
            <TaskStatusTag v-if="task.latest" :status="task.latest.status" />
          </template>
          <MarkdownView :content="content" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MarkdownView from '@/components/common/MarkdownView.vue'
import TaskStatusTag from '@/components/common/TaskStatusTag.vue'
import { useJdStore } from '@/stores/jd'
import { useResumeStore } from '@/stores/resume'
import { useTaskStore } from '@/stores/task'

const resume = useResumeStore()
const jd = useJdStore()
const task = useTaskStore()
const resumeId = ref<string>()
const jdId = ref<string>()
const content = computed(() => formatAnalysisContent(task.latest?.output))

onMounted(async () => {
  await resume.load()
  await jd.load()
  resumeId.value = resume.items[0]?.id
  jdId.value = jd.items[0]?.id
})

async function run() {
  const r = resume.items.find((item) => item.id === resumeId.value)
  const j = jd.items.find((item) => item.id === jdId.value)
  const created = await task.submit({
    capability: 'resume',
    action: 'optimize',
    bizId: r?.id,
    input: { resume_text: r?.rawText, jd_text: j?.rawText }
  })
  if (created.status !== 2) await task.waitForResult(created.taskUuid)
}

function formatAnalysisContent(output: any) {
  if (!output) return '点击开始分析后，这里展示 Markdown 格式的 AI 建议。'
  if (typeof output === 'string') return output
  if (output.advice || output.answer) return output.advice || output.answer
  const parts = ['## 分析结果']
  if (output.match) {
    const matchedSkills = output.match.matched_skills || output.match.matchedSkills || []
    const missingSkills = output.match.missing_skills || output.match.missingSkills || []
    parts.push([
      '### 匹配度',
      `- **总分**：${output.match.total_score ?? output.match.totalScore ?? '-'}`,
      `- **已匹配技能**：${matchedSkills.join('、') || '-'}`,
      `- **缺失技能**：${missingSkills.join('、') || '-'}`
    ].join('\n\n'))
  }
  if (output.jd?.summary) parts.push(`### JD 摘要\n\n${output.jd.summary}`)
  if (output.keywords) parts.push(`### 关键词\n\n${JSON.stringify(output.keywords)}`)
  return parts.join('\n\n')
}
</script>
