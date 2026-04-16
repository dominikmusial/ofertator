import { useMutation } from '@tanstack/react-query'
import { api } from '../../../../lib/api'

interface RestoreBannersRequest {
  accountId: number
  offerIds: string[]
}

interface RestoreBannersResponse {
  task_id: string
}

export const useRestoreBanners = () => {
  return useMutation<RestoreBannersResponse, Error, RestoreBannersRequest>({
    mutationFn: async (request) => {
      const payload = {
        account_id: request.accountId,
        offer_ids: request.offerIds
      }

      const response = await api.post('/allegro/offers/bulk-restore-banners', payload)
      return response.data
    }
  })
} 