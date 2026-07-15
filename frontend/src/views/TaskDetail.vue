<template>
  <div class="task-detail">
    <div class="task-header">
      <h2>任务详情</h2>
      <el-tag :type="getStatusType(task?.status)">
        {{ getStatusName(task?.status) }}
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
        @select-media="handleSelectMedia"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import SubtitleSegmentComponent from '../components/SubtitleSegment.vue'

interface MatchResult {
  id: string
  media_id: string
  score: number
  keyword_score: number
  semantic_score: number
  reason: string
  rank: number
  media_name?: string
  media_url?: string
  media_type?: string
}

interface Segment {
  id: string
  task_id: string
  content: string
  keywords?: string[]
  sort_order: number
  selected_media_id?: string
  matches?: MatchResult[]
}

interface TaskDetail {
  task_id: string
  type: string
  status: string
  input_text?: string
  error_message?: string
  segments?: Segment[]
}

const route = useRoute()
const taskId = route.params.id as string

const task = ref<TaskDetail | null>(null)
const segments = ref<Segment[]>([])
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

const getStatusName = (status?: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || ''] || status || ''
}

const loadTask = async () => {
  try {
    const { data } = await taskApi.getStatus(taskId)
    task.value = data
    segments.value = data.segments || []
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(async () => {
    await loadTask()
    if (task.value?.status === 'completed' || task.value?.status === 'failed') {
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

const handleSelectMedia = async (segmentId: string, mediaId: string) => {
  try {
    await taskApi.updateSegment(taskId, segmentId, {
      selected_media_id: mediaId
    })
    ElMessage.success('已选择素材')
    // 更新本地状态
    const segment = segments.value.find(s => s.id === segmentId)
    if (segment) {
      segment.selected_media_id = mediaId
    }
  } catch (error) {
    ElMessage.error('选择失败')
  }
}

const retryTask = async () => {
  try {
    await taskApi.retry(taskId)
    ElMessage.success('任务已重新提交')
    loading.value = true
    await loadTask()
    if (task.value?.status === 'processing') {
      startPolling()
    }
    loading.value = false
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(async () => {
  await loadTask()
  if (task.value?.status === 'processing') {
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

.segments {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
