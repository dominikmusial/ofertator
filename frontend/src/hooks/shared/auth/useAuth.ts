import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '../../../lib/api'
import { useAuthStore } from '../../../store/authStore'
import { useToastStore } from '../../../store/toastStore'

interface LoginData {
  email: string
  password: string
}

interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
}

interface PasswordChangeData {
  current_password: string
  new_password: string
}

export function useLogin() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (data: LoginData) => {
      await login(data.email, data.password)
    },
    onSuccess: () => {
      addToast('Zalogowano pomyślnie!', 'success')
      navigate('/')
    },
    onError: (error: any) => {
      addToast(error.message, 'error')
    }
  })
}

export function useRegister() {
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await api.post('/auth/register', data)
      return response.data
    },
    onSuccess: () => {
      addToast('Konto zostało utworzone! Sprawdź email w celu weryfikacji.', 'success')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd rejestracji'
      addToast(message, 'error')
    }
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout')
    },
    onSuccess: () => {
      logout()
      queryClient.clear()
      addToast('Wylogowano pomyślnie', 'success')
      navigate('/login')
    },
    onError: () => {
      // Even if logout fails on server, clear local state
      logout()
      queryClient.clear()
      navigate('/login')
    }
  })
}

export function useChangePassword() {
  const { addToast } = useToastStore()

  return useMutation({
    mutationFn: async (data: PasswordChangeData) => {
      const response = await api.post('/auth/change-password', data)
      return response.data
    },
    onSuccess: () => {
      addToast('Hasło zostało pomyślnie zmienione!', 'success')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd zmiany hasła'
      addToast(message, 'error')
    }
  })
}

export function useDeleteAccount() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const response = await api.delete('/auth/delete-account')
      return response.data
    },
    onSuccess: () => {
      logout()
      queryClient.clear()
      addToast('Konto zostało pomyślnie usunięte', 'success')
      navigate('/auth/login')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Błąd usuwania konta'
      addToast(message, 'error')
    }
  })
} 