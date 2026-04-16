import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import api from '../../../../lib/api'

interface Response {
  task_id: string
  status: string
  result: any
}

export function useAuthStatus(taskId?: string) {
  const queryClient = useQueryClient()
  const query = useQuery<Response>({
    queryKey: ['auth-status', taskId],
    queryFn: async () => {
      const { data } = await api.get<Response>(`/allegro/auth/status/${taskId}`)
      return data
    },
    enabled: !!taskId,
    refetchInterval: 3000
  })

  // Invalidate account queries when auth succeeds
  useEffect(() => {
    if (query.data?.status === 'SUCCESS') {
      // Invalidate all account-related queries (including user-specific keys)
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['shared-accounts'] })  // Matches all ['shared-accounts', ...] variations
    }
  }, [query.data?.status, queryClient])

  return query
} 