export interface Task {
  id: string
  type: 'video' | 'audio' | 'text'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  input_text?: string
  input_file_url?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface SubtitleSegment {
  id: string
  task_id: string
  content: string
  start_time?: number
  end_time?: number
  keywords?: string[]
  sort_order: number
  selected_media_id?: string
  matches?: MatchResult[]
}

export interface Media {
  id: string
  type: 'image' | 'video'
  url: string
  thumbnail_url?: string
  name?: string
  tags?: string[]
  keywords?: string[]
  duration?: number
  created_at: string
}

export interface MatchResult {
  id: string
  segment_id: string
  media_id: string
  score?: number
  keyword_score?: number
  semantic_score?: number
  reason?: string
  rank?: number
}
