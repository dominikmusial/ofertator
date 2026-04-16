import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../lib/api'
import { toast } from 'react-hot-toast'

interface ImportError {
  row: number
  offer_id: string
  error: string
}

interface ImportResponse {
  success: boolean
  message: string
  imported_count?: number
  deleted_count?: number
  errors?: ImportError[]
}

export function useImportSchedules(accountId: number) {
  const queryClient = useQueryClient()

  return useMutation<ImportResponse, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await api.post<ImportResponse>(
        `/price-schedules/import/${accountId}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      return data
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message)
        // Invalidate schedules query to refresh the list
        queryClient.invalidateQueries({ queryKey: ['price-schedules', accountId] })
      } else {
        toast.error(data.message)
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas importu pliku'
      toast.error(message)
    }
  })
}
