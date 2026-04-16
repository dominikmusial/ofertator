import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'

interface UploadCustomAttachmentRequest {
  account_id: number
  offer_ids: string[]
  attachment_type: string
  file: File
}

interface TaskResponse {
  task_id: string
}

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB in bytes

export function useUploadCustomAttachment() {
  return useMutation<TaskResponse, Error, UploadCustomAttachmentRequest>({
    mutationFn: async (request) => {
      // Validate file size before upload
      if (request.file.size > MAX_FILE_SIZE) {
        throw new Error(`Plik jest za duży. Maksymalny rozmiar to ${Math.round(MAX_FILE_SIZE / (1024 * 1024))}MB, a wybrany plik ma ${(request.file.size / (1024 * 1024)).toFixed(1)}MB.`);
      }

      const formData = new FormData()
      formData.append('account_id', request.account_id.toString())
      formData.append('offer_ids', JSON.stringify(request.offer_ids))
      formData.append('attachment_type', request.attachment_type)
      formData.append('file', request.file)

      const { data } = await api.post<TaskResponse>('/allegro/offers/upload-custom-attachment', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return data
    },
  })
} 