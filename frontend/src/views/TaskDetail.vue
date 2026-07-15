<template>
  <div class="task-detail">
    <div class="task-header">
      <h2>任务详情</h2>
      <el-tag :type="getStatusType(task?.status)">
        {{ task?.status }}
      </el-tag>
    </div>

    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="task?.status === 'processing'" class="processing">
      <el-progress :percentage="50" status="warning" />
      <p>任务处理中，请稍候...</p>
    </div>

    <div v-else-if="task?.status === 'failed'" class="failed">
      <el-alert
        :title="task.error_message || '任务处理失败'"
        type="error"
        show-icon
      />
      <el-button type="primary" @click="retryTask" style="margin-top: 20px;">
        重试
      </el-button>
    </div>

    <div v-else class="segments">
      <SubtitleSegmentComponent
        v-for="segment in segments"
        :key="segment.id"
        :segment="segment"
        @update="loadSegments"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import type { Task, SubtitleSegment } from '../types'
import SubtitleSegmentComponent from '../components/SubtitleSegment.vue'

const route = useRoute()
const taskId = route.params.id as string

const task = ref<Task | null>(null)
const segments = ref<SubtitleSegment[]>([])
const loading = ref(true)
let pollTimer: number | null = null

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || ''] || 'info'
}

const loadTask = async () => {
  try {
    const { data } = await taskApi.getStatus(taskId)
    task.value = {
      ...data,
      id: data.task_id
    } as unknown as Task
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

const loadSegments = async () => {
  try {
    const { data } = await taskApi.getSegments(taskId)
    segments.value = data
  } catch (error) {
    ElMessage.error('加载字幕片段失败')
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(async () => {
    await loadTask()
    if (task.value?.status === 'completed') {
      await loadSegments()
      stopPolling()
    } else if (task.value?.status === 'failed') {
      stopPolling()
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const retryTask = async () => {
  try {
    await taskApi.retry(taskId)
    ElMessage.success('任务已重新提交')
    loading.value = true
    await loadTask()
    startPolling()
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(async () => {
  await loadTask()
  if (task.value?.status === 'completed') {
    await loadSegments()
  } else if (task.value?.status === 'processing') {
    startPolling()
  }
  loading.value = false
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.loading, .processing, .failed {
  text-align: center;
  padding: 50px;
}
</style>
