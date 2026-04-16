import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface DeliveryMethod {
  id: string
  name: string
  // Add other relevant fields from the API response
}

export interface DeliverySettings {
  // Structure based on Allegro API response - could be various formats
  deliveryMethods?: DeliveryMethod[]
  // The actual response might have different structure
  [key: string]: any
}

export function useDeliverySettings(accountId: number) {
  return useQuery<DeliverySettings>({
    queryKey: ['delivery-settings', accountId],
    queryFn: async () => {
      const { data } = await api.get<DeliverySettings>(`/allegro/offers/account-settings/${accountId}/delivery`)
      return data
    },
    enabled: !!accountId
  })
} 