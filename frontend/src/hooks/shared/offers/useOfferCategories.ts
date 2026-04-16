import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Category {
  id: string
  name: string
  parent?: {
    id: string
    name: string
  }
  leaf: boolean
}

interface CategoriesResponse {
  categories: Category[]
  count: number
}

export function useOfferCategories(accountId?: number) {
  return useQuery<CategoriesResponse>({
    queryKey: ['offer-categories', accountId],
    enabled: !!accountId,
    staleTime: 3600000, // Consider data fresh for 1 hour
    queryFn: async () => {
      const { data } = await api.get<CategoriesResponse>(
        `/allegro/offers/categories/${accountId}`
      )
      return data
    }
  })
}
