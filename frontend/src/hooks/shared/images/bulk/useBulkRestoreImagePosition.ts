import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkRestoreImagePositionParams {
  accountId: number
  offerIds: string[]
  imagePosition: number
}

interface TaskResponse {
  task_id: string
}

export const useBulkRestoreImagePosition = () => {
  return useMutation({
    mutationFn: async ({
      accountId,
      offerIds,
      imagePosition
    }: BulkRestoreImagePositionParams): Promise<TaskResponse> => {
      const response = await api.post('/allegro/offers/bulk-restore-image-position', {
        account_id: accountId,
        offer_ids: offerIds,
        image_position: imagePosition
      })
      
      return response.data
    }
  })
} 