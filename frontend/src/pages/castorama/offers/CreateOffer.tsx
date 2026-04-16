import { useAccountStore } from '../../../store/accountStore'
import MarketplaceAccountSelector from '../../../components/ui/MarketplaceAccountSelector'

export default function CastoramaCreateOffer() {
  const { current } = useAccountStore()

  if (!current || current.marketplace_type !== 'castorama') {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Wystawianie Ofert - Castorama</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Wybierz konto:</span>
            <MarketplaceAccountSelector marketplaceType="castorama" />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto Castorama</div>
            <div className="text-sm">
              Aby wystawić oferty na Castorama, wybierz konto Castorama powyżej
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full flex flex-col max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <span className="text-4xl">🟠</span>
            <h1 className="text-3xl font-semibold">Wystawianie Ofert - Castorama</h1>
          </div>
          <p className="text-gray-600 mt-2">
            Zarządzaj produktami dla konta: <span className="font-medium text-orange-600">{current.nazwa_konta}</span>
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Konto:</span>
          <MarketplaceAccountSelector marketplaceType="castorama" />
        </div>
      </div>
    </div>
  )
}
