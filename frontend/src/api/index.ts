import axios from 'axios'
import type { Task, Media } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Task APIs
export const taskApi = {
  list(params?: { skip?: number; limit?: number }) {
    return api.get<Task[]>('/tasks', { params })
  },

  create(data: { type: string; content?: string }) {
    return api.post<Task>('/tasks', data)
  },

  getStatus(taskId: string) {
    return api.get<{
      task_id: string
      type: string
      status: string
      input_text?: string
      error_message?: string
      created_at?: string
      updated_at?: string
      segments?: Array<{
        id: string
        task_id: string
        content: string
        keywords?: string[]
        sort_order: number
        selected_media_id?: string
        matches?: Array<{
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
        }>
      }>
    }>(`/tasks/${taskId}`)
  },

  getSegments(taskId: string) {
    return api.get<Array<{
      id: string
      task_id: string
      content: string
      keywords?: string[]
      sort_order: number
      selected_media_id?: string
      matches?: Array<{
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
      }>
    }>>(`/tasks/${taskId}/segments`)
  },

  updateSegment(taskId: string, segmentId: string, data: { content?: string; sort_order?: number; selected_media_id?: string }) {
    return api.put(`/tasks/${taskId}/segments/${segmentId}`, data)
  },

  retry(taskId: string) {
    return api.post(`/tasks/${taskId}/retry`)
  }
}

// Media APIs
export const mediaApi = {
  list(params?: { keyword?: string; page?: number; size?: number }) {
    return api.get<{ items: Media[]; total: number }>('/media', { params })
  },

  get(mediaId: string) {
    return api.get<Media>(`/media/${mediaId}`)
  },

  upload(file: File, name?: string, tags?: string[]) {
    const formData = new FormData()
    formData.append('file', file)
    if (name) formData.append('name', name)
    if (tags) formData.append('tags', JSON.stringify(tags))
    return api.post<Media>('/media', formData)
  },

  delete(mediaId: string) {
    return api.delete(`/media/${mediaId}`)
  }
}

// Transcription APIs
export const transcribeApi = {
  create(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ task_id: string; status: string }>('/transcribe', formData)
  },

  getStatus(taskId: string) {
    return api.get<{ status: string; text?: string; error?: string }>(
      `/transcribe/${taskId}`
    )
  }
}

export default api
