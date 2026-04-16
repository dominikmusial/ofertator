import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'

interface TaskStatus {
  task_id: string
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: {
    status?: string
    current?: number
    total?: number
    current_offer?: string
    success_count?: number
    failure_count?: number
    total_processed?: number
    successful_offers?: string[]
    failed_offers?: Array<{ offer_id: string; error: string }>
    exc_message?: string
  }
  meta?: {
    status?: string
    progress?: number
    successful?: number
    failed?: number
    total_offers?: number
    successful_offers?: string[]
    failed_offers?: Array<{ offer_id: string; error: string }>
    success_count?: number
    failure_count?: number
  }
}

export function useTaskStatus(taskId?: string, enabled: boolean = true) {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: ['task-status', taskId],
    queryFn: async (): Promise<TaskStatus> => {
      const { data } = await api.get<TaskStatus>(`/allegro/offers/task-status/${taskId}`)
      return data
    },
    enabled: !!taskId && enabled,
    refetchInterval: (query) => {
      // Stop polling when task is completed
      if (query.state.data?.status === 'SUCCESS' || query.state.data?.status === 'FAILURE') {
        return false
      }
      return 2000 // Poll every 2 seconds
    }
  })

  // Handle success case with useEffect equivalent
  if (query.data?.status === 'SUCCESS' && query.isFetched) {
    queryClient.invalidateQueries({ queryKey: ['offers'] })
  }

  return query
} 