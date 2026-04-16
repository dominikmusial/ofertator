import { useState, useEffect } from 'react'
import Modal from '../ui/Modal'
import { MARKETPLACE_CONFIGS } from '../../types/marketplace'
import AllegroAuthFlow from './AllegroAuthFlow'
import MiraklAuthFlow from '../mirakl/MiraklAuthFlow'
import { useFeatureFlags } from '../../hooks/shared/useFeatureFlags'

interface Props {
  open: boolean
  onClose: () => void
}

type MarketplaceSelection = 'allegro' | 'decathlon' | 'castorama' | 'leroymerlin' | null

export default function AddAccountModal({ open, onClose }: Props) {
  const [step, setStep] = useState<'select' | 'auth'>('select')
  const [selectedMarketplace, setSelectedMarketplace] = useState<MarketplaceSelection>(null)
  const { isMarketplaceEnabled } = useFeatureFlags()

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setStep('select')
      setSelectedMarketplace(null)
    }
  }, [open])

  const handleMarketplaceSelect = (marketplace: 'allegro' | 'decathlon' | 'castorama' | 'leroymerlin') => {
    setSelectedMarketplace(marketplace)
    setStep('auth')
  }

  const handleBack = () => {
    setStep('select')
    setSelectedMarketplace(null)
  }

  const handleSuccess = () => {
    onClose()
  }

  return (
    <Modal open={open} onClose={onClose}>
      {step === 'select' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">Dodaj integrację</h2>
            <p className="text-gray-600 text-sm">Wybierz platformę marketplace</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Allegro */}
            {isMarketplaceEnabled('allegro') && (
              <button
                onClick={() => handleMarketplaceSelect('allegro')}
                className="border-2 border-gray-200 rounded-lg p-6 hover:border-orange-500 hover:bg-orange-50 transition-all group"
              >
                <div className="text-5xl mb-3">{MARKETPLACE_CONFIGS.allegro.icon}</div>
                <div className="font-semibold text-lg mb-1">{MARKETPLACE_CONFIGS.allegro.name}</div>
                <div className="text-xs text-gray-500 group-hover:text-orange-700">OAuth Device Flow</div>
              </button>
            )}

            {/* Decathlon */}
            {isMarketplaceEnabled('decathlon') && (
              <button
                onClick={() => handleMarketplaceSelect('decathlon')}
                className="border-2 border-gray-200 rounded-lg p-6 hover:border-blue-500 hover:bg-blue-50 transition-all group"
              >
                <div className="text-5xl mb-3">{MARKETPLACE_CONFIGS.decathlon.icon}</div>
                <div className="font-semibold text-lg mb-1">{MARKETPLACE_CONFIGS.decathlon.name}</div>
                <div className="text-xs text-gray-500 group-hover:text-blue-700">API Key (Mirakl)</div>
              </button>
            )}

            {/* Castorama */}
            {isMarketplaceEnabled('castorama') && (
              <button
                onClick={() => handleMarketplaceSelect('castorama')}
                className="border-2 border-gray-200 rounded-lg p-6 hover:border-yellow-500 hover:bg-yellow-50 transition-all group"
              >
                <div className="text-5xl mb-3">{MARKETPLACE_CONFIGS.castorama.icon}</div>
                <div className="font-semibold text-lg mb-1">{MARKETPLACE_CONFIGS.castorama.name}</div>
                <div className="text-xs text-gray-500 group-hover:text-yellow-700">API Key (Mirakl)</div>
              </button>
            )}

            {/* Leroy Merlin */}
            {isMarketplaceEnabled('leroymerlin') && (
              <button
                onClick={() => handleMarketplaceSelect('leroymerlin')}
                className="border-2 border-gray-200 rounded-lg p-6 hover:border-green-500 hover:bg-green-50 transition-all group"
              >
                <div className="text-5xl mb-3">{MARKETPLACE_CONFIGS.leroymerlin.icon}</div>
                <div className="font-semibold text-lg mb-1">{MARKETPLACE_CONFIGS.leroymerlin.name}</div>
                <div className="text-xs text-gray-500 group-hover:text-green-700">API Key (Mirakl)</div>
              </button>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p className="font-medium mb-1">💡 Wskazówka:</p>
            <p>
              Każda platforma używa innego sposobu autoryzacji. Po wybraniu platformy zostaniesz
              poprowadzony przez odpowiedni proces autoryzacji.
            </p>
          </div>
        </div>
      )}

      {step === 'auth' && selectedMarketplace === 'allegro' && (
        <AllegroAuthFlow onSuccess={handleSuccess} onBack={handleBack} />
      )}

      {step === 'auth' && ['decathlon', 'castorama', 'leroymerlin'].includes(selectedMarketplace || '') && (
        <MiraklAuthFlow 
          marketplaceType={selectedMarketplace as 'decathlon' | 'castorama' | 'leroymerlin'}
          onSuccess={handleSuccess} 
          onBack={handleBack} 
        />
      )}
    </Modal>
  )
} 