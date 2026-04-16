import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'

interface UploadResponse {
  url: string
}

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB in bytes

export const useImageUpload = () => {
  return useMutation({
    mutationFn: async (file: File): Promise<UploadResponse> => {
      // Validate file size before upload
      if (file.size > MAX_FILE_SIZE) {
        throw new Error(`Plik jest za duży. Maksymalny rozmiar to ${Math.round(MAX_FILE_SIZE / (1024 * 1024))}MB, a wybrany plik ma ${(file.size / (1024 * 1024)).toFixed(1)}MB.`)
      }

      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/allegro/images/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      return response.data
    }
  })
} 