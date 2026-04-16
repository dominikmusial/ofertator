import { useMutation, useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface TitleToOptimize {
  offer_id: string
  current_title: string
}

export interface OptimizedTitleResult {
  offer_id: string
  current_title: string
  optimized_title: string
  analysis?: string
  character_count: number
  success: boolean
  error?: string
}

export interface OptimizeTitlesAIRequest {
  account_id: number
  titles: TitleToOptimize[]
  include_offer_parameters?: boolean
}

export interface OptimizeTitlesAIResponse {
  results: OptimizedTitleResult[]
  total_processed: number
  successful: number
  failed: number
}

export interface OptimizeTitlesAITaskResponse {
  task_id: string
}

// Hook to start AI optimization task (returns task_id)
export const useOptimizeTitlesAI = () => {
  return useMutation<OptimizeTitlesAITaskResponse, Error, OptimizeTitlesAIRequest>({
    mutationFn: async (data) => {
      const response = await api.post('/allegro/offers/optimize-titles-ai', data)
      return response.data
    },
  })
}

// Interface for AI optimization task status
export interface AIOptimizationTaskStatus {
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: OptimizeTitlesAIResponse | {
    status?: string
    progress?: number
    processed?: number
    total?: number
    successful?: number
    failed?: number
    exc_type?: string
    exc_message?: string
  }
}

// Hook to poll AI optimization task status
export const useAIOptimizationTaskStatus = (taskId: string | undefined) => {
  return useQuery<AIOptimizationTaskStatus>({
    queryKey: ['aiOptimizationTask', taskId],
    queryFn: async () => {
      if (!taskId) return null
      const response = await api.get(`/allegro/offers/task-status/${taskId}`)
      return response.data
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Stop polling when task is complete
      const data = query.state.data
      if (!data || data.status === 'SUCCESS' || data.status === 'FAILURE') {
        return false
      }
      return 3000 // Poll every 3 seconds while in progress
    },
  })
}


