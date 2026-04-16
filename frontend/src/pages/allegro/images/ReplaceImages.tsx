import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useAccountStore } from '../../../store/accountStore'
import { useBulkCompositeImageReplace } from '../../../hooks/shared/images/bulk'
import { useBulkRestoreImagePosition } from '../../../hooks/shared/images/bulk'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import { useToastStore } from '../../../store/toastStore'
import { useImageUpload } from '../../../hooks/shared/images'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { FileImportResult } from '../../../hooks/shared/pricing'

export default function ReplaceImages() {
  const { current } = useAccountStore()
  const [offerIds, setOfferIds] = useState('')
  const [restoreOfferIds, setRestoreOfferIds] = useState('')
  const [imagePosition, setImagePosition] = useState('1')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null)
  const [replaceError, setReplaceError] = useState<string | null>(null)
  const [restoreError, setRestoreError] = useState<string | null>(null)

  // Task tracking
  const [replaceTaskId, setReplaceTaskId] = useState<string | null>(null)
  const [restoreTaskId, setRestoreTaskId] = useState<string | null>(null)

  const { addToast } = useToastStore()
  const compositeImageMutation = useBulkCompositeImageReplace()
  const restoreImageMutation = useBulkRestoreImagePosition()
  const uploadImageMutation = useImageUpload()

  const { data: replaceTaskStatus } = useTaskStatus(replaceTaskId || undefined)
  const { data: restoreTaskStatus } = useTaskStatus(restoreTaskId || undefined)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setSelectedFile(file)
      setUploadedImageUrl(null) // Reset uploaded URL when new file is selected
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: false,
    maxFiles: 1
  })

  const removeFile = () => {
    setSelectedFile(null)
    setUploadedImageUrl(null)
  }

  const handleReplaceFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setOfferIds(result.offerIds.join('\n'))
      setReplaceError(null)
    } else {
      setReplaceError('Nie znaleziono ID ofert w pliku')
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

  const uploadImageIfNeeded = async (): Promise<string> => {
    if (uploadedImageUrl) {
      return uploadedImageUrl
    }

    if (!selectedFile) {
      throw new Error('Nie wybrano pliku obrazu')
    }

    const result = await uploadImageMutation.mutateAsync(selectedFile)
    setUploadedImageUrl(result.url)
    return result.url
  }

  const handleReplaceImages = async () => {
    if (!current) {
      addToast('Wybierz konto', 'error')
      return
    }

    if (!selectedFile && !uploadedImageUrl) {
      addToast('Wybierz plik obrazu nakładki', 'error')
      return
    }

    if (!offerIds.trim()) {
      addToast('Wprowadź ID ofert', 'error')
      return
    }

    try {
      setReplaceError(null)
      
      // Parse offer IDs from textarea
      const lines = offerIds.trim().split('\n').filter(line => line.trim())
      const validOfferIds = lines.map(line => line.trim()).filter(id => id)
      
      // Validate offer IDs format
      const invalidIds = validOfferIds.filter(id => !/^\d+$/.test(id))
      if (invalidIds.length > 0) {
        throw new Error(`Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`)
      }
      
      // Check for reasonable ID length
      const suspiciousIds = validOfferIds.filter(id => id.length < 10 || id.length > 15)
      if (suspiciousIds.length > 0) {
        throw new Error(`Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są poprawne.`)
      }
      const position = parseInt(imagePosition)
      
      if (position < 1 || position > 16) {
        addToast('Numer pozycji zdjęcia musi być z zakresu 1-16', 'error')
        return
      }

      // Upload image to MinIO if not already uploaded
      const imageUrl = await uploadImageIfNeeded()

      // Start the composite image replacement task
      const result = await compositeImageMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds,
        imagePosition: position,
        overlayImageUrl: imageUrl
      })

      setReplaceTaskId(result.task_id)
      addToast('Rozpoczęto podmianę zdjęć', 'success')
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas podmiany zdjęć'
      setReplaceError(errorMessage)
      addToast(errorMessage, 'error')
    }
  }

  const handleRestoreImages = async () => {
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
      
      // Parse offer IDs from textarea
      const lines = restoreOfferIds.trim().split('\n').filter(line => line.trim())
      const validOfferIds = lines.map(line => line.trim()).filter(id => id)
      
      // Validate offer IDs format
      const invalidIds = validOfferIds.filter(id => !/^\d+$/.test(id))
      if (invalidIds.length > 0) {
        throw new Error(`Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`)
      }
      
      // Check for reasonable ID length
      const suspiciousIds = validOfferIds.filter(id => id.length < 10 || id.length > 15)
      if (suspiciousIds.length > 0) {
        throw new Error(`Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są poprawne.`)
      }
      const position = parseInt(imagePosition)
      
      if (position < 1 || position > 16) {
        addToast('Numer pozycji zdjęcia musi być z zakresu 1-16', 'error')
        return
      }

      // Start the restore task
      const result = await restoreImageMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds,
        imagePosition: position
      })

      setRestoreTaskId(result.task_id)
      addToast('Rozpoczęto przywracanie zdjęć', 'success')
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas przywracania zdjęć'
      setRestoreError(errorMessage)
      addToast(errorMessage, 'error')
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
        <h1 className="text-2xl font-bold">Podmiana zdjęć</h1>
        <AccountSelector />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Replace Images Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Podmiana zdjęć</h2>
          
          {/* Image Position Selection */}
          <div className="mb-4">
            <label htmlFor="imagePosition" className="block text-sm font-medium text-gray-700 mb-2">
              Numer pozycji zdjęcia (1-16):
            </label>
            <select
              id="imagePosition"
              value={imagePosition}
              onChange={(e) => setImagePosition(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({ length: 16 }, (_, i) => i + 1).map(num => (
                <option key={num} value={num.toString()}>{num}</option>
              ))}
            </select>
          </div>

          {/* Image Upload */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Zdjęcie nakładki:
            </label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : selectedFile
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              {selectedFile ? (
                <div className="space-y-2">
                  <p className="text-green-600 font-medium">Wybrano: {selectedFile.name}</p>
                  {uploadedImageUrl && (
                    <p className="text-sm text-gray-500">Przesłano na serwer</p>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile()
                    }}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Usuń plik
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600">
                    {isDragActive
                      ? 'Upuść plik tutaj...'
                      : 'Przeciągnij i upuść plik obrazu lub kliknij aby wybrać'}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Obsługiwane formaty: PNG, JPG, JPEG, GIF, WebP
                  </p>
                </div>
              )}
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
                  setError={setReplaceError}
                />
                <FileImportButton
                  label="Importuj z pliku"
                  onImport={handleReplaceFileImport}
                  onError={setReplaceError}
                  config={{ extractOfferIds: true, validateOfferIds: true }}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                />
                <button
                  onClick={() => setOfferIds('')}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  Wyczyść
                </button>
              </div>
            </div>
            <textarea
              value={offerIds}
              onChange={(e) => {
                setOfferIds(e.target.value)
                if (replaceError) setReplaceError(null)
              }}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Wprowadź ID ofert, po jednym w każdej linii..."
            />
            <div className="flex justify-between mt-2">
              <div className="text-xs text-gray-500">
                💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              </div>
            </div>
          </div>

          {/* Replace Button */}
          <button
            onClick={handleReplaceImages}
            disabled={compositeImageMutation.isPending || uploadImageMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {compositeImageMutation.isPending || uploadImageMutation.isPending 
              ? 'Przetwarzanie...' 
              : 'Podmień zdjęcia'
            }
          </button>

          {/* Replace Error Display */}
          {replaceError && (
            <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-start">
                <div className="text-red-600 text-sm">
                  <span className="font-medium">Błąd:</span> {replaceError}
                </div>
                <button
                  onClick={() => setReplaceError(null)}
                  className="ml-auto text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {replaceTaskStatus && (
            <div className="mt-3">
              <div className={`p-3 rounded ${
                replaceTaskStatus.status === 'SUCCESS' ? 'bg-green-50 border border-green-200' :
                replaceTaskStatus.status === 'FAILURE' ? 'bg-red-50 border border-red-200' :
                'bg-blue-50 border border-blue-200'
              }`}>
                <div className={`font-medium ${
                  replaceTaskStatus.status === 'SUCCESS' ? 'text-green-700' :
                  replaceTaskStatus.status === 'FAILURE' ? 'text-red-700' :
                  'text-blue-700'
                }`}>
                  {getTaskStatusText(replaceTaskStatus)}
                </div>

                {/* Show successful offers */}
                {replaceTaskStatus.status === 'SUCCESS' && replaceTaskStatus.result?.successful_offers && replaceTaskStatus.result.successful_offers.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-green-800 mb-2">✅ Zaktualizowane oferty:</h4>
                    <div className="max-h-24 overflow-y-auto bg-white rounded p-2 border border-green-200">
                      {replaceTaskStatus.result.successful_offers.map((offerId: string, index: number) => (
                        <div key={index} className="text-xs text-green-700 mb-1 p-1">
                          <span className="font-medium">Oferta {offerId}:</span> Zdjęcie na pozycji {imagePosition} zostało pomyślnie zastąpione
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Show detailed errors */}
                {replaceTaskStatus.status === 'SUCCESS' && replaceTaskStatus.result?.failed_offers && replaceTaskStatus.result.failed_offers.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-red-800 mb-2">❌ Błędy ({replaceTaskStatus.result.failed_offers.length}):</h4>
                    <div className="max-h-32 overflow-y-auto bg-white rounded border border-red-200">
                      {replaceTaskStatus.result.failed_offers.map((failedOffer: any, index: number) => (
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

        {/* Restore Images Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Przywróć stare zdjęcia</h2>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-4">
              Przywraca zdjęcia z pozycji {imagePosition} z automatycznie utworzonych kopii zapasowych.
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
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                />
                <button
                  onClick={() => setRestoreOfferIds('')}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
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
            <div className="flex justify-between mt-2">
              <div className="text-xs text-gray-500">
                💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              </div>
            </div>
          </div>

          {/* Restore Button */}
          <button
            onClick={handleRestoreImages}
            disabled={restoreImageMutation.isPending}
            className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {restoreImageMutation.isPending 
              ? 'Przywracanie...' 
              : 'Przywróć stare zdjęcia'
            }
          </button>

          {/* Restore Error Display */}
          {restoreError && (
            <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-start">
                <div className="text-red-600 text-sm">
                  <span className="font-medium">Błąd:</span> {restoreError}
                </div>
                <button
                  onClick={() => setRestoreError(null)}
                  className="ml-auto text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
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
                {restoreTaskStatus.status === 'SUCCESS' && restoreTaskStatus.result?.successful_offers && restoreTaskStatus.result.successful_offers.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-green-800 mb-2">✅ Przywrócone oferty:</h4>
                    <div className="max-h-24 overflow-y-auto bg-white rounded p-2 border border-green-200">
                      {restoreTaskStatus.result.successful_offers.map((offerId: string, index: number) => (
                        <div key={index} className="text-xs text-green-700 mb-1 p-1">
                          <span className="font-medium">Oferta {offerId}:</span> Zdjęcie na pozycji {imagePosition} zostało przywrócone z kopii zapasowej
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Show detailed errors */}
                {restoreTaskStatus.status === 'SUCCESS' && restoreTaskStatus.result?.failed_offers && restoreTaskStatus.result.failed_offers.length > 0 && (
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
          <li>• Funkcja tworzy kompozytowe zdjęcia poprzez nakładanie wybranego obrazu na istniejące zdjęcia w ofertach</li>
          <li>• Przed każdą operacją automatycznie tworzona jest kopia zapasowa oferty</li>
          <li>• Pozycje zdjęć liczone są od 1 do 16 (pierwsze zdjęcie to miniaturka)</li>
          <li>• Przywracanie działa tylko dla ofert, które mają kopie zapasowe w systemie</li>
          <li>• Jeśli zdjęcie występuje również w opisie oferty, zostanie tam również zaktualizowane</li>
        </ul>
      </div>
    </div>
  )
} 