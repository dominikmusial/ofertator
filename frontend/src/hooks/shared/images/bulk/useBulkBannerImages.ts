import { useMutation } from '@tanstack/react-query'
import { api } from '../../../../lib/api'

interface BulkBannerImagesRequest {
  accountId: number
  offerIds: string[]
  settings: {
    bannerWidth: number
    bannerHeight: number
    productSize: number
    horizontalPosition: number
    verticalPosition: number
    shape: 'original' | 'circle' | 'square'
    removeBackground: boolean
  }
}

interface BulkBannerImagesResponse {
  task_id: string
}

export const useBulkBannerImages = () => {
  return useMutation<BulkBannerImagesResponse, Error, BulkBannerImagesRequest>({
    mutationFn: async (request) => {
      const payload = {
        account_id: request.accountId,
        offer_ids: request.offerIds,
        settings: {
          width: request.settings.bannerWidth,
          height: request.settings.bannerHeight,
          size_percent: request.settings.productSize,
          horizontal_position_percent: request.settings.horizontalPosition,
          vertical_position_percent: request.settings.verticalPosition,
          shape: request.settings.shape,
          remove_background: request.settings.removeBackground
        }
      }

      const response = await api.post('/allegro/offers/bulk-banner-images', payload)
      return response.data
    }
  })
} 