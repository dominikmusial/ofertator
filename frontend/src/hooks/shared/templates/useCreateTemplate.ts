import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

interface CreateTemplateRequest {
  name: string
  content: any
  prompt?: string
  account_id: number
}

export const useCreateTemplate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (request: CreateTemplateRequest): Promise<Template> => {
      const { account_id, ...templateData } = request
      const response = await api.post('/allegro/templates', templateData, { 
        params: { account_id } 
      })
      return response.data
    },
    onSuccess: () => {
      // Invalidate all templates queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
} 