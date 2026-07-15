<template>
  <div class="task-list">
    <el-button type="primary" @click="$router.push('/tasks/new')">
      新建任务
    </el-button>

    <el-table :data="tasks" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="任务ID" width="120" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag>{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewTask(row.id)">查看</el-button>
          <el-button size="small" type="warning" @click="retryTask(row.id)">
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>
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

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const loadTasks = async () => {
  try {
    // TODO: 实现任务列表API
    tasks.value = []
  } catch (error) {
    ElMessage.error('加载任务列表失败')
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
</style>
