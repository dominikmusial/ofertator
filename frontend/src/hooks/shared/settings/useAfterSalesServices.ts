import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Warranty {
  id: string
  name: string
  // Add other relevant fields from the API response
}

export interface ReturnPolicy {
  id: string
  name: string
  // Add other relevant fields from the API response
}

export interface AfterSalesServices {
  warranties?: Warranty[]
  returns?: ReturnPolicy[]
  // The actual response might have different structure
  [key: string]: any
}

export function useAfterSalesServices(accountId: number) {
  return useQuery<AfterSalesServices>({
    queryKey: ['after-sales-services', accountId],
    queryFn: async () => {
      const { data } = await api.get<AfterSalesServices>(`/allegro/offers/account-settings/${accountId}/after-sales-services`)
      return data
    },
    enabled: !!accountId
  })
} 