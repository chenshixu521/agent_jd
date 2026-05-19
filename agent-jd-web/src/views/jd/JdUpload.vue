<template>
  <div class="page fade-in">
    <div class="page-title">
      <div>
        <h1>JD 上传</h1>
        <p>录入目标岗位描述，驱动匹配度与简历优化。</p>
      </div>
    </div>

    <el-row :gutter="18">
      <el-col :span="10">
        <el-card>
          <el-form :model="form" label-position="top">
            <el-form-item label="岗位">
              <el-input v-model="form.title" />
            </el-form-item>
            <el-form-item label="公司">
              <el-input v-model="form.company" />
            </el-form-item>
            <el-form-item label="城市">
              <el-input v-model="form.city" />
            </el-form-item>
            <el-form-item label="JD 原文">
              <el-input v-model="form.rawText" type="textarea" :rows="12" />
            </el-form-item>
            <el-button type="primary" @click="save">保存 JD</el-button>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header>
            <b>岗位 JD</b>
          </template>
          <el-table :data="store.items">
            <el-table-column prop="title" label="岗位" />
            <el-table-column prop="company" label="公司" />
            <el-table-column prop="city" label="城市" />
            <el-table-column label="操作">
              <template #default="{row}">
                <el-button link type="primary" @click="store.current = row">选择</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useJdStore } from '@/stores/jd'

const store = useJdStore()
const form = reactive({
  title: 'Java 后端工程师',
  company: 'AI 科技公司',
  city: '上海',
  rawText: '要求 Spring Boot、MySQL、Redis、微服务，有 AI Agent 经验优先。'
})

onMounted(() => store.load())

async function save() {
  await store.create(form)
  ElMessage.success('JD 已保存')
}
</script>
