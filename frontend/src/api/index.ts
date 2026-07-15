import axios from 'axios'
import type { Task, SubtitleSegment, Media } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Task APIs
export const taskApi = {
  create(data: { type: string; content?: string }) {
    return api.post<Task>('/tasks', data)
  },

  getStatus(taskId: string) {
    return api.get<{ task_id: string; status: string; segments_count?: number }>(
      `/tasks/${taskId}`
    )
  },

  getSegments(taskId: string) {
    return api.get<SubtitleSegment[]>(`/tasks/${taskId}/segments`)
  },

  updateSegment(taskId: string, segmentId: string, data: Partial<SubtitleSegment>) {
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
