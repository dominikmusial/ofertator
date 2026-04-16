import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkRestoreAttachmentsRequest {
  account_id: number
  offer_ids: string[]
  original_attachments: any
}

interface TaskResponse {
  task_id: string
}

export function useBulkRestoreAttachments() {
  return useMutation<TaskResponse, Error, BulkRestoreAttachmentsRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post<TaskResponse>('/allegro/offers/bulk-restore-attachments', request)
      return data
    },
  })
} 