import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkGenerateProductCardsRequest {
  account_id: number
  offer_ids: string[]
  strip_html?: boolean
}

interface TaskResponse {
  task_id: string
}

export function useBulkGenerateProductCards() {
  return useMutation<TaskResponse, Error, BulkGenerateProductCardsRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post<TaskResponse>('/allegro/offers/bulk-generate-product-cards', request)
      return data
    },
  })
} 