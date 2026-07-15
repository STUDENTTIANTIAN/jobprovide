<template>
  <div class="media-library">
    <div class="header">
      <h2>素材库</h2>
      <el-upload
        :auto-upload="false"
        :on-change="handleFileSelect"
        :show-file-list="false"
      >
        <el-button type="primary">上传素材</el-button>
      </el-upload>
    </div>

    <div class="search">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索素材..."
        @input="searchMedia"
        clearable
      />
    </div>

    <div class="media-grid">
      <MediaCard
        v-for="media in mediaList"
        :key="media.id"
        :media="media"
        @delete="deleteMedia(media.id)"
      />
    </div>

    <el-empty v-if="mediaList.length === 0 && !loading" description="暂无素材" />

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传素材"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="文件">
          <div class="file-info" v-if="uploadForm.file">
            <el-icon><Document /></el-icon>
            <span>{{ uploadForm.file.name }}</span>
            <el-tag size="small" type="info">{{ formatSize(uploadForm.file.size) }}</el-tag>
          </div>
        </el-form-item>

        <el-form-item label="名称">
          <el-input v-model="uploadForm.name" placeholder="素材名称（可选）" />
        </el-form-item>

        <el-form-item label="标签">
          <div class="tags-input">
            <el-tag
              v-for="tag in uploadForm.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="tagInputVisible"
              ref="tagInputRef"
              v-model="tagInputValue"
              class="tag-input"
              size="small"
              @keyup.enter="addTag"
              @blur="addTag"
              placeholder="输入标签后回车"
            />
            <el-button v-else size="small" @click="showTagInput">
              + 添加标签
            </el-button>
          </div>
          <div class="tag-hint">常用标签：科技、编程、教学、数据、AI、开发</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import { mediaApi } from '../api'
import type { Media } from '../types'
import MediaCard from '../components/MediaCard.vue'

const mediaList = ref<Media[]>([])
const searchKeyword = ref('')
const loading = ref(false)

// 上传对话框相关
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadForm = ref({
  file: null as File | null,
  name: '',
  tags: [] as string[]
})
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

const loadMedia = async () => {
  loading.value = true
  try {
    const { data } = await mediaApi.list({ keyword: searchKeyword.value })
    mediaList.value = data.items
  } catch (error) {
    ElMessage.error('加载素材失败')
  } finally {
    loading.value = false
  }
}

const searchMedia = () => {
  loadMedia()
}

const handleFileSelect = (file: any) => {
  uploadForm.value = {
    file: file.raw,
    name: file.name.replace(/\.[^/.]+$/, ''), // 去掉扩展名作为默认名称
    tags: []
  }
  uploadDialogVisible.value = true
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.input?.focus()
  })
}

const addTag = () => {
  const tag = tagInputValue.value.trim()
  if (tag && !uploadForm.value.tags.includes(tag)) {
    uploadForm.value.tags.push(tag)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

const removeTag = (tag: string) => {
  uploadForm.value.tags = uploadForm.value.tags.filter(t => t !== tag)
}

const confirmUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    await mediaApi.upload(uploadForm.value.file, uploadForm.value.name, uploadForm.value.tags)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    uploadForm.value = { file: null, name: '', tags: [] }
    loadMedia()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const deleteMedia = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除该素材？', '提示', {
      type: 'warning'
    })
    await mediaApi.delete(id)
    ElMessage.success('删除成功')
    loadMedia()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadMedia()
})
</script>

<style scoped>
.media-library {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search {
  margin-bottom: 20px;
  max-width: 400px;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.tag-input {
  width: 100px;
}

.tag-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
