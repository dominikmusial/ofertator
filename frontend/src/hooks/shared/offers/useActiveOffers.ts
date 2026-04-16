import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

interface Offer {
  id: string;
  name: string;
  price: string;
  category?: string;
}

interface ActiveOffersResponse {
  offers: Offer[];
  count: number;
}

export function useActiveOffers(accountId?: number) {
  return useQuery<ActiveOffersResponse>({
    queryKey: ['active-offers', accountId],
    queryFn: async () => {
      const { data } = await api.get<ActiveOffersResponse>(`/allegro/offers/active/${accountId}`)
      return data
    },
    enabled: !!accountId,
  })
}
