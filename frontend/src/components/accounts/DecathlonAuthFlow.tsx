import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'
import { useToastStore } from '../../store/toastStore'

interface Props {
  onSuccess: () => void
  onBack: () => void
}

export default function DecathlonAuthFlow({ onSuccess, onBack }: Props) {
  const [apiKey, setApiKey] = useState('')
  const [shopId, setShopId] = useState('')
  const { addToast } = useToastStore()
  const queryClient = useQueryClient()

  const authMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      formData.append('api_key', apiKey)
      formData.append('shop_id', shopId)
      return api.post('/decathlon/authorize', formData)
    },
    onSuccess: () => {
      addToast('Konto Decathlon dodane pomyślnie', 'success')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      onSuccess()
    },
    onError: (error: any) => {
      addToast(error.response?.data?.detail || 'Błąd podczas dodawania konta Decathlon', 'error')
    }
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-3 mb-4">
        <button onClick={onBack} className="text-gray-400 hover:text-gray-600">
          ← Wstecz
        </button>
        <h2 className="text-xl font-semibold">Dodaj konto Decathlon</h2>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">Autoryzacja API Key (Mirakl)</h3>
        <p className="text-sm text-blue-800">
          Decathlon używa platformy Mirakl. Wprowadź klucz API i Shop ID z panelu Marketplace
          Decathlon.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Shop ID</label>
        <input
          type="text"
          value={shopId}
          onChange={(e) => setShopId(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="np. 12345"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Twój klucz API z Mirakl Decathlon"
        />
      </div>

      <button
        onClick={() => authMutation.mutate()}
        disabled={!apiKey || !shopId || authMutation.isPending}
        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {authMutation.isPending ? 'Dodawanie...' : 'Dodaj konto Decathlon'}
      </button>

      {authMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">
            <span className="font-medium">Błąd:</span>{' '}
            {(authMutation.error as any)?.response?.data?.detail || 'Nieprawidłowy klucz API lub Shop ID'}
          </p>
        </div>
      )}

      <div className="text-xs text-gray-500 bg-gray-50 rounded p-3">
        <p className="font-medium mb-1">Gdzie znaleźć API Key?</p>
        <p>
          1. Zaloguj się do panelu Mirakl Decathlon
          <br />
          2. Przejdź do Settings → API Keys
          <br />
          3. Wygeneruj nowy klucz API dla aplikacji
        </p>
      </div>
    </div>
  )
}
