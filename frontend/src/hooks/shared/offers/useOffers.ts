import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Offer {
  id: string
  title: string
  price: string
  quantity: number
  status: string
}

interface Filters {
  search?: string
  status?: string
  page?: number
  pageSize?: number
}

export function useOffers(accountId?: number, filters: Filters = {}) {
  return useQuery<{ items: Offer[]; total: number }>({
    queryKey: ['offers', accountId, filters],
    enabled: !!accountId,
    staleTime: 30000, // Consider data fresh for 30 seconds
    cacheTime: 300000, // Keep in cache for 5 minutes
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('account_id', String(accountId))
      if (filters.search) params.set('search', filters.search)
      if (filters.status && filters.status !== 'ALL') params.set('status', filters.status)
      if (filters.page) params.set('page', String(filters.page))
      if (filters.pageSize) params.set('page_size', String(filters.pageSize))
      const { data } = await api.get<{ items: Offer[]; total: number }>(`/allegro/offers/?${params.toString()}`)
      return data
    }
  })
} 