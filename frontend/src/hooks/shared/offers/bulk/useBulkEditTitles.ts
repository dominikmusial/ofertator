import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'
import { useToastStore } from '../../../../store/toastStore'

interface Item {
  offer_id: string
  title: string
}

interface Payload {
  account_id: number
  items: Item[]
}

export function useBulkEditTitles() {
  const addToast = useToastStore(s => s.addToast)

  return useMutation({
    mutationFn: (payload: Payload) => api.post('/allegro/offers/bulk-edit-titles', payload),
    onSuccess: () => {
      addToast('Zadanie edycji tytułów zostało uruchomione', 'success')
    },
    onError: () => {
      addToast('Nie udało się uruchomić zmiany tytułów', 'error')
    }
  })
} 