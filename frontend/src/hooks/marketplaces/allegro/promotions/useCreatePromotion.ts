import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../../lib/api'

interface CreatePromotionData {
  account_id: number
  offer_ids: string[]
  for_each_quantity: number
  percentage: number
  group_size: number
}

interface CreatePromotionResponse {
  success_count: number
  total_groups: number
  results: boolean[]
}

export function useCreatePromotion() {
  const queryClient = useQueryClient()

  return useMutation<CreatePromotionResponse, Error, CreatePromotionData>({
    mutationFn: async (data: CreatePromotionData) => {
      const response = await api.post('/allegro/promotions/bundles/grouped', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions'] })
    }
    // Removed onSuccess and onError handlers - let the component handle the response
  })
} 