import { useState, useMemo } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { usePromotions, type Promotion } from '../../../hooks/marketplaces/allegro/promotions'
import { useCreatePromotion } from '../../../hooks/marketplaces/allegro/promotions'
import { useDeletePromotion } from '../../../hooks/marketplaces/allegro/promotions'
import { useDeleteAllPromotions } from '../../../hooks/marketplaces/allegro/promotions'
import { useToastStore } from '../../../store/toastStore'
import AccountSelector from '../../../components/ui/AccountSelector'
import PromotionCreator from '../../../components/promotions/PromotionCreator'

interface CreatePromotionResult {
  success_count: number
  total_groups: number
  results: boolean[]
}

export default function Promotions() {
  const { current } = useAccountStore()
  const { data: promotions, isLoading, refetch } = usePromotions(current?.id)
  const createMutation = useCreatePromotion()
  const deleteMutation = useDeletePromotion()
  const deleteAllMutation = useDeleteAllPromotions()
  const { addToast } = useToastStore()

  const [activeTab, setActiveTab] = useState<'create' | 'manage'>('create')
  const [searchTerm, setSearchTerm] = useState('')
  
  // Creation result tracking
  const [creationResult, setCreationResult] = useState<CreatePromotionResult | null>(null)
  const [creationError, setCreationError] = useState<string | null>(null)

  const handleCreate = async (promotionData: {
    offer_ids: string[]
    for_each_quantity: number
    percentage: number
    group_size: number
  }) => {
    if (!current?.id) return

    // Clear previous results and errors
    setCreationResult(null)
    setCreationError(null)

    try {
      const result = await createMutation.mutateAsync({
        account_id: current.id,
        ...promotionData
      })
      
      // Store the result for display
      setCreationResult(result)
      
      // Check if promotion creation was actually successful
      const successCount = result?.success_count || 0
      const totalGroups = result?.total_groups || 0
      
      if (successCount > 0) {
        // At least some promotions were created successfully
        setActiveTab('manage')
        refetch()
      } else {
        // No promotions were created - stay on current tab
        // Results will be displayed in the error section below
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas tworzenia promocji'
      setCreationError(errorMessage)
    }
  }

  const handleDelete = async (promotion: Promotion) => {
    if (!current?.id) return
    if (!confirm(`Czy na pewno chcesz usunąć promocję "${promotion.id}"?`)) return

    try {
      await deleteMutation.mutateAsync({
        account_id: current.id,
        promotion_id: promotion.id
      })
      addToast('Promocja została usunięta', 'success')
    } catch (error) {
      addToast('Błąd podczas usuwania promocji', 'error')
    }
  }

  const handleDeleteAll = async () => {
    if (!current?.id) return
    if (!confirm('Czy na pewno chcesz usunąć WSZYSTKIE rabaty? Ta operacja jest nieodwracalna.')) return

    try {
      await deleteAllMutation.mutateAsync({
        account_id: current.id
      })
    } catch (error) {
      addToast('Błąd podczas usuwania promocji', 'error')
    }
  }

  const filteredPromotions = useMemo(() => {
    if (!promotions || !searchTerm) return promotions || []
    
    return promotions.filter(promotion => 
      promotion.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      promotion.offers.some(offerId => 
        offerId.toString().toLowerCase().includes(searchTerm.toLowerCase())
      )
    )
  }, [promotions, searchTerm])

  const downloadExcel = () => {
    if (!filteredPromotions.length) {
      addToast('Brak rabatów do pobrania', 'info')
      return
    }

    // Create CSV content with offer IDs
    const offerIds = filteredPromotions.flatMap(promotion => promotion.offers)
    const csvContent = 'ID oferty\n' + offerIds.join('\n')
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `rabaty_${current?.nazwa_konta}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    addToast('Plik został pobrany', 'success')
  }

  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Promocje</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby zarządzać promocjami, wybierz konto powyżej</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Promocje</h1>
          <p className="text-gray-600 mt-1">
            Zarządzaj promocjami i rabatami ilościowymi dla konta: <span className="font-medium">{current.nazwa_konta}</span>
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Konto:</span>
          <AccountSelector />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('create')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'create'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Tworzenie rabatów
        </button>
        <button
          onClick={() => setActiveTab('manage')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'manage'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Lista rabatów
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'create' ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Utwórz nowy rabat ilościowy</h2>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-800 mb-2">Jak działają rabaty ilościowe?</h3>
              <p className="text-sm text-blue-700">
                Rabaty typu "bundle" pozwalają na oferowanie rabatu przy zakupie określonej ilości produktów. 
                Oferty zostaną automatycznie podzielone na grupy o wybranym rozmiarze.
              </p>
            </div>
          </div>
          <PromotionCreator
            accountId={current.id}
            onSave={handleCreate}
            onCancel={() => {}}
            onInputChange={() => {
              setCreationResult(null)
              setCreationError(null)
            }}
          />
          
          {/* Creation Error Display */}
          {creationError && (
            <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-start">
                <div className="text-red-600 text-sm">
                  <span className="font-medium">Błąd:</span> {creationError}
                </div>
                <button
                  onClick={() => setCreationError(null)}
                  className="ml-auto text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
          
          {/* Creation Results Display */}
          {creationResult && (
            <div className="mt-4 space-y-2">
              {creationResult.success_count === 0 ? (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-start justify-between">
                    <div className="text-red-600 text-sm">
                      <span className="font-medium">Nie udało się utworzyć żadnych rabatów:</span>
                      <div className="mt-2">
                        <div>• Sprawdź czy ID ofert są prawidłowe</div>
                        <div>• Upewnij się, że oferty należą do wybranego konta</div>
                        <div>• Zweryfikuj czy oferty nie mają już aktywnych rabatów</div>
                        <div>• Sprawdź czy oferty są aktywne i dostępne</div>
                      </div>
                      <div className="mt-2 text-xs text-red-500">
                        Próbowano utworzyć {creationResult.total_groups} grup rabatów z {creationResult.results.length} ofert
                      </div>
                    </div>
                    <button
                      onClick={() => setCreationResult(null)}
                      className="ml-auto text-red-400 hover:text-red-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : creationResult.success_count < creationResult.total_groups ? (
                <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-start justify-between">
                    <div className="text-yellow-800 text-sm">
                      <span className="font-medium">Częściowy sukces:</span> Utworzono {creationResult.success_count} z {creationResult.total_groups} grup rabatów
                      <div className="mt-2">
                        <div>• {creationResult.success_count} grup zostało pomyślnie utworzonych</div>
                        <div>• {creationResult.total_groups - creationResult.success_count} grup nie zostało utworzonych</div>
                        <div className="mt-1 text-xs">
                          Możliwe przyczyny niepowodzeń: nieprawidłowe ID ofert, oferty należące do innego konta, 
                          istniejące rabaty, nieaktywne oferty
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setCreationResult(null)}
                      className="ml-auto text-yellow-400 hover:text-yellow-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-start justify-between">
                    <div className="text-green-600 text-sm">
                      <span className="font-medium">Sukces:</span> Pomyślnie utworzono wszystkie {creationResult.success_count} grup rabatów!
                    </div>
                    <button
                      onClick={() => setCreationResult(null)}
                      className="ml-auto text-green-400 hover:text-green-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Aktywne rabaty</h2>
              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  placeholder="Szukaj..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={downloadExcel}
                  className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                >
                  Pobierz
                </button>
                <button
                  onClick={handleDeleteAll}
                  disabled={deleteAllMutation.isPending}
                  className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-sm"
                >
                  Usuń wszystkie
                </button>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                    <div className="h-8 bg-gray-200 rounded w-20 ml-auto"></div>
                  </div>
                ))}
              </div>
            ) : filteredPromotions && filteredPromotions.length > 0 ? (
              <div className="space-y-4">
                {filteredPromotions.map((promotion) => (
                  <div key={promotion.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      {/* Left - Basic Info */}
                      <div>
                        <div className="text-sm font-medium text-gray-900">ID: {promotion.id}</div>
                        <div className="text-sm text-gray-500">Typ: {promotion.type}</div>
                        {promotion.discount && (
                          <div className="text-sm text-gray-500">Rabat: {promotion.discount}%</div>
                        )}
                        {promotion.for_each_quantity && (
                          <div className="text-sm text-gray-500">Co {promotion.for_each_quantity} sztuk</div>
                        )}
                      </div>
                      
                      {/* Center - Offers */}
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-2">
                          Oferty ({promotion.offers.length}):
                        </div>
                        <div className="bg-gray-50 rounded p-2 max-h-24 overflow-y-auto">
                          <div className="text-xs text-gray-600 space-y-1">
                            {promotion.offers.slice(0, 5).map((offerId) => (
                              <div key={offerId}>{offerId}</div>
                            ))}
                            {promotion.offers.length > 5 && (
                              <div className="text-gray-400">...i {promotion.offers.length - 5} więcej</div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Right - Actions */}
                      <div className="flex items-center justify-end">
                        <button
                          onClick={() => handleDelete(promotion)}
                          disabled={deleteMutation.isPending}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-sm"
                        >
                          {deleteMutation.isPending ? '...' : 'Usuń rabat'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchTerm ? 'Nie znaleziono pasujących rabatów' : 'Brak rabatów'}
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchTerm ? 'Spróbuj zmienić kryteria wyszukiwania' : 'Utwórz swój pierwszy rabat ilościowy'}
                </p>
                {!searchTerm && (
                  <button
                    onClick={() => setActiveTab('create')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Utwórz rabat
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
} 