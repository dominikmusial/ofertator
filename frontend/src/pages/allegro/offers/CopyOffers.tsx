import { useState } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { useSharedAccounts } from '../../../hooks/marketplaces/allegro/accounts'
import { useCopyOffers } from '../../../hooks/shared/offers'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import { useToastStore } from '../../../store/toastStore'
import { useDeliverySettings } from '../../../hooks/shared/settings'
import { useAfterSalesServices } from '../../../hooks/shared/settings'
import AccountSelector from '../../../components/ui/AccountSelector'

export default function CopyOffers() {
  const { current } = useAccountStore()
  const { accounts } = useSharedAccounts()
  const copyMutation = useCopyOffers()
  const { addToast } = useToastStore()

  const [sourceOfferId, setSourceOfferId] = useState('')
  const [targetAccountId, setTargetAccountId] = useState('')
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const [copyOptions, setCopyOptions] = useState({
    copy_images: true,
    copy_description: true,
    copy_parameters: true,
    copy_shipping: true,
    copy_return_policy: true,
    copy_warranty: true,
    copy_price: false,
    copy_quantity: false
  })

  const [selectedDeliveryId, setSelectedDeliveryId] = useState('')
  const [selectedWarrantyId, setSelectedWarrantyId] = useState('')
  const [selectedReturnPolicyId, setSelectedReturnPolicyId] = useState('')

  const { data: taskStatus } = useTaskStatus(currentTaskId || undefined)
  const { data: deliverySettings } = useDeliverySettings(targetAccountId ? parseInt(targetAccountId) : 0)
  const { data: afterSalesServices } = useAfterSalesServices(targetAccountId ? parseInt(targetAccountId) : 0)

  const targetAccounts = accounts?.filter(acc => acc.id !== current?.id) || []

  const handleCopy = () => {
    if (!current || !sourceOfferId || !targetAccountId) {
      addToast('Proszę wypełnić wszystkie wymagane pola', 'error')
      return
    }

    copyMutation.mutate({
      requests: [{
        source_account_id: current.id,
        source_offer_id: sourceOfferId,
        options: {
          target_account_id: parseInt(targetAccountId),
          ...copyOptions,
          selected_delivery_id: selectedDeliveryId || undefined,
          selected_warranty_id: selectedWarrantyId || undefined,
          selected_return_policy_id: selectedReturnPolicyId || undefined
        }
      }]
    }, {
      onSuccess: (data) => {
        if (data && data.length > 0) {
          setCurrentTaskId(data[0].task_id)
        }
      }
    })
  }

  const handleOptionChange = (option: string, value: boolean) => {
    setCopyOptions(prev => ({ ...prev, [option]: value }))
  }

  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Kopiowanie Ofert</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby kopiować oferty, wybierz konto źródłowe powyżej</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full flex flex-col max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Kopiowanie Ofert</h1>
          <p className="text-gray-600 mt-1">
            Kopiuj oferty między kontami
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Konto źródłowe:</span>
          <AccountSelector />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6">
        <h2 className="text-xl font-semibold mb-4">Konfiguracja kopiowania</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Source offer selection */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">ID oferty źródłowej</label>
              <input
                type="text"
                value={sourceOfferId}
                onChange={(e) => setSourceOfferId(e.target.value)}
                placeholder="Wprowadź ID oferty (np. 13796064815)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Konto docelowe</label>
              <select
                value={targetAccountId}
                onChange={(e) => setTargetAccountId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Wybierz konto docelowe</option>
                {targetAccounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.nazwa_konta}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Copy options */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Opcje kopiowania</h3>
            <div className="space-y-3">
              {[
                { key: 'copy_images', label: 'Obrazy' },
                { key: 'copy_description', label: 'Opis' },
                { key: 'copy_parameters', label: 'Parametry' },
                { key: 'copy_shipping', label: 'Dostawa' },
                { key: 'copy_return_policy', label: 'Zwroty' },
                { key: 'copy_warranty', label: 'Gwarancja' },
                { key: 'copy_price', label: 'Cena' },
                { key: 'copy_quantity', label: 'Ilość' }
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={copyOptions[key as keyof typeof copyOptions]}
                    onChange={(e) => handleOptionChange(key, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Delivery, Warranty, and Returns Selection */}
          {targetAccountId && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Ustawienia dla konta docelowego</h3>
              
              {/* Delivery Settings */}
              {copyOptions.copy_shipping && deliverySettings?.deliveryMethods && Array.isArray(deliverySettings.deliveryMethods) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wybierz metodę dostawy
                  </label>
                  <select
                    value={selectedDeliveryId}
                    onChange={(e) => setSelectedDeliveryId(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Wybierz metodę dostawy --</option>
                    {deliverySettings.deliveryMethods.map((method) => (
                      <option key={method.id} value={method.id}>
                        {method.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Warranty Settings */}
              {copyOptions.copy_warranty && afterSalesServices?.warranties && Array.isArray(afterSalesServices.warranties) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wybierz gwarancję
                  </label>
                  <select
                    value={selectedWarrantyId}
                    onChange={(e) => setSelectedWarrantyId(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Wybierz gwarancję --</option>
                    {afterSalesServices.warranties.map((warranty) => (
                      <option key={warranty.id} value={warranty.id}>
                        {warranty.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Return Policy Settings */}
              {copyOptions.copy_return_policy && afterSalesServices?.returns && Array.isArray(afterSalesServices.returns) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wybierz politykę zwrotów
                  </label>
                  <select
                    value={selectedReturnPolicyId}
                    onChange={(e) => setSelectedReturnPolicyId(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Wybierz politykę zwrotów --</option>
                    {afterSalesServices.returns.map((returnPolicy) => (
                      <option key={returnPolicy.id} value={returnPolicy.id}>
                        {returnPolicy.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleCopy}
            disabled={!sourceOfferId || !targetAccountId || copyMutation.isPending || (taskStatus && taskStatus.status === 'PROGRESS')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {copyMutation.isPending ? 'Uruchamianie...' : 
             taskStatus?.status === 'PROGRESS' ? 'Kopiowanie...' : 
             'Kopiuj ofertę'}
          </button>
        </div>

        {/* Task Progress Indicator */}
        {taskStatus && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Status kopiowania:</span>
              <span className={`text-sm px-2 py-1 rounded ${
                taskStatus.result?.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                taskStatus.result?.status === 'FAILURE' ? 'bg-red-100 text-red-800' :
                taskStatus.status === 'PROGRESS' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {taskStatus.result?.status === 'SUCCESS' ? 'Ukończono' :
                 taskStatus.result?.status === 'FAILURE' ? 'Błąd' :
                 taskStatus.status === 'PROGRESS' ? 'W toku' :
                 'Oczekuje'}
              </span>
            </div>
            
            {taskStatus.meta?.status && (
              <div className="text-sm text-gray-600 mb-2">
                {taskStatus.meta.status}
              </div>
            )}

            {taskStatus.status === 'PROGRESS' && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full transition-all duration-300 animate-pulse" style={{width: '50%'}}></div>
              </div>
            )}

            {taskStatus.result?.status === 'SUCCESS' && taskStatus.result?.new_offer_id && (
              <div className="text-sm text-green-600">
                Nowa oferta utworzona: {taskStatus.result.new_offer_id}
              </div>
            )}

            {taskStatus.result?.status === 'FAILURE' && taskStatus.result?.error && (
              <div className="text-sm text-red-600">
                Błąd: {taskStatus.result.error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 