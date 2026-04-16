import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../../lib/api'
import { useToastStore } from '../../../../store/toastStore'

interface BulkStatusChangeRequest {
  account_id: number
  offer_ids: string[]
  status: 'ACTIVE' | 'ENDED'
}

interface TaskResponse {
  task_id: string
  offer_id: string
}

export function useBulkChangeStatus() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation<TaskResponse[], Error, BulkStatusChangeRequest>({
    mutationFn: async (request: BulkStatusChangeRequest) => {
      const response = await api.post('/allegro/offers/bulk-change-status', request)
      return response.data
    },
    onSuccess: (data, variables) => {
      const action = variables.status === 'ENDED' ? 'zakańczania' : 'przywracania'
      addToast(`Zadanie ${action} ofert zostało uruchomione`, 'success')
      queryClient.invalidateQueries({ queryKey: ['offers'] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas zmiany statusu ofert'
      addToast(message, 'error')
    }
  })
} 