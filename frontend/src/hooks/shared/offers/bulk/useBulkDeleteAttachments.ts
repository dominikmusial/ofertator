import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkDeleteAttachmentsRequest {
  account_id: number
  offer_ids: string[]
}

interface TaskResponse {
  task_id: string
}

export function useBulkDeleteAttachments() {
  return useMutation<TaskResponse, Error, BulkDeleteAttachmentsRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post<TaskResponse>('/allegro/offers/bulk-delete-attachments', request)
      return data
    },
  })
} 