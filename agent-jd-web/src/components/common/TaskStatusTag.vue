<template>
  <el-tag :type="type" effect="plain">{{ statusText(status) }}</el-tag>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { statusText } from '@/utils/format'
const props = defineProps<{ status: number }>()
const type = computed(() =>
  props.status === 2
    ? 'success'
    : props.status === 3
      ? 'danger'
      : props.status === 1
        ? 'warning'
        : 'info'
)
</script>
