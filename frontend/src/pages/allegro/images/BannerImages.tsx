import { useState } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { useBulkBannerImages } from '../../../hooks/shared/images/bulk'
import { useRestoreBanners } from '../../../hooks/shared/images/bulk'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import { useToastStore } from '../../../store/toastStore'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { FileImportResult } from '../../../hooks/shared/pricing'

export default function BannerImages() {
  const { current } = useAccountStore()
  const [offerIds, setOfferIds] = useState('')
  const [restoreOfferIds, setRestoreOfferIds] = useState('')
  const [settings, setSettings] = useState({
    bannerWidth: 2560,
    bannerHeight: 2560,
    productSize: 50,
    horizontalPosition: 10,
    verticalPosition: 10,
    shape: 'original' as 'original' | 'circle' | 'square',
    removeBackground: false
  })
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [restoreError, setRestoreError] = useState<string | null>(null)

  // Task tracking
  const [processTaskId, setProcessTaskId] = useState<string | null>(null)
  const [restoreTaskId, setRestoreTaskId] = useState<string | null>(null)

  const { addToast } = useToastStore()
  const bannerImagesMutation = useBulkBannerImages()
  const restoreBannersMutation = useRestoreBanners()

  const { data: processTaskStatus } = useTaskStatus(processTaskId)
  const { data: restoreTaskStatus } = useTaskStatus(restoreTaskId)

  const handleProcessFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setOfferIds(result.offerIds.join('\n'))
      setProcessingError(null)
    } else {
      setProcessingError('Nie znaleziono ID ofert w pliku')
    }
  }

  const handleRestoreFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setRestoreOfferIds(result.offerIds.join('\n'))
      setRestoreError(null)
    } else {
      setRestoreError('Nie znaleziono ID ofert w pliku')
    }
  }

  const validateOfferIds = (ids: string): string[] => {
    const lines = ids.trim().split('\n').filter(line => line.trim())
    const validIds = lines.map(line => line.trim()).filter(id => id)
    
    // Validate offer IDs format
    const invalidIds = validIds.filter(id => !/^\d+$/.test(id))
    if (invalidIds.length > 0) {
      throw new Error(`Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`)
    }
    
    // Check for reasonable ID length
    const suspiciousIds = validIds.filter(id => id.length < 10 || id.length > 15)
    if (suspiciousIds.length > 0) {
      throw new Error(`Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są poprawne.`)
    }

    return validIds
  }

  const handleProcessBanners = async () => {
    if (!current) {
      addToast('Wybierz konto', 'error')
      return
    }

    if (!offerIds.trim()) {
      addToast('Wprowadź ID ofert', 'error')
      return
    }

    try {
      setProcessingError(null)
      
      const validOfferIds = validateOfferIds(offerIds)

      const result = await bannerImagesMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds,
        settings
      })

      setProcessTaskId(result.task_id)
      addToast('Rozpoczęto przetwarzanie banerów', 'success')
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas przetwarzania banerów'
      setProcessingError(errorMessage)
    }
  }

  const handleRestoreBanners = async () => {
    if (!current) {
      addToast('Wybierz konto', 'error')
      return
    }

    if (!restoreOfferIds.trim()) {
      addToast('Wprowadź ID ofert do przywrócenia', 'error')
      return
    }

    try {
      setRestoreError(null)
      
      const validOfferIds = validateOfferIds(restoreOfferIds)

      const result = await restoreBannersMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds
      })

      setRestoreTaskId(result.task_id)
      addToast('Rozpoczęto przywracanie banerów', 'success')
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas przywracania banerów'
      setRestoreError(errorMessage)
    }
  }

  const getTaskStatusText = (taskStatus: any) => {
    if (!taskStatus) return null

    if (taskStatus.status === 'PENDING') {
      return 'Zadanie oczekuje na realizację...'
    } else if (taskStatus.status === 'PROGRESS') {
      const current = taskStatus.result?.current || 0
      const total = taskStatus.result?.total || 0
      const statusMsg = taskStatus.result?.status || 'Przetwarzanie...'
      return `${statusMsg} (${current}/${total})`
    } else if (taskStatus.status === 'SUCCESS') {
      const success = taskStatus.result?.success_count || 0
      const failed = taskStatus.result?.failure_count || 0
      const total = taskStatus.result?.total_processed || 0
      return `Zakończono: ${success} sukces, ${failed} błędów z ${total} ofert`
    } else if (taskStatus.status === 'FAILURE') {
      return `Błąd: ${taskStatus.result?.exc_message || 'Nieznany błąd'}`
    }

    return null
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Zdjęcia na Banerach</h1>
        <AccountSelector />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Banner Processing Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Przetwarzanie banerów</h2>
          
          {/* Settings Panel */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-medium">Ustawienia</h3>
            
            {/* Banner Dimensions */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Szerokość banera (px)
                </label>
                <input
                  type="number"
                  value={settings.bannerWidth}
                  onChange={(e) => setSettings(prev => ({ ...prev, bannerWidth: parseInt(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Wysokość banera (px)
                </label>
                <input
                  type="number"
                  value={settings.bannerHeight}
                  onChange={(e) => setSettings(prev => ({ ...prev, bannerHeight: parseInt(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Product Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rozmiar produktu: {settings.productSize}%
              </label>
              <input
                type="range"
                min="10"
                max="150"
                value={settings.productSize}
                onChange={(e) => setSettings(prev => ({ ...prev, productSize: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Horizontal Position */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pozycja pozioma: {settings.horizontalPosition}% od prawej
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.horizontalPosition}
                onChange={(e) => setSettings(prev => ({ ...prev, horizontalPosition: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Vertical Position */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pozycja pionowa: {settings.verticalPosition}% od góry
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.verticalPosition}
                onChange={(e) => setSettings(prev => ({ ...prev, verticalPosition: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Shape Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Kształt produktu
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'original', label: 'Oryginalny' },
                  { value: 'circle', label: 'Okrągły' },
                  { value: 'square', label: 'Kwadratowy' }
                ].map(shape => (
                  <button
                    key={shape.value}
                    onClick={() => setSettings(prev => ({ ...prev, shape: shape.value as any }))}
                    className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                      settings.shape === shape.value
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {shape.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Remove Background */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="removeBackground"
                checked={settings.removeBackground}
                onChange={(e) => setSettings(prev => ({ ...prev, removeBackground: e.target.checked }))}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="removeBackground" className="ml-2 block text-sm text-gray-700">
                Usuń jasne tło produktu
              </label>
            </div>
          </div>

          {/* Offer IDs */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ID ofert (jedno na linię):
              </label>
              <div className="flex gap-2">
                <OfferSelectorButton
                  accountId={current.id}
                  offerIds={offerIds}
                  setOfferIds={setOfferIds}
                  setError={setProcessingError}
                />
                <FileImportButton
                  label="Importuj z pliku"
                  onImport={handleProcessFileImport}
                  onError={setProcessingError}
                  config={{ extractOfferIds: true, validateOfferIds: true }}
                  className="text-sm text-blue-600 hover:text-blue-800"
                />
                <button
                  onClick={() => setOfferIds('')}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Wyczyść
                </button>
              </div>
            </div>
            <textarea
              value={offerIds}
              onChange={(e) => {
                setOfferIds(e.target.value)
                if (processingError) setProcessingError(null)
              }}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Wprowadź ID ofert, po jednym w każdej linii..."
            />
            <div className="mt-2 text-xs text-gray-500">
              💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              <br />
              Ofert: {offerIds.trim() ? offerIds.trim().split('\n').filter(line => line.trim()).length : 0}
            </div>
          </div>

          {/* Process Button */}
          <button
            onClick={handleProcessBanners}
            disabled={bannerImagesMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {bannerImagesMutation.isPending ? 'Przetwarzanie...' : 'Przetwórz banery'}
          </button>

          {/* Processing Status */}
          {processingError && (
            <div className="mt-3 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {processingError}
            </div>
          )}

          {processTaskStatus && (
            <div className="mt-3">
              <div className={`p-3 rounded ${
                processTaskStatus.status === 'SUCCESS' ? 'bg-green-50 border border-green-200' :
                processTaskStatus.status === 'FAILURE' ? 'bg-red-50 border border-red-200' :
                'bg-blue-50 border border-blue-200'
              }`}>
                <div className={`font-medium ${
                  processTaskStatus.status === 'SUCCESS' ? 'text-green-700' :
                  processTaskStatus.status === 'FAILURE' ? 'text-red-700' :
                  'text-blue-700'
                }`}>
                  {getTaskStatusText(processTaskStatus)}
                </div>

                {/* Show successful offers */}
                {processTaskStatus.status === 'SUCCESS' && processTaskStatus.result?.successful_offers?.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-green-800 mb-2">✅ Zaktualizowane oferty:</h4>
                    <div className="max-h-24 overflow-y-auto bg-white rounded p-2 border border-green-200">
                      {processTaskStatus.result.successful_offers.map((offerId: string, index: number) => (
                        <div key={index} className="text-xs text-green-700 mb-1 p-1">
                          <span className="font-medium">Oferta {offerId}:</span> Banery zostały pomyślnie przetworzone
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Show detailed errors */}
                {processTaskStatus.status === 'SUCCESS' && processTaskStatus.result?.failed_offers?.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-red-800 mb-2">❌ Błędy ({processTaskStatus.result.failed_offers.length}):</h4>
                    <div className="max-h-32 overflow-y-auto bg-white rounded border border-red-200">
                      {processTaskStatus.result.failed_offers.map((failedOffer: any, index: number) => (
                        <div key={index} className="text-xs p-2 border-b border-red-100 last:border-b-0">
                          <div className="font-medium text-red-800">Oferta {failedOffer.offer_id}:</div>
                          <div className="text-red-600 mt-1">{failedOffer.reason || 'Nieznany błąd'}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Restore Banners Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Przywróć oryginalne banery</h2>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-4">
              Przywraca oryginalne banery z automatycznie utworzonych kopii zapasowych.
            </p>
          </div>

          {/* Restore Offer IDs */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ID ofert do przywrócenia (jedno na linię):
              </label>
              <div className="flex gap-2">
                <FileImportButton
                  label="Importuj z pliku"
                  onImport={handleRestoreFileImport}
                  onError={setRestoreError}
                  config={{ extractOfferIds: true, validateOfferIds: true }}
                  className="text-sm text-blue-600 hover:text-blue-800"
                />
                <button
                  onClick={() => setRestoreOfferIds('')}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Wyczyść
                </button>
              </div>
            </div>
            <textarea
              value={restoreOfferIds}
              onChange={(e) => {
                setRestoreOfferIds(e.target.value)
                if (restoreError) setRestoreError(null)
              }}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Wprowadź ID ofert, po jednym w każdej linii..."
            />
            <div className="mt-2 text-xs text-gray-500">
              💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              <br />
              Ofert: {restoreOfferIds.trim() ? restoreOfferIds.trim().split('\n').filter(line => line.trim()).length : 0}
            </div>
          </div>

          {/* Restore Button */}
          <button
            onClick={handleRestoreBanners}
            disabled={restoreBannersMutation.isPending}
            className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {restoreBannersMutation.isPending ? 'Przywracanie...' : 'Przywróć oryginalne banery'}
          </button>

          {/* Restore Status */}
          {restoreError && (
            <div className="mt-3 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {restoreError}
            </div>
          )}

          {restoreTaskStatus && (
            <div className="mt-3">
              <div className={`p-3 rounded ${
                restoreTaskStatus.status === 'SUCCESS' ? 'bg-green-50 border border-green-200' :
                restoreTaskStatus.status === 'FAILURE' ? 'bg-red-50 border border-red-200' :
                'bg-blue-50 border border-blue-200'
              }`}>
                <div className={`font-medium ${
                  restoreTaskStatus.status === 'SUCCESS' ? 'text-green-700' :
                  restoreTaskStatus.status === 'FAILURE' ? 'text-red-700' :
                  'text-blue-700'
                }`}>
                  {getTaskStatusText(restoreTaskStatus)}
                </div>

                {/* Show successful offers */}
                {restoreTaskStatus.status === 'SUCCESS' && restoreTaskStatus.result?.successful_offers?.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-green-800 mb-2">✅ Przywrócone oferty:</h4>
                    <div className="max-h-24 overflow-y-auto bg-white rounded p-2 border border-green-200">
                      {restoreTaskStatus.result.successful_offers.map((offerId: string, index: number) => (
                        <div key={index} className="text-xs text-green-700 mb-1 p-1">
                          <span className="font-medium">Oferta {offerId}:</span> Oryginalne banery zostały przywrócone z kopii zapasowej
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Show detailed errors */}
                {restoreTaskStatus.status === 'SUCCESS' && restoreTaskStatus.result?.failed_offers?.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-red-800 mb-2">❌ Błędy ({restoreTaskStatus.result.failed_offers.length}):</h4>
                    <div className="max-h-32 overflow-y-auto bg-white rounded border border-red-200">
                      {restoreTaskStatus.result.failed_offers.map((failedOffer: any, index: number) => (
                        <div key={index} className="text-xs p-2 border-b border-red-100 last:border-b-0">
                          <div className="font-medium text-red-800">Oferta {failedOffer.offer_id}:</div>
                          <div className="text-red-600 mt-1">{failedOffer.reason || 'Nieznany błąd'}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Information Section */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-lg font-medium text-yellow-800 mb-2">Informacje</h3>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>• Funkcja wyszukuje banery o określonych wymiarach w galerii i opisie ofert</li>
          <li>• Na znalezione banery nakłada pierwsze zdjęcie produktu z konfigurowalnymi ustawieniami</li>
          <li>• Przed każdą operacją automatycznie tworzona jest kopia zapasowa oferty</li>
          <li>• Przywracanie działa tylko dla ofert, które mają kopie zapasowe w systemie</li>
          <li>• Usuwanie tła działa najlepiej z jasnymi tłami (białe, szare)</li>
          <li>• Rozmiar produktu jest obliczany jako procent wysokości banera</li>
        </ul>
      </div>
    </div>
  )
} 