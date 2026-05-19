<template>
  <div class="page fade-in">
    <div class="page-title">
      <div>
        <h1>匹配度展示</h1>
        <p>选择已保存的简历和岗位 JD，生成 AI 匹配结果。</p>
      </div>
      <el-button type="primary" :loading="task.loading" @click="run">计算匹配度</el-button>
    </div>

    <el-card>
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="选择简历">
              <el-select v-model="resumeId" filterable placeholder="请选择简历" style="width: 100%">
                <el-option v-for="item in resume.items" :key="item.id" :label="item.title" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选择 JD">
              <el-select v-model="jdId" filterable placeholder="请选择 JD" style="width: 100%">
                <el-option
                  v-for="item in jd.items"
                  :key="item.id"
                  :label="`${item.title}${item.company ? ' · ' + item.company : ''}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <el-alert
        v-if="!resume.items.length"
        type="warning"
        show-icon
        :closable="false"
        title="还没有可用简历，请先到“简历上传”页面保存简历。"
      />
      <el-alert
        v-else-if="!selectedResume?.rawText"
        type="warning"
        show-icon
        :closable="false"
        title="当前简历没有文本内容。文件上传只保存文件本身，匹配分析需要在“简历文本”中粘贴或补充简历正文。"
      />
      <el-alert
        v-if="!jd.items.length"
        type="warning"
        show-icon
        :closable="false"
        title="还没有可用 JD，请先到“JD 上传”页面保存岗位描述。"
        style="margin-top: 10px"
      />
    </el-card>

    <div class="card-grid">
      <MatchScoreCard
        :score="match.total_score || match.totalScore || 0"
        title="总匹配度"
        subtitle="综合技能、经验与岗位要求"
      />
      <MatchScoreCard :score="match.hard_score || match.hardScore || 0" title="硬技能" />
      <MatchScoreCard :score="match.soft_score || match.softScore || 0" title="软技能" />
      <MatchScoreCard :score="match.exp_score || match.expScore || 0" title="经验匹配" />
    </div>

    <el-row :gutter="18">
      <el-col :span="12">
        <el-card>
          <template #header>
            <b>匹配技能</b>
          </template>
          <el-tag
            v-for="item in matchedSkills"
            :key="item"
            type="success"
            style="margin: 4px"
          >
            {{ item }}
          </el-tag>
          <el-empty v-if="!matchedSkills.length" description="暂无匹配技能" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <b>缺失技能</b>
          </template>
          <el-tag
            v-for="item in missingSkills"
            :key="item"
            type="warning"
            style="margin: 4px"
          >
            {{ item }}
          </el-tag>
          <el-empty v-if="!missingSkills.length" description="暂无缺失技能" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 18px">
      <template #header>
        <b>AI 匹配分析</b>
      </template>
      <MarkdownView :content="aiAnalysis" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownView from '@/components/common/MarkdownView.vue'
import MatchScoreCard from '@/components/match/MatchScoreCard.vue'
import { useJdStore } from '@/stores/jd'
import { useResumeStore } from '@/stores/resume'
import { useTaskStore } from '@/stores/task'

const task = useTaskStore()
const resume = useResumeStore()
const jd = useJdStore()
const resumeId = ref<string>()
const jdId = ref<string>()

const selectedResume = computed(() => resume.items.find((item) => item.id === resumeId.value))
const selectedJd = computed(() => jd.items.find((item) => item.id === jdId.value))
const match = computed(() => task.latest?.output?.match || {})
const matchedSkills = computed<string[]>(() => match.value.matched_skills || match.value.matchedSkills || [])
const missingSkills = computed<string[]>(() => match.value.missing_skills || match.value.missingSkills || [])
const aiAnalysis = computed(() => {
  if (!task.latest?.output?.match) return '计算匹配度后，这里会展示 AI 生成的匹配总结、优势、风险点和补强建议。'
  const suggestions = match.value.suggestions || []
  const advantages = match.value.advantages || []
  const risks = match.value.risks || []
  return [
    `## 匹配总结\n\n${match.value.summary || 'AI 已完成匹配分析。'}`,
    `## 候选人优势\n\n${formatList(advantages)}`,
    `## 风险点\n\n${formatList(risks)}`,
    `## 补强建议\n\n${formatList(suggestions)}`
  ].join('\n\n')
})

onMounted(async () => {
  await Promise.all([resume.load(), jd.load()])
  resumeId.value = resume.current?.id || resume.items[0]?.id
  jdId.value = jd.current?.id || jd.items[0]?.id
})

async function run() {
  if (!selectedResume.value) {
    ElMessage.warning('请先选择简历')
    return
  }
  if (!selectedJd.value) {
    ElMessage.warning('请先选择 JD')
    return
  }
  if (!selectedResume.value.rawText?.trim()) {
    ElMessage.warning('当前简历没有文本内容，请先补充简历正文')
    return
  }
  const created = await task.submit({
    capability: 'match',
    action: 'analyze',
    bizId: selectedResume.value.id,
    input: {
      resume_text: selectedResume.value.rawText,
      jd_text: selectedJd.value.rawText
    }
  })
  if (created.status !== 2) await task.waitForResult(created.taskUuid)
}

function formatList(items: string[]) {
  return items.length ? items.map((item) => `- ${item}`).join('\n') : '- 暂无'
}
</script>
