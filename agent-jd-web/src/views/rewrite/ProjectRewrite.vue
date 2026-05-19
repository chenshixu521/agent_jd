<template>
  <div class="page fade-in">
    <div class="page-title">
      <div>
        <h1>AI 项目改写</h1>
        <p>按 STAR 法则和目标 JD 重写项目经历。</p>
      </div>
      <el-button type="primary" :loading="task.loading || rewriting" @click="run">生成改写</el-button>
    </div>

    <el-row :gutter="18">
      <el-col :span="10">
        <el-card>
          <el-form label-position="top">
            <el-form-item label="项目经历">
              <el-input v-model="projectText" type="textarea" :rows="10" />
            </el-form-item>
            <el-form-item label="目标 JD">
              <el-input v-model="jdText" type="textarea" :rows="8" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header>
            <b>AI 改写结果</b>
          </template>
          <MarkdownView :content="result" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import MarkdownView from '@/components/common/MarkdownView.vue'
import { useTaskStore } from '@/stores/task'

const task = useTaskStore()
const rewriting = ref(false)
const projectText = ref('负责 AI 求职 Agent 平台后端开发，包含用户、简历、JD、AI任务等模块。')
const jdText = ref('招聘 Java 后端工程师，要求 Spring Boot、Redis、AI 项目经验。')
const result = computed(() => formatRewriteResult(task.latest?.output))

async function run() {
  rewriting.value = true
  try {
    const created = await task.submit({
      capability: 'project',
      action: 'rewrite',
      input: { project_text: projectText.value, jd_text: jdText.value }
    })
    if (created.status !== 2) await task.waitForResult(created.taskUuid)
  } finally {
    rewriting.value = false
  }
}

function formatRewriteResult(output: any) {
  if (rewriting.value || task.latest?.status === 0 || task.latest?.status === 1) {
    return '## 正在生成项目改写\n\nAI 正在结合项目经历与目标 JD 生成改写结果，请稍等。'
  }
  if (!output) return '生成后将在这里展示项目改写结果。'
  if (typeof output === 'string') return output
  if (output.rewrite?.rewritten) return output.rewrite.rewritten
  if (output.rewritten) return output.rewritten
  if (output.advice || output.answer) return output.advice || output.answer
  return `## 项目改写结果\n\n${JSON.stringify(output, null, 2)}`
}
</script>
