<template>
  <div class="page fade-in">
    <div class="page-title">
      <div>
        <h1>简历上传</h1>
        <p>上传 PDF / DOCX / TXT 后自动解析正文，也可以手动编辑后保存。</p>
      </div>
    </div>

    <el-row :gutter="18">
      <el-col :span="10">
        <UploadCard @selected="onFile" />
        <el-alert
          style="margin-top: 12px"
          type="success"
          show-icon
          :closable="false"
          title="上传文件后会自动解析并保存为简历资产，解析结果会显示在下方。"
        />
        <el-card style="margin-top: 16px">
          <el-form :model="form" label-position="top">
            <el-form-item label="简历标题">
              <el-input v-model="form.title" />
            </el-form-item>
            <el-form-item label="解析/编辑后的简历文本">
              <el-input
                v-model="form.rawText"
                type="textarea"
                :rows="12"
                placeholder="上传文件后自动填充，也可以直接粘贴或修改简历正文"
              />
            </el-form-item>
            <el-space wrap>
              <el-button type="primary" :loading="saving" @click="save">保存当前文本</el-button>
              <el-button @click="resetForm">清空</el-button>
            </el-space>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header>
            <b>我的简历</b>
          </template>
          <el-table :data="store.items" v-loading="store.loading">
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="createdAt" label="创建时间" width="180" />
            <el-table-column label="文本" width="100">
              <template #default="{row}">
                <el-tag :type="row.rawText ? 'success' : 'warning'" effect="plain">
                  {{ row.rawText ? '已解析' : '缺正文' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="{row}">
                <el-button link type="primary" @click="selectResume(row)">查看</el-button>
                <el-button link type="danger" @click="removeResume(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import UploadCard from '@/components/common/UploadCard.vue'
import { uploadFileApi } from '@/api/file'
import { useResumeStore } from '@/stores/resume'
import type { Resume } from '@/types/domain'

const store = useResumeStore()
const saving = ref(false)
const form = reactive({ title: '我的求职简历', rawText: '', fileId: undefined as string | undefined })

onMounted(() => store.load())

async function onFile(file: File) {
  saving.value = true
  try {
    const uploaded = await uploadFileApi(file)
    form.fileId = uploaded.id
    form.title = uploaded.originalName
    const item = await store.create({ title: uploaded.originalName, fileId: uploaded.id })
    form.rawText = item.rawText || ''
    ElMessage.success('简历已上传并解析保存')
  } finally {
    saving.value = false
  }
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写简历标题')
    return
  }
  if (!form.rawText.trim() && !form.fileId) {
    ElMessage.warning('请上传简历文件或填写简历正文')
    return
  }
  saving.value = true
  try {
    const item = await store.create(form)
    form.rawText = item.rawText || form.rawText
    ElMessage.success('简历已保存')
  } finally {
    saving.value = false
  }
}

async function removeResume(row: Resume) {
  await ElMessageBox.confirm(`确认删除简历「${row.title}」吗？`, '删除简历', { type: 'warning' })
  await store.remove(row.id)
  if (form.fileId === row.fileId && form.title === row.title) resetForm()
  ElMessage.success('简历已删除')
}

function selectResume(row: Resume) {
  store.current = row
  form.title = row.title
  form.rawText = row.rawText || ''
  form.fileId = row.fileId
}

function resetForm() {
  form.title = '我的求职简历'
  form.rawText = ''
  form.fileId = undefined
}
</script>
