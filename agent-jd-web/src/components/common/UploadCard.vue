<template>
  <el-card class="upload-card">
    <el-upload
      drag
      :auto-upload="false"
      :show-file-list="true"
      :limit="1"
      :on-change="onChange"
    >
      <el-icon class="upload-icon">
        <UploadFilled />
      </el-icon>
      <div>拖拽文件到此处，或点击选择</div>
      <small>支持 PDF / DOCX / TXT</small>
    </el-upload>
  </el-card>
</template>
<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
const emit = defineEmits<{ selected: [file: File] }>()

function onChange(file: UploadFile) {
  if (file.raw) emit('selected', file.raw)
}
</script>
<style scoped>
.upload-card small {
  color: var(--color-muted);
}

.upload-icon {
  color: var(--color-primary);
  font-size: 42px;
}
</style>
