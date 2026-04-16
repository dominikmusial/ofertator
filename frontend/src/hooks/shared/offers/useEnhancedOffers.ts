import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Offer {
  id: string
  name: string
  title: string // Keep for backward compatibility
  price: string
  quantity: number
  status: string
  category_id?: string
  image_url?: string
}

interface EnhancedFilters {
  search?: string
  status?: string
  page?: number
  pageSize?: number
  price_from?: number
  price_to?: number
  category_id?: string
  offer_ids?: string
}

interface EnhancedOffersResponse {
  items: Offer[]
  total: number
}

export function useEnhancedOffers(accountId?: number, filters: EnhancedFilters = {}) {
  return useQuery<EnhancedOffersResponse>({
    queryKey: ['enhanced-offers', accountId, filters],
    enabled: !!accountId,
    staleTime: 30000, // Consider data fresh for 30 seconds
    cacheTime: 300000, // Keep in cache for 5 minutes
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('account_id', String(accountId))
      
      // Add all filter parameters
      if (filters.search) params.set('search', filters.search)
      if (filters.status && filters.status !== 'ALL') params.set('status', filters.status)
      if (filters.page) params.set('offset', String((filters.page - 1) * (filters.pageSize || 25)))
      if (filters.pageSize) params.set('limit', String(filters.pageSize))
      if (filters.price_from !== undefined) params.set('price_from', String(filters.price_from))
      if (filters.price_to !== undefined) params.set('price_to', String(filters.price_to))
      if (filters.category_id) params.set('category_id', filters.category_id)
      if (filters.offer_ids) params.set('offer_ids', filters.offer_ids)
      
      const { data } = await api.get<EnhancedOffersResponse>(`/allegro/offers/?${params.toString()}`)
      return data
    }
  })
}
