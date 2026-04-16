import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../../lib/api'
import { useToastStore } from '../../../../store/toastStore'

interface DeletePromotionRequest {
  account_id: number
  promotion_id: string
}

export function useDeletePromotion() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (request: DeletePromotionRequest) => {
      const response = await api.delete(`/allegro/promotions/bundles/${request.promotion_id}?account_id=${request.account_id}`)
      return response.data
    },
    onSuccess: (data, variables) => {
      // Invalidate promotions queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['promotions', variables.account_id] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas usuwania promocji'
      addToast(message, 'error')
    }
  })
} 