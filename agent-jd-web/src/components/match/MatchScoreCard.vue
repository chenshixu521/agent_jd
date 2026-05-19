<template>
  <el-card class="score-card">
    <div class="score">{{ score }}</div>
    <div>
      <b>{{ title }}</b>
      <p>{{ subtitle }}</p>
    </div>
  </el-card>
</template>
<script setup lang="ts">
defineProps<{
  score: number | string
  title: string
  subtitle?: string
}>()
</script>
<style scoped>
.score-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
}

.score {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  font-size: 24px;
  font-weight: 800;
}

p {
  margin: 4px 0 0;
  color: var(--color-muted);
}
</style>
