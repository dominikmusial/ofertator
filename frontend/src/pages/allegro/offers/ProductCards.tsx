import React, { useState, useRef, useEffect } from 'react'
import { useAuthStore } from '../../../store/authStore'
import { useAccountStore } from '../../../store/accountStore'
import { useToastStore } from '../../../store/toastStore'
import { useBulkGenerateProductCards } from '../../../hooks/shared/offers/bulk'
import { useBulkDeleteAttachments } from '../../../hooks/shared/offers/bulk'
import { useBulkRestoreAttachments } from '../../../hooks/shared/offers/bulk'
import { useUploadCustomAttachment } from '../../../hooks/shared/settings'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'

const ATTACHMENT_TYPES = [
  { label: 'Instrukcja', value: 'MANUAL' },
  { label: 'Warunki oferty specjalnej', value: 'SPECIAL_OFFER_RULES' },
  { label: 'Regulamin konkursu', value: 'COMPETITION_RULES' },
  { label: 'Fragment książki', value: 'BOOK_EXCERPT' },
  { label: 'Instrukcja obsługi', value: 'USER_MANUAL' },
  { label: 'Instrukcja instalacji', value: 'INSTALLATION_INSTRUCTIONS' },
  { label: 'Instrukcja gry', value: 'GAME_INSTRUCTIONS' },
  { label: 'Etykieta energetyczna (JPG/PNG)', value: 'ENERGY_LABEL' },
  { label: 'Karta informacyjna produktu', value: 'PRODUCT_INFORMATION_SHEET' },
  { label: 'Etykieta opony (JPG/PNG)', value: 'TIRE_LABEL' },
  { label: 'Instrukcja bezpieczeństwa', value: 'SAFETY_INFORMATION_MANUAL' },
]

