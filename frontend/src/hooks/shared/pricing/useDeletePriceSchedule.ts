import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { useToastStore } from '../../../store/toastStore'

interface DeletePriceScheduleData {
  schedule_id: number;
  restore_original: boolean;
}

export function useDeletePriceSchedule() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async ({ schedule_id, restore_original }: DeletePriceScheduleData) => {
      const response = await api.delete(`/price-schedules/${schedule_id}`, {
        params: { restore_original }
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-schedules'] })
      addToast('Harmonogram został usunięty', 'success')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas usuwania harmonogramu'
      addToast(message, 'error')
    },
  })
}
