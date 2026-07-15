<template>
  <div class="subtitle-segment">
    <el-card class="segment-card">
      <template #header>
        <div class="segment-header">
          <span class="order">[{{ segment.sort_order + 1 }}]</span>
          <div class="segment-content">
            <el-input
              v-model="editContent"
              type="textarea"
              :rows="2"
              @blur="saveContent"
            />
          </div>
        </div>
      </template>

      <div class="keywords" v-if="segment.keywords?.length">
        <span class="label">关键词:</span>
        <el-tag
          v-for="keyword in segment.keywords"
          :key="keyword"
          size="small"
          type="info"
        >
          {{ keyword }}
        </el-tag>
      </div>

      <div class="matches-section" v-if="segment.matches?.length">
        <h4>推荐素材</h4>
        <div class="matches-list">
          <div
            v-for="match in segment.matches"
            :key="match.id"
            class="match-item"
            :class="{ selected: segment.selected_media_id === match.media_id }"
            @click="$emit('select-media', segment.id, match.media_id)"
          >
            <div class="media-preview">
              <img v-if="match.media_url" :src="match.media_url" :alt="match.media_name" />
              <div v-else class="placeholder">暂无预览</div>
            </div>
            <div class="match-info">
              <div class="media-name">{{ match.media_name || '未命名素材' }}</div>
              <div class="match-score">
                匹配度: {{ (match.score * 100).toFixed(0) }}%
              </div>
              <div class="match-reason">{{ match.reason }}</div>
              <div class="match-details">
                <span>关键词: {{ (match.keyword_score * 100).toFixed(0) }}%</span>
                <span>语义: {{ (match.semantic_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <div class="select-indicator" v-if="segment.selected_media_id === match.media_id">
              ✓ 已选择
            </div>
          </div>
        </div>
      </div>

      <div class="no-matches" v-else-if="segment.matches?.length === 0">
        <el-empty description="暂无匹配素材" :image-size="60" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'

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

const props = defineProps<{
  segment: {
    id: string
    task_id: string
    content: string
    keywords?: string[]
    sort_order: number
    selected_media_id?: string
    matches?: MatchResult[]
  }
}>()

defineEmits<{
  'select-media': [segmentId: string, mediaId: string]
}>()

const editContent = ref(props.segment.content)

watch(() => props.segment.content, (newVal) => {
  editContent.value = newVal
})

const saveContent = async () => {
  if (editContent.value === props.segment.content) return

  try {
    await taskApi.updateSegment(props.segment.task_id, props.segment.id, {
      content: editContent.value
    })
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.segment-card {
  margin-bottom: 0;
}

.segment-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.order {
  font-weight: bold;
  color: #409eff;
  min-width: 30px;
}

.segment-content {
  flex: 1;
}

.keywords {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.keywords .label {
  color: #606266;
  font-size: 14px;
}

.keywords .el-tag {
  margin: 0;
}

.matches-section {
  margin-top: 15px;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.matches-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
}

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.match-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.match-item.selected {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.media-preview {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
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
  font-size: 12px;
}

.match-info {
  flex: 1;
  min-width: 0;
}

.media-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.match-score {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  margin-bottom: 4px;
}

.match-reason {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.match-details {
  font-size: 12px;
  color: #909399;
}

.match-details span {
  margin-right: 12px;
}

.select-indicator {
  color: #67c23a;
  font-weight: 500;
  font-size: 12px;
}

.no-matches {
  padding: 20px;
  text-align: center;
}
</style>
