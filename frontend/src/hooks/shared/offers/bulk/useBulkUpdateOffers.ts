import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface TemplateProcessingOptions {
  mode: string
  frame_scale: number
  generate_pdf: boolean
  auto_fill_images: boolean
  save_original_images: boolean
  save_processed_images: boolean
  save_images_only: boolean
  save_location?: string
  custom_path?: string
}

interface TemplateSection {
  // Support both formats: backend format (items) and frontend format (type + values)
  items?: Array<{
    type: string
    content?: string
    url?: string
  }>
  type?: string
  values?: Record<string, any>
  id?: string
}

interface TemplateContent {
  prompt: string
  sections: TemplateSection[]
}

interface BulkUpdateOffersRequest {
  account_id: number
  offer_ids: string[]
  template: TemplateContent
  options: TemplateProcessingOptions
}

interface TaskResponse {
  task_id: string
  offer_id: string
}

export const useBulkUpdateOffers = () => {
  return useMutation({
    mutationFn: async (request: BulkUpdateOffersRequest): Promise<TaskResponse> => {
      const response = await api.post('/allegro/offers/bulk-update-with-template', request)
      return response.data
    }
  })
}

export const useBulkRestoreOffers = () => {
  return useMutation({
    mutationFn: async ({ account_id, offer_ids }: { account_id: number; offer_ids: string[] }): Promise<TaskResponse[]> => {
      const response = await api.post('/allegro/offers/bulk-restore', offer_ids, {
        params: { account_id }
      })
      return response.data
    }
  })
} 