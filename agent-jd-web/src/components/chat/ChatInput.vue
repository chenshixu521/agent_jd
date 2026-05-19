<template>
  <div class="chat-input">
    <el-upload :auto-upload="false" :show-file-list="false" :on-change="onUpload">
      <el-button :disabled="loading">上传文档</el-button>
    </el-upload>
    <el-input
      v-model="text"
      type="textarea"
      :rows="3"
      resize="none"
      placeholder="输入你的问题，例如：帮我分析这个 JD 是否适合我的简历"
      @keydown.enter.exact.prevent="submit"
    />
    <el-button type="primary" :loading="loading" @click="submit">发送</el-button>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import type { UploadFile } from 'element-plus'
defineProps<{ loading?: boolean }>()
const emit = defineEmits<{
  send: [content: string]
  upload: [file: File]
}>()
const text = ref('')

function submit() {
  const value = text.value.trim()
  if (!value) return
  emit('send', value)
  text.value = ''
}

function onUpload(file: UploadFile) {
  if (file.raw) emit('upload', file.raw)
}
</script>
<style scoped>
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
</style>
