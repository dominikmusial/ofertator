import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Account {
  id: number
  nazwa_konta: string
  marketplace_type?: string
  needs_reauth?: boolean
}

export function useAccounts() {
  return useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const { data } = await api.get<Account[]>('/accounts/')
      return data
    }
  })
} 