import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface Response {
  user_code: string
  verification_uri: string
  task_id: string
}

export function useAuthorizeAccount() {
  return useMutation<Response, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post<Response>('/allegro/auth/start')
      return data
    }
  })
} 