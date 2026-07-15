<template>
  <div class="task-new">
    <h2>新建字幕任务</h2>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="文本输入" name="text">
        <el-input
          v-model="textContent"
          type="textarea"
          :rows="10"
          placeholder="请输入字幕文本..."
        />
        <el-button
          type="primary"
          @click="createTextTask"
          :loading="loading"
          style="margin-top: 20px;"
        >
          创建任务
        </el-button>
      </el-tab-pane>

      <el-tab-pane label="上传文件" name="file">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".mp4,.avi,.mov,.mp3,.wav"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 mp4, avi, mov, mp3, wav 格式
            </div>
          </template>
        </el-upload>
        <el-button
          type="primary"
          @click="uploadFile"
          :loading="loading"
          :disabled="!selectedFile"
          style="margin-top: 20px;"
        >
          上传并创建任务
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi, transcribeApi } from '../api'

const router = useRouter()
const activeTab = ref('text')
const textContent = ref('')
const selectedFile = ref<File | null>(null)
const loading = ref(false)

const createTextTask = async () => {
  if (!textContent.value.trim()) {
    ElMessage.warning('请输入字幕文本')
    return
  }

  loading.value = true
  try {
    const { data } = await taskApi.create({
      type: 'text',
      content: textContent.value
    })
    ElMessage.success('任务创建成功')
    router.push(`/tasks/${data.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file: { raw: File }) => {
  selectedFile.value = file.raw
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  loading.value = true
  try {
    const { data } = await transcribeApi.create(selectedFile.value)
    ElMessage.success('文件上传成功，正在识别...')
    router.push(`/tasks/${data.task_id}`)
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.task-new {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
