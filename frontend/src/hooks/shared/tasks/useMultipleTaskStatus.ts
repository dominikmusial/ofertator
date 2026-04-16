import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { api } from '../../../lib/api'

export interface TaskStatus {
  task_id: string
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: any
  meta?: any
  offer_id?: string
  error?: string
}

export interface TaskInfo {
  task_id: string
  offer_id: string
}

export function useMultipleTaskStatus(tasks: TaskInfo[] = [], enabled: boolean = true) {
  const queryClient = useQueryClient()
  
  const query = useQuery<TaskStatus[]>({
    queryKey: ['multiple-task-status', tasks.map(t => t.task_id)],
    queryFn: async (): Promise<TaskStatus[]> => {
      if (!tasks.length) return []
      
      const statusPromises = tasks.map(async (task) => {
        try {
          const { data } = await api.get<TaskStatus>(`/allegro/offers/task-status/${task.task_id}`)
          return { ...data, task_id: task.task_id, offer_id: task.offer_id }
        } catch (error) {
          return {
            task_id: task.task_id,
            offer_id: task.offer_id,
            status: 'FAILURE' as const,
            result: null,
            meta: { error: 'Failed to fetch task status' }
          }
        }
      })

      return Promise.all(statusPromises)
    },
    enabled: !!tasks.length && enabled,
    refetchInterval: (data) => {
      // Stop polling when all tasks are completed
      if (data && Array.isArray(data) && data.every(task => task.status === 'SUCCESS' || task.status === 'FAILURE')) {
        return false
      }
      return 2000 // Poll every 2 seconds
    }
  })

  // Use useEffect to handle side effects instead of deprecated onSuccess
  useEffect(() => {
    if (query.data && Array.isArray(query.data) && query.data.every(task => task.status === 'SUCCESS' || task.status === 'FAILURE')) {
      queryClient.invalidateQueries({ queryKey: ['offers'] })
    }
  }, [query.data, queryClient])

  return query
} 