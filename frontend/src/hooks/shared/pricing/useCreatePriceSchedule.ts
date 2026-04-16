import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { useToastStore } from '../../../store/toastStore'

interface CreatePriceScheduleData {
  account_id: number;
  offer_id: string;
  offer_name: string;
  scheduled_price: string;
  schedule_config: Record<string, number[]>;
}

export function useCreatePriceSchedule() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (data: CreatePriceScheduleData) => {
      const response = await api.post('/price-schedules/', data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['price-schedules', variables.account_id] })
      addToast('Harmonogram został utworzony', 'success')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas tworzenia harmonogramu'
      addToast(message, 'error')
    },
  })
}
