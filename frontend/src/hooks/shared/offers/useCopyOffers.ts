import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../lib/api'
import { useToastStore } from '../../../store/toastStore'

interface CopyOfferOptions {
  target_account_id: number
  copy_images: boolean
  copy_description: boolean
  copy_parameters: boolean
  copy_shipping: boolean
  copy_return_policy: boolean
  copy_warranty: boolean
  copy_price: boolean
  copy_quantity: boolean
}

interface CopyOfferRequest {
  source_account_id: number
  source_offer_id: string
  options: CopyOfferOptions
}

interface BulkCopyRequest {
  requests: CopyOfferRequest[]
}

interface TaskResponse {
  task_id: string
  offer_id: string
}

export function useCopyOffers() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation<TaskResponse[], Error, BulkCopyRequest>({
    mutationFn: async (request: BulkCopyRequest) => {
      const response = await api.post('/allegro/offers/copy', request)
      return response.data
    },
    onSuccess: (data) => {
      addToast('Zadanie kopiowania ofert zostało uruchomione', 'success')
      // Invalidate offers queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['offers'] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas kopiowania ofert'
      addToast(message, 'error')
    }
  })
} 