export default function ProductCards() {
  const { user } = useAuthStore()
  const { current: selectedAccount } = useAccountStore()
  const { addToast } = useToastStore()
  
  const [offerIds, setOfferIds] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [attachmentType, setAttachmentType] = useState('MANUAL')
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const [backupData, setBackupData] = useState<any>(null)
  const [fileImportError, setFileImportError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const statusSectionRef = useRef<HTMLDivElement>(null)
  
  const generateProductCardsMutation = useBulkGenerateProductCards()
  const deleteAttachmentsMutation = useBulkDeleteAttachments()
  const restoreAttachmentsMutation = useBulkRestoreAttachments()
  const uploadCustomAttachmentMutation = useUploadCustomAttachment()
  
  const { data: taskStatus } = useTaskStatus(currentTaskId || undefined, !!currentTaskId)

  // Store backup data when delete task completes
  useEffect(() => {
    if (taskStatus && taskStatus.status === 'SUCCESS' && (taskStatus.result as any)?.original_attachments) {
      setBackupData((taskStatus.result as any).original_attachments)
      addToast('Załączniki zostały usunięte. Dane do przywrócenia zostały zapisane.', 'info')
    }
  }, [taskStatus, addToast])

  const parseOfferIds = (text: string): string[] => {
    return text
      .split('\n')
      .map(id => id.trim())
      .filter(id => id.length > 0)
  }

  // Validate offer IDs with centralized logic
  const validateOfferIds = (ids: string[]): string | null => {
    if (ids.length === 0) return null
    
    for (const id of ids) {
      if (!/^\d+$/.test(id)) {
        return `ID oferty "${id}" zawiera nieprawidłowe znaki. Dozwolone są tylko cyfry.`
      }
      if (id.length < 10 || id.length > 15) {
        return `ID oferty "${id}" ma nieprawidłową długość (${id.length} znaków). Wymagane 10-15 znaków.`
      }
    }
    return null
  }

  // File import handlers
  const handleFileImport = (result: any) => {
    try {
      setFileImportError(null)
      if (result?.offerIds) {
        setOfferIds(result.offerIds.join('\n'))
        addToast(`Zaimportowano ${result.offerIds.length} ID ofert`, 'success')
      }
    } catch (error: any) {
      setFileImportError(error.message)
      addToast(`Błąd importu: ${error.message}`, 'error')
    }
  }

  const handleFileImportError = (error: string) => {
    setFileImportError(error)
    addToast(`Błąd importu: ${error}`, 'error')
  }

  const handleClearOfferIds = () => {
    setOfferIds('')
    setFileImportError(null)
  }

  // Clear error when user starts typing
  const handleOfferIdsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setOfferIds(e.target.value)
    if (fileImportError) {
      setFileImportError(null)
    }
  }

  const scrollToStatus = () => {
    setTimeout(() => {
      statusSectionRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      })
    }, 100)
  }

  const handleGenerateProductCards = async () => {
    if (!selectedAccount) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const ids = parseOfferIds(offerIds)
    if (ids.length === 0) {
      addToast('Proszę wprowadzić co najmniej jedno ID oferty', 'error')
      return
    }

    const validationError = validateOfferIds(ids)
    if (validationError) {
      addToast(validationError, 'error')
      return
    }

    try {
      const result = await generateProductCardsMutation.mutateAsync({
        account_id: selectedAccount.id,
        offer_ids: ids,
        strip_html: true  // Always strip HTML (parameter kept for backward compatibility)
      })
      
      setCurrentTaskId(result.task_id)
      scrollToStatus()
      addToast(`Rozpoczęto generowanie kart produktowych dla ${ids.length} ofert`, 'success')
    } catch (error: any) {
      addToast(error.response?.data?.detail || 'Błąd podczas uruchamiania zadania', 'error')
    }
  }

  const handleDeleteAttachments = async () => {
    if (!selectedAccount) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const ids = parseOfferIds(offerIds)
    if (ids.length === 0) {
      addToast('Proszę wprowadzić co najmniej jedno ID oferty', 'error')
      return
    }

    const validationError = validateOfferIds(ids)
    if (validationError) {
      addToast(validationError, 'error')
      return
    }

    if (!confirm(`Czy na pewno chcesz usunąć załączniki dla ${ids.length} ofert?`)) {
      return
    }

    try {
      const result = await deleteAttachmentsMutation.mutateAsync({
        account_id: selectedAccount.id,
        offer_ids: ids
      })
      
      setCurrentTaskId(result.task_id)
      scrollToStatus()
      // Store the task ID so we can get backup data when task completes
      addToast(`Rozpoczęto usuwanie załączników dla ${ids.length} ofert`, 'success')
    } catch (error: any) {
      addToast(error.response?.data?.detail || 'Błąd podczas uruchamiania zadania', 'error')
    }
  }

  const handleRestoreAttachments = async () => {
    if (!selectedAccount) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    if (!backupData) {
      addToast('Brak danych do przywrócenia. Najpierw usuń załączniki, aby utworzyć kopię zapasową.', 'error')
      return
    }

    const ids = parseOfferIds(offerIds)
    if (ids.length === 0) {
      addToast('Proszę wprowadzić co najmniej jedno ID oferty', 'error')
      return
    }

    const validationError = validateOfferIds(ids)
    if (validationError) {
      addToast(validationError, 'error')
      return
    }

    if (!confirm(`Czy na pewno chcesz przywrócić załączniki dla ${ids.length} ofert?`)) {
      return
    }

    try {
      const result = await restoreAttachmentsMutation.mutateAsync({
        account_id: selectedAccount.id,
        offer_ids: ids,
        original_attachments: backupData
      })
      
      setCurrentTaskId(result.task_id)
      scrollToStatus()
      addToast(`Rozpoczęto przywracanie załączników dla ${ids.length} ofert`, 'success')
    } catch (error: any) {
      addToast(error.response?.data?.detail || 'Błąd podczas uruchamiania zadania', 'error')
    }
  }

  const handleUploadCustomAttachment = async () => {
    if (!selectedAccount) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const ids = parseOfferIds(offerIds)
    if (ids.length === 0) {
      addToast('Proszę wprowadzić co najmniej jedno ID oferty', 'error')
      return
    }

    const validationError = validateOfferIds(ids)
    if (validationError) {
      addToast(validationError, 'error')
      return
    }

    if (!selectedFile) {
      addToast('Proszę wybrać plik do wgrania', 'error')
      return
    }

    // Validate file type based on attachment type
    const fileExt = selectedFile.name.toLowerCase().split('.').pop()
    const isImageType = ['ENERGY_LABEL', 'TIRE_LABEL'].includes(attachmentType)
    const isPdfType = !isImageType

    if (isImageType && !['jpg', 'jpeg', 'png'].includes(fileExt || '')) {
      addToast(`Typ załącznika ${attachmentType} wymaga pliku obrazu (JPG, PNG)`, 'error')
      return
    }

    if (isPdfType && fileExt !== 'pdf') {
      addToast(`Typ załącznika ${attachmentType} wymaga pliku PDF`, 'error')
      return
    }

    try {
      const result = await uploadCustomAttachmentMutation.mutateAsync({
        account_id: selectedAccount.id,
        offer_ids: ids,
        attachment_type: attachmentType,
        file: selectedFile
      })
      
      setCurrentTaskId(result.task_id)
      scrollToStatus()
      addToast(`Rozpoczęto wgrywanie własnej karty produktowej dla ${ids.length} ofert`, 'success')
    } catch (error: any) {
      addToast(error.response?.data?.detail || 'Błąd podczas uruchamiania zadania', 'error')
    }
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }





  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">Karty produktowe</h1>
            <p className="text-gray-600 mt-2">
              Generuj karty produktowe, zarządzaj załącznikami i wgrywaj własne pliki do ofert
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* Task Progress Display - Moved to top */}
            {taskStatus && taskStatus.status !== 'SUCCESS' && taskStatus.status !== 'FAILURE' && (
              <div ref={statusSectionRef} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                  <h3 className="text-lg font-semibold text-blue-900">Przetwarzanie w toku...</h3>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-blue-700">Status:</span>
                    <span className="font-medium text-blue-900">{taskStatus.result?.status || 'Przetwarzanie...'}</span>
                  </div>
                  
                  {taskStatus.result?.current !== undefined && taskStatus.result?.total !== undefined && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-blue-700">Postęp:</span>
                        <span className="font-medium text-blue-900">{taskStatus.result.current} / {taskStatus.result.total}</span>
                      </div>
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${Math.round((taskStatus.result.current / taskStatus.result.total) * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {taskStatus.result?.current_offer && (
                    <div className="flex justify-between text-sm">
                      <span className="text-blue-700">Aktualna oferta:</span>
                      <span className="font-medium text-blue-900">{taskStatus.result.current_offer}</span>
                    </div>
                  )}
                  
                  {taskStatus.result?.success_count !== undefined && (
                    <div className="flex justify-between text-sm">
                      <span className="text-blue-700">Udane:</span>
                      <span className="font-medium text-green-600">{taskStatus.result.success_count}</span>
                    </div>
                  )}
                  
                  {taskStatus.result?.failure_count !== undefined && taskStatus.result.failure_count > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-blue-700">Nieudane:</span>
                      <span className="font-medium text-red-600">{taskStatus.result.failure_count}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Task Results Display - Moved to top */}
            {taskStatus && (taskStatus.status === 'SUCCESS' || taskStatus.status === 'FAILURE') && (
              <div ref={statusSectionRef} className={`border rounded-lg p-4 ${
                taskStatus.status === 'SUCCESS' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex justify-between items-center mb-3">
                  <h3 className={`text-lg font-semibold ${
                    taskStatus.status === 'SUCCESS' ? 'text-green-900' : 'text-red-900'
                  }`}>
                    {taskStatus.status === 'SUCCESS' ? 'Zadanie zakończone pomyślnie' : 'Błąd podczas wykonywania zadania'}
                  </h3>
                  <button
                    onClick={() => setCurrentTaskId(null)}
                    className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    Zamknij
                  </button>
                </div>
                
                {taskStatus.status === 'SUCCESS' && taskStatus.result && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-green-700">Udane operacje:</span>
                      <span className="font-medium text-green-900">{taskStatus.result.success_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-green-700">Nieudane operacje:</span>
                      <span className="font-medium text-red-600">{taskStatus.result.failure_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-green-700">Łącznie ofert:</span>
                      <span className="font-medium text-green-900">{taskStatus.result.total || 0}</span>
                    </div>
                    
                    {taskStatus.result.failed_offers && taskStatus.result.failed_offers.length > 0 && (
                      <div className="mt-3">
                        <h4 className="font-medium text-red-900 mb-2">Błędy:</h4>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {taskStatus.result.failed_offers.map((error: any, index: number) => (
                            <div key={index} className="text-xs bg-red-100 p-2 rounded">
                              <span className="font-medium">Oferta {error.offer_id}:</span> {error.error}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {taskStatus.status === 'FAILURE' && (
                  <div className="text-red-700">
                    {taskStatus.result?.exc_message || 'Wystąpił nieoczekiwany błąd'}
                  </div>
                )}
              </div>
            )}

            {/* Account Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Wybierz konto
              </label>
              <AccountSelector />
            </div>

            {/* Offer IDs Input */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  ID ofert (jedno na linię)
                </label>
                <div className="flex gap-2">
                  <OfferSelectorButton
                    accountId={selectedAccount?.id || 0}
                    offerIds={offerIds}
                    setOfferIds={setOfferIds}
                    setError={setFileImportError}
                  />
                  <FileImportButton
                    onImport={handleFileImport}
                    onError={handleFileImportError}
                    config={{
                      extractOfferIds: true,
                      validateOfferIds: true
                    }}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  />
                  <button
                    onClick={handleClearOfferIds}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    Wyczyść
                  </button>
                </div>
              </div>
              <textarea
                value={offerIds}
                onChange={handleOfferIdsChange}
                className={`w-full h-32 px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                  fileImportError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="Wprowadź ID ofert, każde w nowej linii, lub użyj przycisku 'Importuj z pliku' aby wczytać z Excel/CSV..."
              />
              {fileImportError && (
                <div className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                  {fileImportError}
                </div>
              )}
              <div className="mt-2 text-xs text-gray-500">
                Obsługiwane formaty: TXT, CSV, Excel (.xlsx, .xls). Automatyczne wykrywanie nagłówków i separatorów.
              </div>
            </div>



            {/* Generator kart produktowych */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Generator kart produktowych</h3>
              
              <p className="text-sm text-gray-600 mb-4">
                Karty produktowe są automatycznie generowane z czystym tekstem (bez tagów HTML).
              </p>
              
              <button
                onClick={handleGenerateProductCards}
                disabled={generateProductCardsMutation.isPending || !selectedAccount}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {generateProductCardsMutation.isPending ? 'Generowanie...' : 'Generuj karty produktowe'}
              </button>
            </div>

            {/* Własna karta produktowa */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Własna karta produktowa</h3>
              
              <div className="space-y-4">
                {/* File Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wybierz plik
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleFileSelect}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      Wybierz plik
                    </button>
                    <span className="text-sm text-gray-600">
                      {selectedFile ? selectedFile.name : 'Nie wybrano pliku'}
                    </span>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                  />
                </div>

                {/* Attachment Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Typ załącznika
                  </label>
                  <select
                    value={attachmentType}
                    onChange={(e) => setAttachmentType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    {ATTACHMENT_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleUploadCustomAttachment}
                  disabled={uploadCustomAttachmentMutation.isPending || !selectedAccount || !selectedFile}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {uploadCustomAttachmentMutation.isPending ? 'Wgrywanie...' : 'Wgraj własną kartę'}
                </button>
              </div>
            </div>

            {/* Zarządzanie załącznikami */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Zarządzanie załącznikami</h3>
              
              <div className="flex gap-3">
                <button
                  onClick={handleDeleteAttachments}
                  disabled={deleteAttachmentsMutation.isPending || !selectedAccount}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {deleteAttachmentsMutation.isPending ? 'Usuwanie...' : 'Usuń załączniki'}
                </button>
                
                <button
                  onClick={handleRestoreAttachments}
                  disabled={restoreAttachmentsMutation.isPending || !selectedAccount || !backupData}
                  className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {restoreAttachmentsMutation.isPending ? 'Przywracanie...' : 'Przywróć załączniki'}
                </button>
              </div>
              
              {/* Backup Status Indicator */}
              <div className="mt-3 text-sm">
                {backupData ? (
                  <div className="flex items-center text-green-600">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Dane do przywrócenia dostępne ({Object.keys(backupData).length} ofert)
                  </div>
                ) : (
                  <div className="flex items-center text-gray-500">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Brak danych do przywrócenia
                  </div>
                )}
              </div>
              
              <p className="text-sm text-gray-600 mt-2">
                Uwaga: Funkcja przywracania działa tylko z załącznikami usuniętymi w tej sesji.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
