<template>
  <el-card class="media-card" shadow="hover">
    <div class="media-preview">
      <img v-if="media.type === 'image'" :src="media.url" :alt="media.name" />
      <video v-else :src="media.url" controls />
    </div>
    <div class="media-info">
      <div class="name">{{ media.name }}</div>
      <div class="tags">
        <el-tag
          v-for="tag in media.tags"
          :key="tag"
          size="small"
          style="margin-right: 5px;"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button size="small" type="danger" @click="$emit('delete')">
          删除
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Media } from '../types'

defineProps<{
  media: Media
}>()

defineEmits<{
  delete: []
}>()
</script>

<style scoped>
.media-card {
  margin-bottom: 20px;
}

.media-preview {
  height: 200px;
  overflow: hidden;
  margin-bottom: 10px;
}

.media-preview img,
.media-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name {
  font-weight: bold;
  margin-bottom: 5px;
}

.tags {
  margin-bottom: 10px;
}
</style>