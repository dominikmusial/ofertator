import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

export const useDeleteTemplate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (templateId: number): Promise<Template> => {
      const response = await api.delete(`/allegro/templates/${templateId}`)
      return response.data
    },
    onSuccess: () => {
      // Invalidate templates queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
} 