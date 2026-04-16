import { useState } from 'react'
import { AlertTriangle, Settings, Loader2 } from 'lucide-react'
import { useAdminAIConfig, useUpdateAdminAIConfig } from '../../hooks/shared/ai'
import { useToastStore } from '../../store/toastStore'
import AIConfigForm from '../../components/admin/AIConfigForm'

type Provider = 'anthropic' | 'gemini'

export default function AdminAIPrompts() {
  const [selectedProvider, setSelectedProvider] = useState<Provider>('anthropic')

  const { data: config, isLoading, error } = useAdminAIConfig()
  const updateConfigMutation = useUpdateAdminAIConfig()
  const { addToast } = useToastStore()

  const handleSave = async (updatedConfig: any) => {
    try {
      await updateConfigMutation.mutateAsync({
        provider: selectedProvider,
        config: updatedConfig,
      })
      addToast('Konfiguracja zapisana pomyślnie', 'success')
    } catch (error: any) {
      addToast(
        error?.response?.data?.detail || 'Nie udało się zapisać konfiguracji',
        'error'
      )
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Ładowanie konfiguracji AI...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-red-800 font-medium">Nie udało się załadować konfiguracji</h3>
              <p className="text-red-700 text-sm mt-1">
                {(error as any)?.response?.data?.detail || 'Wystąpił błąd podczas ładowania konfiguracji.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!config) {
    return null
  }

  const currentConfig = config.titles[selectedProvider]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <Settings className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Konfiguracja AI - Optymalizacja Tytułów</h1>
        </div>
        <p className="text-gray-600">
          Konfiguruj prompty AI i parametry dla optymalizacji tytułów ofert.
          Te ustawienia będą używane w całej aplikacji.
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-blue-800 font-medium">Ważne informacje</h3>
            <ul className="text-blue-700 text-sm mt-2 space-y-1 list-disc list-inside">
              <li>Zmiany wpłyną na wszystkich użytkowników natychmiast po zapisaniu</li>
              <li>Upewnij się, że zmiany zostały przetestowane przed wdrożeniem</li>
              <li>Parametry muszą spełniać ograniczenia specyficzne dla providera (zakresy temperatury, limity tokenów, itp.)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Provider Tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b border-gray-200 bg-gray-50">
          <nav className="flex -mb-px px-6">
            <button
              onClick={() => setSelectedProvider('anthropic')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                selectedProvider === 'anthropic'
                  ? 'border-purple-600 text-purple-600 bg-white'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Anthropic (Claude)
            </button>
            <button
              onClick={() => setSelectedProvider('gemini')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                selectedProvider === 'gemini'
                  ? 'border-green-600 text-green-600 bg-white'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Google Gemini
            </button>
          </nav>
        </div>

        {/* Configuration Form */}
        <div className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Optymalizacja Tytułów -{' '}
                {selectedProvider === 'anthropic' ? 'Anthropic Claude' : 'Google Gemini'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Skonfiguruj sposób optymalizacji tytułów produktów przez AI dla lepszej widoczności i zaangażowania.
              </p>
            </div>
          </div>

          {currentConfig && (
            <AIConfigForm
              provider={selectedProvider}
              config={currentConfig}
              onSave={handleSave}
              isSaving={updateConfigMutation.isPending}
            />
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Wytyczne parametrów</h3>
        
        <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>💡 Jak wyłączyć parametr:</strong> Użyj checkboxa obok nazwy parametru. 
            Gdy checkbox jest odznaczony, parametr nie jest wysyłany do API (wartość = null).
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <h4 className="font-medium text-gray-900">Temperature (opcjonalne)</h4>
            <ul className="mt-1 space-y-1 list-disc list-inside">
              <li>Anthropic: 0.0 - 1.0</li>
              <li>Gemini: 0.0 - 2.0</li>
              <li>Niższa = bardziej deterministyczna, Wyższa = bardziej kreatywna</li>
              <li className="text-amber-700"><strong>Anthropic:</strong> Nie łączyć z Top P</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Max Output Tokens (wymagane)</h4>
            <ul className="mt-1 space-y-1 list-disc list-inside">
              <li>Anthropic: 1 - 4096</li>
              <li>Gemini: 1 - 8192</li>
              <li>Kontroluje maksymalną długość odpowiedzi</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Top P (opcjonalne)</h4>
            <ul className="mt-1 space-y-1 list-disc list-inside">
              <li>Zakres: 0.0 - 1.0</li>
              <li>Próg próbkowania jądrowego</li>
              <li>Niższy = bardziej skoncentrowany, Wyższy = bardziej różnorodny</li>
              <li className="text-amber-700"><strong>Anthropic:</strong> Nie łączyć z Temperature</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Top K (opcjonalne)</h4>
            <ul className="mt-1 space-y-1 list-disc list-inside">
              <li>Ogranicza wybór tokenów do K najlepszych kandydatów</li>
              <li>Zalecane: 40-100 dla kreatywności, 1-20 dla precyzji</li>
              <li>Wyłącz checkbox jeśli nie chcesz używać</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

