<template>
  <div class="media-library">
    <div class="header">
      <h2>素材库</h2>
      <el-upload
        :auto-upload="false"
        :on-change="handleUpload"
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

    <el-empty v-if="mediaList.length === 0" description="暂无素材" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mediaApi } from '../api'
import type { Media } from '../types'
import MediaCard from '../components/MediaCard.vue'

const mediaList = ref<Media[]>([])
const searchKeyword = ref('')

const loadMedia = async () => {
  try {
    const { data } = await mediaApi.list({ keyword: searchKeyword.value })
    mediaList.value = data.items
  } catch (error) {
    ElMessage.error('加载素材失败')
  }
}

const searchMedia = () => {
  loadMedia()
}

const handleUpload = async (file: any) => {
  try {
    await mediaApi.upload(file.raw, file.name)
    ElMessage.success('上传成功')
    loadMedia()
  } catch (error) {
    ElMessage.error('上传失败')
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
</style>