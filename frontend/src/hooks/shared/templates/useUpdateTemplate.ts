import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

interface UpdateTemplateRequest {
  id: number
  name: string
  content: any
}

export const useUpdateTemplate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, ...request }: UpdateTemplateRequest): Promise<Template> => {
      const response = await api.put(`/allegro/templates/${id}`, request)
      return response.data
    },
    onSuccess: (data) => {
      // Invalidate templates queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
} 