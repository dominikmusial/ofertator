import { useQuery } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface Image {
  id: string
  url: string
  filename: string
  size: number
  upload_date: string
  content_type: string
}

export const useImages = (search?: string) => {
  return useQuery({
    queryKey: ['images', search],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      
      const queryString = params.toString()
      const url = queryString ? `/images?${queryString}` : '/images'
      
      const response = await api.get(url)
      return response.data as Image[]
    },
    staleTime: 30000, // Cache for 30 seconds
    refetchOnWindowFocus: false
  })
} 