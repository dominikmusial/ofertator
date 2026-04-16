import { useMutation } from '@tanstack/react-query'
import { api } from '../../../../lib/api'
import { useToastStore } from '../../../../store/toastStore'

interface PullTitlesRequest {
  account_id: number
  offer_ids: string[]
}

interface PullTitlesResponse {
  task_id: string
}

export const usePullTitles = () => {
  const { addToast } = useToastStore()

  return useMutation<PullTitlesResponse, Error, PullTitlesRequest>({
    mutationFn: async (request) => {
      const response = await api.post(`/allegro/offers/pull-titles?account_id=${request.account_id}`, request.offer_ids)
      return response.data
    },
    onSuccess: (data) => {
      addToast('Rozpoczęto pobieranie tytułów', 'success')
    },
    onError: (error) => {
      addToast(`Błąd pobierania tytułów: ${error.message}`, 'error')
    }
  })
} 