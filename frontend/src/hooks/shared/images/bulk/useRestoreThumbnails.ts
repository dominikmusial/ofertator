import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface RestoreThumbnailsParams {
  accountId: number
  offerIds: string[]
}

interface TaskResponse {
  task_id: string
  offer_id: string
}

export const useRestoreThumbnails = () => {
  return useMutation({
    mutationFn: async ({ accountId, offerIds }: RestoreThumbnailsParams): Promise<TaskResponse[]> => {
      const response = await api.post(`/allegro/offers/restore-thumbnails?account_id=${accountId}`, offerIds)
      return response.data
    }
  })
} 