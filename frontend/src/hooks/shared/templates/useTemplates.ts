import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

export const useTemplates = (accountId: number | undefined) => {
  return useQuery({
    queryKey: ['templates', accountId],
    queryFn: async () => {
      if (!accountId) return []
      const response = await api.get('/allegro/templates', { 
        params: { account_id: accountId } 
      })
      return response.data as Template[]
    },
    enabled: !!accountId, // Only run query if accountId is provided
    staleTime: 60000, // Cache for 1 minute
    refetchOnWindowFocus: false
  })
} 