<template>
  <div class="task-list">
    <div class="header">
      <h2>字幕任务列表</h2>
      <el-button type="primary" @click="$router.push('/tasks/new')">
        新建任务
      </el-button>
    </div>

    <el-table :data="tasks" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="id" label="任务ID" width="120">
        <template #default="{ row }">
          {{ row.id?.substring(0, 8) }}...
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.type)">{{ getTypeName(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusName(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="input_text" label="输入内容" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.input_text || '文件上传' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewTask(row.id)">查看</el-button>
          <el-button size="small" type="warning" @click="retryTask(row.id)" v-if="row.status === 'failed'">
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import type { Task } from '../types'

const router = useRouter()
const tasks = ref<Task[]>([])
const loading = ref(false)

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusName = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getTypeColor = (type: string) => {
  const map: Record<string, string> = {
    text: '',
    audio: 'warning',
    video: 'danger'
  }
  return map[type] || ''
}

const getTypeName = (type: string) => {
  const map: Record<string, string> = {
    text: '文本',
    audio: '音频',
    video: '视频'
  }
  return map[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const loadTasks = async () => {
  loading.value = true
  try {
    const { data } = await taskApi.list()
    tasks.value = data
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const viewTask = (id: string) => {
  router.push(`/tasks/${id}`)
}

const retryTask = async (id: string) => {
  try {
    await taskApi.retry(id)
    ElMessage.success('任务已重新提交')
    loadTasks()
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  margin: 0;
}
</style>
