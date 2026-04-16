import { useEffect } from 'react'
import { useAuthorizeAccount } from '../../hooks/marketplaces/allegro/auth'
import { useAuthStatus } from '../../hooks/marketplaces/allegro/auth'
import { useToastStore } from '../../store/toastStore'

interface Props {
  onSuccess: () => void
  onBack: () => void
}

export default function AllegroAuthFlow({ onSuccess, onBack }: Props) {
  const authMutation = useAuthorizeAccount()
  const { addToast } = useToastStore()

  const started = authMutation.isSuccess
  const { user_code, verification_uri, task_id } = authMutation.data || {}

  const { data: statusData } = useAuthStatus(task_id)
  const startErrorMessage =
    (authMutation.error as any)?.response?.data?.detail ||
    authMutation.error?.message ||
    'Nie udało się rozpocząć autoryzacji Allegro'

  useEffect(() => {
    if (
      statusData &&
      typeof statusData === 'object' &&
      'result' in statusData &&
      statusData.result &&
      typeof statusData.result === 'object' &&
      'status' in statusData.result &&
      statusData.result.status === 'SUCCESS'
    ) {
      setTimeout(onSuccess, 1000)
    }
  }, [statusData, onSuccess])

  return (
    <div className="space-y-4">
      {!started ? (
        <>
          <div className="flex items-center space-x-3 mb-4">
            <button
              onClick={onBack}
              className="text-gray-400 hover:text-gray-600"
            >
              ← Wstecz
            </button>
            <h2 className="text-xl font-semibold">Dodaj konto Allegro</h2>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h3 className="font-medium text-orange-900 mb-2">Autoryzacja OAuth (Device Flow)</h3>
            <p className="text-sm text-orange-800">
              Zostaniesz przekierowany do strony Allegro w celu autoryzacji. Nazwa konta zostanie
              automatycznie pobrana po zalogowaniu.
            </p>
          </div>
          <button
            className="w-full rounded bg-orange-600 px-4 py-3 text-white hover:bg-orange-700 disabled:opacity-50 font-medium"
            disabled={authMutation.isPending}
            onClick={() =>
              authMutation.mutate(undefined, {
                onError: (error: any) => {
                  const message =
                    error?.response?.data?.detail ||
                    error?.message ||
                    'Nie udało się rozpocząć autoryzacji Allegro'
                  addToast(message, 'error')
                },
              })
            }
          >
            {authMutation.isPending ? 'Rozpoczynam...' : 'Rozpocznij autoryzację Allegro'}
          </button>
          {authMutation.isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 text-sm">
                <span className="font-medium">Błąd:</span> {String(startErrorMessage)}
              </p>
              <p className="text-red-700 text-xs mt-2">
                Jeśli uruchamiasz lokalnie: ustaw poprawne ALLEGRO_CLIENT_ID i ALLEGRO_CLIENT_SECRET w pliku .env.
              </p>
            </div>
          )}
        </>
      ) : (
        <>
          <h2 className="text-xl font-semibold mb-4">Krok 2: Autoryzacja w Allegro</h2>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
            <div>
              <p className="text-sm font-medium text-blue-900 mb-2">
                1. Otwórz poniższy link w przeglądarce:
              </p>
              <a
                href={verification_uri}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline break-all hover:text-blue-800"
              >
                {verification_uri}
              </a>
            </div>
            <div>
              <p className="text-sm font-medium text-blue-900 mb-2">2. Wprowadź kod:</p>
              <div className="bg-white border-2 border-blue-300 rounded-lg p-3 text-center">
                <div className="text-3xl font-mono font-bold text-blue-600 tracking-widest">
                  {user_code}
                </div>
              </div>
            </div>
          </div>
          
          {statusData &&
            typeof statusData === 'object' &&
            'result' in statusData &&
            statusData.result &&
            typeof statusData.result === 'object' &&
            'status' in statusData.result &&
            statusData.result.status === 'SUCCESS' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-700 font-medium">
                  ✓ Konto zostało dodane pomyślnie! Okno zamknie się za chwilę...
                </p>
              </div>
            )}
          {statusData &&
            typeof statusData === 'object' &&
            ((('status' in statusData && statusData.status === 'FAILURE') ||
              ('result' in statusData &&
                statusData.result &&
                typeof statusData.result === 'object' &&
                'status' in statusData.result &&
                statusData.result.status === 'FAILURE'))) && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700 text-sm">
                  <span className="font-medium">Błąd:</span>{' '}
                  {statusData.result &&
                  typeof statusData.result === 'object' &&
                  'error' in statusData.result
                    ? String(statusData.result.error)
                    : 'Nie udało się dodać konta'}
                </p>
              </div>
            )}
          <button
            className="w-full rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
            onClick={onSuccess}
          >
            Zamknij
          </button>
        </>
      )}
    </div>
  )
}
