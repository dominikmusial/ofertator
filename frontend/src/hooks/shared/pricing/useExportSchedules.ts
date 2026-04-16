import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'
import { toast } from 'react-hot-toast'

interface ExportSchedulesParams {
  accountId: number
  format: 'xlsx' | 'csv'
}

export function useExportSchedules() {
  return useMutation({
    mutationFn: async ({ accountId, format }: ExportSchedulesParams) => {
      const response = await api.get(
        `/price-schedules/export/${accountId}`,
        {
          params: { format },
          responseType: 'blob'
        }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `harmonogram_cen_export_${accountId}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      return response.data
    },
    onSuccess: () => {
      toast.success('Harmonogramy zostały wyeksportowane')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas eksportowania harmonogramów'
      toast.error(message)
    }
  })
}
