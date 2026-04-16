import { useMutation } from '@tanstack/react-query'
import api from '../../../lib/api'
import { useToastStore } from '../../../store/toastStore'

interface DuplicateItem {
  offer_id: string
  new_title: string
}

interface DuplicatePayload {
  account_id: number
  items: DuplicateItem[]
  activate_immediately: boolean
}

export function useDuplicateOffers() {
  const addToast = useToastStore(s => s.addToast)

  return useMutation({
    mutationFn: (payload: DuplicatePayload) => 
      api.post('/allegro/offers/duplicate-offers-with-titles', payload),
    onSuccess: () => {
      addToast('Duplikacja została uruchomiona', 'success')
    },
    onError: () => {
      addToast('Nie udało się uruchomić duplikacji', 'error')
    }
  })
}

