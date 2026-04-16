import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../../lib/api'

interface AIProvider {
  id: string;
  name: string;
}

interface AIProviderInfo {
  providers: Record<string, AIProvider[]>;
  default_provider: string;
  default_model: string;
}

interface AIConfigStatus {
  has_config: boolean;
  is_active: boolean;
  provider?: string;
  model?: string;
  last_validated?: string;
  can_use_default: boolean;
}

interface AIConfigResponse {
  id: number;
  ai_provider: string;
  model_name: string;
  is_active: boolean;
  last_validated_at?: string;
  created_at: string;
  updated_at?: string;
}

interface TestAPIKeyRequest {
  provider: string;
  model_name: string;
  api_key: string;
}

interface TestAPIKeyResponse {
  is_valid: boolean;
  error_message?: string;
}

interface CreateAIConfigRequest {
  ai_provider: string;
  model_name: string;
  api_key: string;
}

interface UpdateAIConfigRequest {
  ai_provider?: string;
  model_name?: string;
  api_key?: string;
  is_active?: boolean;
}

// Query hooks
export const useAIProviders = () => {
  return useQuery<AIProviderInfo>({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const response = await api.get('/ai-config/providers')
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - providers rarely change
    refetchOnWindowFocus: false
  })
}

export const useAIConfigStatus = () => {
  return useQuery<AIConfigStatus>({
    queryKey: ['ai-config-status'],
    queryFn: async () => {
      const response = await api.get('/ai-config/status')
      return response.data
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: false
  })
}

export const useAIConfig = () => {
  return useQuery<AIConfigResponse>({
    queryKey: ['ai-config'],
    queryFn: async () => {
      try {
        const response = await api.get('/ai-config/config')
        return response.data
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null
        }
        throw error
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: false
  })
}

// Mutation hooks
export const useTestAPIKey = () => {
  return useMutation<TestAPIKeyResponse, Error, TestAPIKeyRequest>({
    mutationFn: async (data) => {
      const response = await api.post('/ai-config/test-key', data)
      return response.data
    }
  })
}

export const useCreateAIConfig = () => {
  const queryClient = useQueryClient()
  
  return useMutation<AIConfigResponse, Error, CreateAIConfigRequest>({
    mutationFn: async (data) => {
      try {
        const response = await api.post('/ai-config/config', data)
        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.detail || 'Failed to create AI config')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] })
      queryClient.invalidateQueries({ queryKey: ['ai-config-status'] })
    }
  })
}

export const useUpdateAIConfig = () => {
  const queryClient = useQueryClient()
  
  return useMutation<AIConfigResponse, Error, UpdateAIConfigRequest>({
    mutationFn: async (data) => {
      try {
        const response = await api.put('/ai-config/config', data)
        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.detail || 'Failed to update AI config')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] })
      queryClient.invalidateQueries({ queryKey: ['ai-config-status'] })
    }
  })
}

export const useDeleteAIConfig = () => {
  const queryClient = useQueryClient()
  
  return useMutation<{ message: string }, Error>({
    mutationFn: async () => {
      const response = await api.delete('/ai-config/config')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] })
      queryClient.invalidateQueries({ queryKey: ['ai-config-status'] })
    }
  })
} 