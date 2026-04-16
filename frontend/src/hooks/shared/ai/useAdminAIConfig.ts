import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'

export interface AIPromptConfig {
  prompt: string
  temperature: number
  max_output_tokens: number
  top_p: number
  top_k: number | null
  stop_sequences: string[]
}

export interface AdminAIConfigResponse {
  titles: {
    anthropic: AIPromptConfig
    gemini: AIPromptConfig
  }
}

export const useAdminAIConfig = () => {
  return useQuery<AdminAIConfigResponse>({
    queryKey: ['admin-ai-config'],
    queryFn: async () => {
      const response = await api.get('/admin/ai-config')
      return response.data
    },
  })
}

export const useUpdateAdminAIConfig = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({
      provider,
      config,
    }: {
      provider: 'anthropic' | 'gemini'
      config: Partial<AIPromptConfig>
    }) => {
      const response = await api.put(`/admin/ai-config/titles/${provider}`, config)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-ai-config'] })
    },
  })
}

