import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { useAccountStore } from '../../../store/accountStore'
import { useBulkUpdateThumbnails } from '../../../hooks/shared/images/bulk'
import { useRestoreThumbnails } from '../../../hooks/shared/images/bulk'
import { useMultipleTaskStatus, TaskInfo } from '../../../hooks/shared/tasks'
import { useToastStore } from '../../../store/toastStore'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { FileImportResult } from '../../../hooks/shared/pricing'

export default function Thumbnails() {
  const { current } = useAccountStore()
  const [offerIds, setOfferIds] = useState('')
  const [restoreOfferIds, setRestoreOfferIds] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [extractIdsFromNames, setExtractIdsFromNames] = useState(false)
  const [updateError, setUpdateError] = useState<string | null>(null)
  const [restoreError, setRestoreError] = useState<string | null>(null)

  // Task tracking
  const [updateTaskIds, setUpdateTaskIds] = useState<TaskInfo[]>([])
  const [restoreTaskIds, setRestoreTaskIds] = useState<TaskInfo[]>([])
  const [updateTasksCompleted, setUpdateTasksCompleted] = useState(false)
  const [restoreTasksCompleted, setRestoreTasksCompleted] = useState(false)

  const { addToast } = useToastStore()
  const bulkUpdateMutation = useBulkUpdateThumbnails()
  const restoreMutation = useRestoreThumbnails()

  const { data: updateTasksStatus } = useMultipleTaskStatus(updateTaskIds, !updateTasksCompleted)
  const { data: restoreTasksStatus } = useMultipleTaskStatus(restoreTaskIds, !restoreTasksCompleted)

  // Check if all tasks are completed and disable polling
  useEffect(() => {
    if (updateTasksStatus && updateTaskIds.length > 0 && 
        updateTasksStatus.every(task => task.status === 'SUCCESS' || task.status === 'FAILURE')) {
      setUpdateTasksCompleted(true)
    }
  }, [updateTasksStatus, updateTaskIds.length])

  useEffect(() => {
    if (restoreTasksStatus && restoreTaskIds.length > 0 && 
        restoreTasksStatus.every(task => task.status === 'SUCCESS' || task.status === 'FAILURE')) {
      setRestoreTasksCompleted(true)
    }
  }, [restoreTasksStatus, restoreTaskIds.length])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setSelectedFiles(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: true
  })

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearFiles = () => {
    setSelectedFiles([])
  }

  const handleUpdateFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setOfferIds(result.offerIds.join('\n'))
      setUpdateError(null)
    } else {
      setUpdateError('Nie znaleziono ID ofert w pliku')
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



  const handleUpdateThumbnails = async () => {
    if (!current) {
      addToast('Wybierz konto', 'error')
      return
    }

    if (selectedFiles.length === 0) {
      addToast('Wybierz pliki obrazów', 'error')
      return
    }

    try {
      setUpdateError(null)
      let validOfferIds: string[] = []

      if (!extractIdsFromNames) {
        if (!offerIds.trim()) {
          addToast('Wprowadź ID ofert', 'error')
          return
        }
        
        // Parse offer IDs from textarea
        const lines = offerIds.trim().split('\n').filter(line => line.trim())
        validOfferIds = lines.map(line => line.trim()).filter(id => id)
        
        // Validate offer IDs format (this will be handled by the centralized validation)
        const invalidIds = validOfferIds.filter(id => !/^\d+$/.test(id))
        if (invalidIds.length > 0) {
          throw new Error(`Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`)
        }
        
        // Check for reasonable ID length
        const suspiciousIds = validOfferIds.filter(id => id.length < 10 || id.length > 15)
        if (suspiciousIds.length > 0) {
          throw new Error(`Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są poprawne.`)
        }
      } else {
        // When extracting from names, we don't need manual offer IDs
        validOfferIds = []
      }

      const result = await bulkUpdateMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds,
        imageFiles: selectedFiles,
        extractIdsFromNames
      })

      if (result && result.length > 0) {
        setUpdateTaskIds(result)
        setUpdateTasksCompleted(false)
        addToast('Rozpoczęto aktualizację miniaturek', 'success')
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas aktualizacji miniaturek'
      setUpdateError(errorMessage)
      addToast(errorMessage, 'error')
    }
  }

  const handleRestoreThumbnails = async () => {
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

      const result = await restoreMutation.mutateAsync({
        accountId: current.id,
        offerIds: validOfferIds
      })

      if (result && result.length > 0) {
        setRestoreTaskIds(result)
        setRestoreTasksCompleted(false)
        addToast('Rozpoczęto przywracanie miniaturek', 'success')
      } else {
        addToast('Brak kopii zapasowych dla podanych ofert', 'info')
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Wystąpił błąd podczas przywracania miniaturek'
      setRestoreError(errorMessage)
      addToast(errorMessage, 'error')
    }
  }

  const getUpdateSummary = () => {
    if (!updateTasksStatus || !Array.isArray(updateTasksStatus)) {
      return { successful: 0, failed: 0, pending: 0, total: 0 }
    }
    
    let successful = 0
    let failed = 0
    let pending = 0
    let total = 0
    
    updateTasksStatus.forEach(task => {
      if (task.status === 'SUCCESS' && task.result) {
        // Count offers within completed tasks
        successful += task.result.success_count || task.result.successful_offers?.length || 0
        failed += task.result.failure_count || task.result.failed_offers?.length || 0
        total += task.result.total_offers || 0
      } else if (task.status === 'FAILURE') {
        // If entire task failed, count as one failure
        failed += 1
        total += 1
      } else if (task.status === 'PENDING' || task.status === 'PROGRESS') {
        // For in-progress tasks, check meta field for progress info
        if (task.meta) {
          successful += task.meta.successful || 0
          failed += task.meta.failed || 0
          // For bulk tasks, we need to estimate total from meta or use the number of offers being processed
          if (task.meta.total_offers) {
            total += task.meta.total_offers
          } else {
            // If no total in meta, estimate from current progress
            const currentCount = (task.meta.successful || 0) + (task.meta.failed || 0)
            if (currentCount > 0) {
              total += currentCount + 1 // +1 for the currently processing offer
            } else {
              pending += 1
            }
          }
        } else {
          pending += 1
        }
      }
    })
    
    return { successful, failed, pending, total }
  }

  const getRestoreSummary = () => {
    if (!restoreTasksStatus || !Array.isArray(restoreTasksStatus)) {
      return { successful: 0, failed: 0, pending: 0, total: 0 }
    }
    
    let successful = 0
    let failed = 0
    let pending = 0
    let total = 0
    
    restoreTasksStatus.forEach(task => {
      if (task.status === 'SUCCESS' && task.result) {
        // For restore tasks, each task handles one offer
        if (task.result.status === 'SUCCESS') {
          successful += 1
        } else {
          failed += 1
        }
        total += 1
      } else if (task.status === 'FAILURE') {
        // If entire task failed, count as one failure
        failed += 1
        total += 1
      } else if (task.status === 'PENDING' || task.status === 'PROGRESS') {
        // For pending tasks, we don't know the result yet
        pending += 1
      }
    })
    
    return { successful, failed, pending, total }
  }

  const updateSummary = getUpdateSummary()
  const restoreSummary = getRestoreSummary()

  // No account selected
  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Miniatury</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby zarządzać miniaturkami ofert, wybierz konto powyżej</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Miniatury</h1>
            <p className="text-gray-600">Zarządzaj miniaturkami (pierwszymi obrazami) ofert</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Update Thumbnails Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Aktualizuj Miniatury</h2>
          
          {/* File Upload Area */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Wybierz pliki obrazów
            </label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-gray-600">
                {isDragActive ? (
                  <p>Upuść pliki tutaj...</p>
                ) : (
                  <div>
                    <p>Przeciągnij i upuść pliki obrazów tutaj, lub kliknij aby wybrać</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Obsługiwane formaty: PNG, JPG, JPEG, GIF, WEBP
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Wybrane pliki ({selectedFiles.length})
                </label>
                <button
                  onClick={clearFiles}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Wyczyść wszystkie
                </button>
              </div>
              <div className="max-h-32 overflow-y-auto border rounded-lg">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border-b last:border-b-0">
                    <span className="text-sm text-gray-700 truncate">{file.name}</span>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-600 hover:text-red-800 ml-2"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extract IDs from Names Option */}
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={extractIdsFromNames}
                onChange={(e) => setExtractIdsFromNames(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">
                Wyciągnij ID ofert z nazw plików
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Gdy zaznaczone, ID ofert będą automatycznie wyciągnięte z nazw plików
            </p>
          </div>

          {/* Offer IDs Input (only when not extracting from names) */}
          {!extractIdsFromNames && (
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  ID Ofert (jeden na linię)
                </label>
                <div className="flex gap-2">
                  <OfferSelectorButton
                    accountId={current.id}
                    offerIds={offerIds}
                    setOfferIds={setOfferIds}
                    setError={setUpdateError}
                  />
                  <FileImportButton
                    label="Importuj z pliku"
                    onImport={handleUpdateFileImport}
                    onError={setUpdateError}
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
                  if (updateError) setUpdateError(null)
                }}
                placeholder="123456789&#10;987654321&#10;..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="mt-2 text-xs text-gray-500">
                💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              </div>
            </div>
          )}

          {updateError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex justify-between items-start">
                <div className="text-red-700 text-sm whitespace-pre-line">{updateError}</div>
                <button
                  onClick={() => setUpdateError(null)}
                  className="text-red-500 hover:text-red-700 ml-2"
                >
                  ×
                </button>
              </div>
            </div>
          )}

          <button
            onClick={handleUpdateThumbnails}
            disabled={bulkUpdateMutation.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg font-medium"
          >
            {bulkUpdateMutation.isPending ? 'Przetwarzanie...' : 'Aktualizuj Miniatury'}
          </button>

          {/* Update Progress */}
          {updateTasksStatus && updateTasksStatus.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-blue-900">Status aktualizacji</h3>
                <span className="text-sm text-blue-700">
                  {updateSummary.successful + updateSummary.failed}/{updateSummary.total}
                </span>
              </div>
              
              <div className="w-full bg-blue-200 rounded-full h-2 mb-3">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${updateSummary.total > 0 ? ((updateSummary.successful + updateSummary.failed) / updateSummary.total) * 100 : 0}%`
                  }}
                ></div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-green-600 font-medium">{updateSummary.successful}</div>
                  <div className="text-gray-600">Sukces</div>
                </div>
                <div className="text-center">
                  <div className="text-red-600 font-medium">{updateSummary.failed}</div>
                  <div className="text-gray-600">Błąd</div>
                </div>
                <div className="text-center">
                  <div className="text-blue-600 font-medium">{updateSummary.pending}</div>
                  <div className="text-gray-600">Oczekuje</div>
                </div>
              </div>

              {updateSummary.failed > 0 && updateTasksStatus && (
                <div className="mt-3 max-h-32 overflow-y-auto">
                  <h4 className="text-sm font-medium text-red-900 mb-1">Błędy:</h4>
                  {updateTasksStatus
                    .filter(task => task.status === 'SUCCESS' && task.result?.failed_offers?.length > 0)
                    .flatMap(task => task.result.failed_offers || [])
                    .map((failedOffer, index) => (
                      <div key={index} className="text-xs text-red-700 mb-1">
                        Oferta {failedOffer.offer_id}: {failedOffer.error || 'Nieznany błąd'}
                      </div>
                    ))}
                  {updateTasksStatus
                    .filter(task => task.status === 'FAILURE')
                    .map((task, index) => (
                      <div key={index} className="text-xs text-red-700 mb-1">
                        Task {task.task_id}: {task.result?.exc_message || task.error || 'Nieznany błąd taska'}
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Restore Thumbnails Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Przywróć Miniatury</h2>
          <p className="text-gray-600 text-sm mb-4">
            Przywróć poprzednie miniatury z kopii zapasowych
          </p>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ID Ofert do przywrócenia (jeden na linię)
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
              placeholder="123456789&#10;987654321&#10;..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="mt-2 text-xs text-gray-500">
              💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
            </div>
          </div>

          {restoreError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex justify-between items-start">
                <div className="text-red-700 text-sm whitespace-pre-line">{restoreError}</div>
                <button
                  onClick={() => setRestoreError(null)}
                  className="text-red-500 hover:text-red-700 ml-2"
                >
                  ×
                </button>
              </div>
            </div>
          )}

          <button
            onClick={handleRestoreThumbnails}
            disabled={restoreMutation.isPending}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg font-medium"
          >
            {restoreMutation.isPending ? 'Przywracanie...' : 'Przywróć Miniatury'}
          </button>

          {/* Restore Progress */}
          {restoreTasksStatus && restoreTasksStatus.length > 0 && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-green-900">Status przywracania</h3>
                <span className="text-sm text-green-700">
                  {restoreSummary.successful + restoreSummary.failed}/{restoreSummary.total}
                </span>
              </div>
              
              <div className="w-full bg-green-200 rounded-full h-2 mb-3">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${restoreSummary.total > 0 ? ((restoreSummary.successful + restoreSummary.failed) / restoreSummary.total) * 100 : 0}%`
                  }}
                ></div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-green-600 font-medium">{restoreSummary.successful}</div>
                  <div className="text-gray-600">Sukces</div>
                </div>
                <div className="text-center">
                  <div className="text-red-600 font-medium">{restoreSummary.failed}</div>
                  <div className="text-gray-600">Błąd</div>
                </div>
                <div className="text-center">
                  <div className="text-blue-600 font-medium">{restoreSummary.pending}</div>
                  <div className="text-gray-600">Oczekuje</div>
                </div>
              </div>

              {restoreSummary.failed > 0 && restoreTasksStatus && (
                <div className="mt-3 max-h-32 overflow-y-auto">
                  <h4 className="text-sm font-medium text-red-900 mb-1">Błędy:</h4>
                  {restoreTasksStatus
                    .filter(task => task.status === 'SUCCESS' && task.result?.status !== 'SUCCESS')
                    .map((task, index) => (
                      <div key={index} className="text-xs text-red-700 mb-1">
                        Oferta {task.result?.offer_id || 'nieznana'}: {task.result?.error || task.error || 'Nieznany błąd'}
                      </div>
                    ))}
                  {restoreTasksStatus
                    .filter(task => task.status === 'FAILURE')
                    .map((task, index) => (
                      <div key={index} className="text-xs text-red-700 mb-1">
                        Task {task.task_id}: {task.result?.exc_message || task.error || 'Nieznany błąd taska'}
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 