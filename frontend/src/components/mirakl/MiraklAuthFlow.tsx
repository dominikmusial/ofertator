import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'
import { useToastStore } from '../../store/toastStore'
import { MARKETPLACE_CONFIGS } from '../../types/marketplace'

interface Props {
  marketplaceType: 'decathlon' | 'castorama' | 'leroymerlin'
  onSuccess: () => void
  onBack: () => void
}

export default function MiraklAuthFlow({ marketplaceType, onSuccess, onBack }: Props) {
  const [apiKey, setApiKey] = useState('')
  const [shopId, setShopId] = useState('')
  const { addToast } = useToastStore()
  const queryClient = useQueryClient()

  const marketplaceConfig = MARKETPLACE_CONFIGS[marketplaceType]

  const authMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      formData.append('api_key', apiKey)
      formData.append('shop_id', shopId)
      return api.post(`/${marketplaceType}/authorize`, formData)
    },
    onSuccess: () => {
      addToast(`Konto ${marketplaceConfig.name} dodane pomyślnie`, 'success')
      // Invalidate all account-related queries (including user-specific keys)
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['shared-accounts'] })  // Matches all ['shared-accounts', ...] variations
      onSuccess()
    },
    onError: (error: any) => {
      addToast(
        error.response?.data?.detail || `Błąd podczas dodawania konta ${marketplaceConfig.name}`,
        'error'
      )
    }
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-3 mb-4">
        <button onClick={onBack} className="text-gray-400 hover:text-gray-600">
          ← Wstecz
        </button>
        <h2 className="text-xl font-semibold flex items-center space-x-2">
          <span>{marketplaceConfig.icon}</span>
          <span>Dodaj konto {marketplaceConfig.name}</span>
        </h2>
      </div>

      <div 
        className="border rounded-lg p-4"
        style={{ 
          backgroundColor: `${marketplaceConfig.color}10`, 
          borderColor: `${marketplaceConfig.color}40` 
        }}
      >
        <h3 className="font-medium mb-2" style={{ color: marketplaceConfig.color }}>
          Autoryzacja API Key (Mirakl)
        </h3>
        <p className="text-sm text-gray-700">
          {marketplaceConfig.name} używa platformy Mirakl. Wprowadź klucz API z panelu 
          Marketplace {marketplaceConfig.name}. Shop ID zostanie pobrany automatycznie.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:border-transparent"
          style={{ 
            '--tw-ring-color': marketplaceConfig.color 
          } as React.CSSProperties}
          placeholder={`Twój klucz API z Mirakl ${marketplaceConfig.name}`}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Shop ID <span className="text-gray-400 text-xs font-normal">(opcjonalne)</span>
        </label>
        <input
          type="text"
          value={shopId}
          onChange={(e) => setShopId(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:border-transparent"
          style={{ 
            '--tw-ring-color': marketplaceConfig.color 
          } as React.CSSProperties}
          placeholder="Zostanie pobrane automatycznie"
        />
        <p className="text-xs text-gray-500 mt-1">
          Pozostaw puste - Shop ID zostanie automatycznie pobrane z API
        </p>
      </div>

      <button
        onClick={() => authMutation.mutate()}
        disabled={!apiKey || authMutation.isPending}
        className="w-full text-white py-3 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        style={{ backgroundColor: marketplaceConfig.color }}
      >
        {authMutation.isPending ? 'Dodawanie...' : `Dodaj konto ${marketplaceConfig.name}`}
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
          1. Zaloguj się do panelu Mirakl {marketplaceConfig.name}
          <br />
          2. Przejdź do Settings → API Keys
          <br />
          3. Wygeneruj nowy klucz API dla aplikacji
          <br />
          <span className="text-gray-600 italic mt-1 block">
            💡 Shop ID zostanie pobrany automatycznie z Twojego konta
          </span>
        </p>
      </div>
    </div>
  )
}
