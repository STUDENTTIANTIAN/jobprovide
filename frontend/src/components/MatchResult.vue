<template>
  <div class="match-result" :class="{ selected: isSelected }">
    <el-card shadow="hover" @click="$emit('select', match.media_id)">
      <div class="match-info">
        <div class="media-preview">
          <img v-if="media" :src="media.url" :alt="media.name" />
          <div v-else class="placeholder">暂无预览</div>
        </div>
        <div class="match-details">
          <div class="score">
            匹配度: {{ match.score != null ? (match.score * 100).toFixed(0) : 'N/A' }}%
          </div>
          <div class="reason">{{ match.reason }}</div>
          <div class="scores">
            <span>关键词: {{ match.keyword_score != null ? (match.keyword_score * 100).toFixed(0) : 'N/A' }}%</span>
            <span>语义: {{ match.semantic_score != null ? (match.semantic_score * 100).toFixed(0) : 'N/A' }}%</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import type { MatchResult, Media } from '../types'

defineProps<{
  match: MatchResult
  media?: Media
  isSelected?: boolean
}>()

defineEmits<{
  select: [mediaId: string]
}>()
</script>

<style scoped>
.match-result {
  cursor: pointer;
  margin-bottom: 10px;
}

.match-result.selected {
  border: 2px solid #409eff;
}

.match-info {
  display: flex;
  gap: 15px;
}

.media-preview {
  width: 100px;
  height: 100px;
  overflow: hidden;
  border-radius: 4px;
}

.media-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}

.match-details {
  flex: 1;
}

.score {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.reason {
  color: #606266;
  margin-bottom: 5px;
}

.scores {
  font-size: 12px;
  color: #909399;
}

.scores span {
  margin-right: 10px;
}
</style>
