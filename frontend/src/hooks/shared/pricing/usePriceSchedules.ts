import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface PriceSchedule {
  id: number;
  account_id: number;
  offer_id: string;
  offer_name: string;
  original_price: string;
  scheduled_price: string;
  schedule_config: Record<string, number[]>;
  is_active: boolean;
  current_price_state: string;
  last_price_check: string | null;
  last_price_update: string | null;
  created_at: string;
  updated_at: string | null;
}

interface PriceSchedulesResponse {
  schedules: PriceSchedule[];
  count: number;
}

export function usePriceSchedules(accountId?: number) {
  return useQuery<PriceSchedulesResponse>({
    queryKey: ['price-schedules', accountId],
    queryFn: async () => {
      const { data } = await api.get<PriceSchedulesResponse>(`/price-schedules/${accountId}`)
      return data
    },
    enabled: !!accountId,
  })
}
