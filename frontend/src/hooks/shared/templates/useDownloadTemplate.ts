import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'
import { toast } from 'react-hot-toast'

interface DownloadTemplateParams {
  accountId: number
  format: 'xlsx' | 'csv'
}

export function useDownloadTemplate() {
  return useMutation({
    mutationFn: async ({ accountId, format }: DownloadTemplateParams) => {
      const response = await api.get(
        `/price-schedules/template/${accountId}`,
        {
          params: { format },
          responseType: 'blob'
        }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `szablon_harmonogram_cen.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      return response.data
    },
    onSuccess: () => {
      toast.success('Szablon został pobrany')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd podczas pobierania szablonu'
      toast.error(message)
    }
  })
}
