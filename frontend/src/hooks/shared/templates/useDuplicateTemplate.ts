import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

interface DuplicateTemplateRequest {
  template_id: number
  new_name: string
}

export const useDuplicateTemplate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (request: DuplicateTemplateRequest): Promise<Template> => {
      const response = await api.post('/allegro/templates/duplicate', request)
      return response.data
    },
    onSuccess: () => {
      // Invalidate templates queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
}
