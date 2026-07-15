<template>
  <div class="subtitle-segment">
    <el-card class="segment-card">
      <template #header>
        <div class="segment-header">
          <span class="order">[{{ segment.sort_order + 1 }}]</span>
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="2"
            @blur="saveContent"
          />
        </div>
      </template>

      <div class="keywords" v-if="segment.keywords?.length">
        <span>关键词:</span>
        <el-tag
          v-for="keyword in segment.keywords"
          :key="keyword"
          size="small"
          style="margin-left: 5px;"
        >
          {{ keyword }}
        </el-tag>
      </div>

      <div class="matches" v-if="segment.matches?.length">
        <h4>推荐素材</h4>
        <MatchResult
          v-for="match in segment.matches"
          :key="match.id"
          :match="match"
          :is-selected="segment.selected_media_id === match.media_id"
          @select="selectMedia"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import MatchResult from './MatchResult.vue'
import type { SubtitleSegment } from '../types'
import { taskApi } from '../api'

const props = defineProps<{
  segment: SubtitleSegment
}>()

const emit = defineEmits<{
  update: []
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
    emit('update')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const selectMedia = async (mediaId: string) => {
  try {
    await taskApi.updateSegment(props.segment.task_id, props.segment.id, {
      selected_media_id: mediaId
    })
    ElMessage.success('已选择素材')
    emit('update')
  } catch (error) {
    ElMessage.error('选择失败')
  }
}
</script>

<style scoped>
.segment-card {
  margin-bottom: 20px;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.order {
  font-weight: bold;
  color: #409eff;
}

.keywords {
  margin-top: 10px;
  color: #606266;
}

.matches {
  margin-top: 15px;
}

.matches h4 {
  margin-bottom: 10px;
  color: #303133;
}
</style>
