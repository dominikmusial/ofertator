import * as React from 'react'
import { useEffect, useState } from 'react'
import Modal from '../ui/Modal'
import { useReAuthAccount } from '../../hooks/marketplaces/allegro/auth'
import { useReAuthStatus } from '../../hooks/marketplaces/allegro/auth'
import { useSharedAccounts } from '../../hooks/marketplaces/allegro/accounts'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'
import { useToastStore } from '../../store/toastStore'

interface Props {
  open: boolean
  onClose: () => void
  accountId: number
  accountName: string
}

export default function ReAuthAccountModal({ open, onClose, accountId, accountName }: Props) {
  const { startReAuth, isLoading, error } = useReAuthAccount()
  const [reAuthData, setReAuthData] = useState<{
    user_code: string
    verification_uri: string
    task_id: string
  } | null>(null)

  const { status } = useReAuthStatus(
    reAuthData ? accountId : null,
    reAuthData?.task_id || null
  )

  // Track if we need to reload on close
  const [shouldReloadOnClose, setShouldReloadOnClose] = useState(false)

  // Mark that we should reload when user closes the modal
  useEffect(() => {
    if (status?.result?.status === 'SUCCESS') {
      setShouldReloadOnClose(true)
    }
  }, [status])

  const handleStartReAuth = async () => {
    const result = await startReAuth(accountId)
    if (result) {
      setReAuthData(result)
    }
  }

  const handleClose = () => {
    setReAuthData(null)
    setShouldReloadOnClose(false)
    onClose()
    
    // Reload page after modal closes if re-auth was successful
    if (shouldReloadOnClose) {
      setTimeout(() => window.location.reload(), 100)
    }
  }

  return (
    <Modal open={open} onClose={handleClose}>
      {!reAuthData ? (
        // Allegro Re-Auth Flow - Step 1
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Ponowna autoryzacja - Allegro</h2>
          <p className="text-gray-600">
            Konto <span className="font-semibold">{accountName}</span> wymaga ponownej autoryzacji.
            Token odświeżania wygasł lub został unieważniony.
          </p>
          <div className="bg-yellow-50 border border-yellow-200 p-3 rounded text-sm text-yellow-800">
            <strong>⚠️ Ważne:</strong> Podczas autoryzacji zaloguj się na konto <strong>{accountName}</strong>. 
            Logowanie na inne konto spowoduje błąd.
          </div>
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-red-700 text-sm">
              {error}
            </div>
          )}
          <button
            className="rounded bg-orange-600 px-4 py-2 text-white hover:bg-orange-700 disabled:opacity-50"
            disabled={isLoading}
            onClick={handleStartReAuth}
          >
            {isLoading ? 'Rozpoczynanie...' : 'Rozpocznij ponowną autoryzację'}
          </button>
        </div>
      ) : (
        // Allegro Re-Auth Flow - Step 2
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Krok 2: Autoryzacja w Allegro</h2>
          <p>1. Otwórz poniższy link w przeglądarce:</p>
          <a 
            href={reAuthData.verification_uri} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-indigo-600 underline break-all hover:text-indigo-800"
          >
            {reAuthData.verification_uri}
          </a>
          <p>2. Wprowadź kod:</p>
          <div className="text-2xl font-mono font-bold bg-gray-100 p-3 rounded text-center">
            {reAuthData.user_code}
          </div>
          
          {/* Show spinner while waiting (PENDING or PROGRESS, and no terminal result yet) */}
          {status && !status.result?.status && (
            <div className="flex items-center space-x-2 text-blue-600">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Oczekiwanie na autoryzację...</span>
            </div>
          )}

          {status?.result?.status === 'SUCCESS' && (
            <div className="bg-green-50 border border-green-200 p-4 rounded">
              <div className="text-green-700 font-semibold flex items-center space-x-2 mb-2">
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Konto zostało pomyślnie ponownie autoryzowane!</span>
              </div>
              <div className="text-sm text-green-600">
                Token odświeżania został zaktualizowany i będzie ważny przez następne 3 miesiące.
              </div>
            </div>
          )}

          {(status?.status === 'FAILURE' || status?.result?.status === 'FAILURE') && (
            <div className="text-red-700 bg-red-50 p-4 rounded border border-red-200">
              <div className="font-semibold mb-2">❌ Błąd autoryzacji</div>
              <div className="text-sm whitespace-pre-wrap">
                {status.result?.error || 'Nie udało się ponownie autoryzować konta'}
              </div>
            </div>
          )}

          <button
            className={`rounded px-4 py-2 text-white ${
              status?.result?.status === 'SUCCESS' 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
            onClick={handleClose}
          >
            {status?.result?.status === 'SUCCESS' ? 'Gotowe' : 'Zamknij'}
          </button>
        </div>
      )}
    </Modal>
  )
}

