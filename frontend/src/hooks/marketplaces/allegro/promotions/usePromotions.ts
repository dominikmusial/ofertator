import { useQuery } from '@tanstack/react-query'
import { api } from '../../../../lib/api'

export interface Promotion {
  id: string
  name: string
  status: string
  type: string
  discount: number
  for_each_quantity: number
  discounted_number: number
  valid_from: string
  valid_until: string
  offers: string[]
}

export function usePromotions(accountId?: number) {
  return useQuery({
    queryKey: ['promotions', accountId],
    queryFn: async () => {
      if (!accountId) return []
      const response = await api.get(`/allegro/promotions/bundles?account_id=${accountId}`)
      return response.data as Promotion[]
    },
    enabled: !!accountId
  })
} 