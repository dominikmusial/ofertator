import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkCompositeImageReplaceParams {
  accountId: number
  offerIds: string[]
  imagePosition: number
  overlayImageUrl: string
}

interface TaskResponse {
  task_id: string
}

export const useBulkCompositeImageReplace = () => {
  return useMutation({
    mutationFn: async ({
      accountId,
      offerIds,
      imagePosition,
      overlayImageUrl
    }: BulkCompositeImageReplaceParams): Promise<TaskResponse> => {
      const response = await api.post('/allegro/offers/bulk-composite-image-replace', {
        account_id: accountId,
        offer_ids: offerIds,
        image_position: imagePosition,
        overlay_image_url: overlayImageUrl
      })
      
      return response.data
    }
  })
} 