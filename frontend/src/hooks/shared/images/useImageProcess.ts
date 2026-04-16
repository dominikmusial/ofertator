import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'

export type ImageOperation = 'remove_background' | 'crop_to_square' | 'add_blur_effect'

interface ProcessImageRequest {
  image_url: string
  operations: ImageOperation[]
}

interface ProcessImageResponse {
  url: string
}

export const useImageProcess = () => {
  return useMutation({
    mutationFn: async (request: ProcessImageRequest): Promise<ProcessImageResponse> => {
      const response = await api.post('/allegro/images/process', request)
      return response.data
    }
  })
} 