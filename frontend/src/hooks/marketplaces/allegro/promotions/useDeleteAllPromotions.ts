import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../../lib/api'
import { useToastStore } from '../../../../store/toastStore'

interface DeleteAllPromotionsRequest {
  account_id: number
}

export function useDeleteAllPromotions() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (request: DeleteAllPromotionsRequest) => {
      const response = await api.delete(`/allegro/promotions/bundles/all?account_id=${request.account_id}`)
      return response.data
    },
    onSuccess: (data, variables) => {
      const deletedCount = data?.deleted_count || 0
      const failedCount = data?.failed_count || 0
      
      if (deletedCount > 0) {
        if (failedCount > 0) {
          addToast(`Usunięto ${deletedCount} rabatów. ${failedCount} nie udało się usunąć`, 'info')
        } else {
          addToast(`Pomyślnie usunięto wszystkie rabaty (${deletedCount})`, 'success')
        }
      } else if (failedCount > 0) {
        addToast(`Nie udało się usunąć żadnego z ${failedCount} rabatów`, 'error')
      } else {
        addToast('Brak rabatów do usunięcia', 'info')
      }
      
      // Invalidate promotions queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['promotions', variables.account_id] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas usuwania promocji'
      addToast(message, 'error')
    }
  })
} 