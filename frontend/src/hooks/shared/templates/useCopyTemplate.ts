import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { Template } from '../../../types/template'

interface CopyTemplateRequest {
  template_id: number
  target_account_id: number
}

export const useCopyTemplate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (request: CopyTemplateRequest): Promise<Template> => {
      const response = await api.post('/allegro/templates/copy', request)
      return response.data
    },
    onSuccess: () => {
      // Invalidate templates queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
} 