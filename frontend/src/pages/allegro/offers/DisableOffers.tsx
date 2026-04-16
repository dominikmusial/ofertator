import { useState, useEffect, useRef } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { useBulkChangeStatus } from '../../../hooks/shared/offers/bulk'
import { useMultipleTaskStatus } from '../../../hooks/shared/tasks'
import { useToastStore } from '../../../store/toastStore'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { FileImportResult } from '../../../hooks/shared/pricing'

interface TaskResponse {
  task_id: string
  offer_id: string
}

// Utility function to translate API errors to Polish
const translateApiError = (error: string): string => {
  if (!error) return 'Nieznany błąd'
  
  // Handle 404 errors
  if (error.includes('404') && error.includes('Not Found')) {
    return 'Oferta nie została znaleziona. Sprawdź czy ID oferty jest poprawne.'
  }
  
  // Handle 403 errors
  if (error.includes('403') && error.includes('Forbidden')) {
    return 'Brak uprawnień do tej oferty. Sprawdź czy oferta należy do wybranego konta.'
  }
  
  // Handle 401 errors
  if (error.includes('401') && error.includes('Unauthorized')) {
    return 'Brak autoryzacji. Sprawdź połączenie z kontem Allegro.'
  }
  
  // Handle 400 errors
  if (error.includes('400') && error.includes('Bad Request')) {
    return 'Nieprawidłowe żądanie. Sprawdź poprawność danych.'
  }
  
  // Handle 500 errors
  if (error.includes('500') && error.includes('Internal Server Error')) {
    return 'Błąd serwera Allegro. Spróbuj ponownie za chwilę.'
  }
  
  // Handle 429 errors (rate limiting)
  if (error.includes('429') && error.includes('Too Many Requests')) {
    return 'Zbyt wiele żądań. Poczekaj chwilę i spróbuj ponownie.'
  }
  
  // Handle timeout errors
  if (error.includes('timeout') || error.includes('Timeout')) {
    return 'Przekroczono limit czasu. Spróbuj ponownie.'
  }
  
  // Handle connection errors
  if (error.includes('Connection') || error.includes('connection')) {
    return 'Błąd połączenia z serwerem Allegro.'
  }
  
  // Handle specific Allegro API errors
  if (error.includes('offer not found') || error.includes('OFFER_NOT_FOUND')) {
    return 'Oferta nie została znaleziona w systemie Allegro.'
  }
  
  if (error.includes('access denied') || error.includes('ACCESS_DENIED')) {
    return 'Dostęp zabroniony. Sprawdź uprawnienia konta.'
  }
  
  if (error.includes('offer already ended') || error.includes('OFFER_ALREADY_ENDED')) {
    return 'Oferta została już zakończona.'
  }
  
  if (error.includes('offer already active') || error.includes('OFFER_ALREADY_ACTIVE')) {
    return 'Oferta jest już aktywna.'
  }
  
  // Return original error if no translation found, but clean it up
  return error.replace(/Client Error: /g, '').replace(/for url: https:\/\/api\.allegro\.pl\/[^\s]+/g, '')
}

export default function DisableOffers() {
  const { current } = useAccountStore()
  const changeStatusMutation = useBulkChangeStatus()
  const { addToast } = useToastStore()

  const [offerIds, setOfferIds] = useState('')
  const [currentTasks, setCurrentTasks] = useState<TaskResponse[]>([])
  const [operationType, setOperationType] = useState<'ENDED' | 'ACTIVE' | null>(null)
  const [fileImportError, setFileImportError] = useState<string | null>(null)
  const [tasksCompleted, setTasksCompleted] = useState(false)

  // Calculate if we should continue polling
  const shouldPoll = currentTasks.length > 0 && !tasksCompleted
  const { data: taskStatuses } = useMultipleTaskStatus(currentTasks, shouldPoll)

  // Calculate task summary
  const getTaskSummary = () => {
    if (!taskStatuses || taskStatuses.length === 0) return null

    const completed = taskStatuses.filter(task => task.status === 'SUCCESS' || task.status === 'FAILURE')
    const successful = taskStatuses.filter(task => task.status === 'SUCCESS')
    const failed = taskStatuses.filter(task => task.status === 'FAILURE')
    const inProgress = taskStatuses.filter(task => task.status === 'PROGRESS' || task.status === 'PENDING')

    const allCompleted = completed.length === taskStatuses.length

    return {
      total: taskStatuses.length,
      successful: successful.length,
      failed: failed.length,
      inProgress: inProgress.length,
      allCompleted,
      successfulTasks: successful,
      failedTasks: failed
    }
  }

  const summary = getTaskSummary()

  // Update completion state when tasks are done
  useEffect(() => {
    if (summary?.allCompleted && !tasksCompleted) {
      setTasksCompleted(true)
    }
  }, [summary?.allCompleted, tasksCompleted])

  // Clear completed tasks function
  const clearCompletedTasks = () => {
    setCurrentTasks([])
    setOperationType(null)
    setTasksCompleted(false)
  }

  const handleFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setOfferIds(result.offerIds.join('\n'))
      setFileImportError(null)
    } else {
      setFileImportError('Nie znaleziono ID ofert w pliku')
    }
  }

  const handleClearIds = () => {
    setOfferIds('')
    setFileImportError(null)
  }

  const handleStatusChange = (status: 'ENDED' | 'ACTIVE') => {
    if (!current) {
      addToast('Wybierz konto', 'error')
      return
    }

    const ids = offerIds.split('\n').map(id => id.trim()).filter(id => id)
    if (ids.length === 0) {
      addToast('Wprowadź ID ofert', 'error')
      return
    }

    // Validate offer IDs format
    const invalidIds = ids.filter(id => !/^\d+$/.test(id))
    if (invalidIds.length > 0) {
      const errorMessage = `Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`
      addToast(errorMessage, 'error')
      return
    }

    // Check for reasonable ID length
    const suspiciousIds = ids.filter(id => id.length < 10 || id.length > 15)
    if (suspiciousIds.length > 0) {
      const errorMessage = `Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są poprawne.`
      addToast(errorMessage, 'error')
      return
    }

    const action = status === 'ENDED' ? 'zakończyć' : 'przywrócić'
    const confirmed = window.confirm(`Czy na pewno chcesz ${action} ${ids.length} ofert?`)
    
    if (confirmed) {
      setOperationType(status)
      // Clear previous tasks when starting a new operation
      setCurrentTasks([])
      setTasksCompleted(false)
      
      changeStatusMutation.mutate({
        account_id: current.id,
        offer_ids: ids,
        status
      }, {
        onSuccess: (data) => {
          setCurrentTasks(data)
        }
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Wyłączanie ofert</h1>
        <AccountSelector />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">ID ofert do zakończenia (jedno na linię):</h2>
        
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ID ofert (jedno na linię):
              </label>
              <div className="flex gap-2">
                <OfferSelectorButton
                  accountId={current.id}
                  offerIds={offerIds}
                  setOfferIds={setOfferIds}
                  setError={setFileImportError}
                />
                <FileImportButton
                  label="Importuj z pliku"
                  onImport={handleFileImport}
                  onError={setFileImportError}
                  config={{ extractOfferIds: true, validateOfferIds: true }}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                />
                <button
                  onClick={handleClearIds}
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
                if (fileImportError) setFileImportError(null)
              }}
              placeholder="Wprowadź ID ofert, każde w nowej linii..."
              className="w-full h-64 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="flex justify-between mt-2">
              <div className="text-xs text-gray-500">
                💡 Obsługiwane formaty: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
              </div>
              <div className="text-sm text-gray-500">
                {offerIds.split('\n').filter(id => id.trim()).length} ofert
              </div>
            </div>
          </div>

          {/* File Import Error Display */}
          {fileImportError && (
            <div className="p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-start">
                <div className="text-red-600 text-sm">
                  <span className="font-medium">Błąd:</span> {fileImportError}
                </div>
                <button
                  onClick={() => setFileImportError(null)}
                  className="ml-auto text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          <div className="flex justify-center space-x-4 pt-4">
            <button
              onClick={() => handleStatusChange('ENDED')}
              disabled={changeStatusMutation.isPending || (summary && !summary.allCompleted)}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {changeStatusMutation.isPending && operationType === 'ENDED' ? 'Zakańczanie...' : 'Zakończ oferty'}
            </button>
            <button
              onClick={() => handleStatusChange('ACTIVE')}
              disabled={changeStatusMutation.isPending || (summary && !summary.allCompleted)}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {changeStatusMutation.isPending && operationType === 'ACTIVE' ? 'Przywracanie...' : 'Przywróć oferty'}
            </button>
          </div>
        </div>
      </div>

      {/* Task Progress */}
      {summary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Status operacji</h3>
          
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Postęp: {summary.successful + summary.failed}/{summary.total}</span>
              <span>
                {summary.allCompleted ? 'Zakończono' : `W toku (${summary.inProgress} pozostało)`}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((summary.successful + summary.failed) / summary.total) * 100}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{summary.successful}</div>
              <div className="text-sm text-green-600">Sukces</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{summary.failed}</div>
              <div className="text-sm text-red-600">Błędów</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{summary.inProgress}</div>
              <div className="text-sm text-blue-600">W toku</div>
            </div>
          </div>

          {/* Detailed Results */}
          {summary.allCompleted && (
            <div className="space-y-4">
              {/* Clear Results Button */}
              <div className="flex justify-end">
                <button
                  onClick={clearCompletedTasks}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Wyczyść wyniki
                </button>
              </div>

              {/* Successful Operations */}
              {summary.successfulTasks.length > 0 && (
                <div>
                  <h4 className="font-medium text-green-700 mb-2 flex items-center">
                    <span className="w-4 h-4 bg-green-500 rounded-full mr-2"></span>
                    Pomyślnie przetworzone oferty ({summary.successfulTasks.length})
                  </h4>
                  <div className="bg-green-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {summary.successfulTasks.map((task) => (
                      <div key={task.task_id} className="text-sm text-green-700">
                        ✅ Oferta {task.offer_id} - {
                          operationType === 'ENDED' ? 'zakończona pomyślnie' : 'przywrócona pomyślnie'
                        }
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Failed Operations */}
              {summary.failedTasks.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-700 mb-2 flex items-center">
                    <span className="w-4 h-4 bg-red-500 rounded-full mr-2"></span>
                    Błędy ({summary.failedTasks.length})
                  </h4>
                  <div className="bg-red-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {summary.failedTasks.map((task) => (
                      <div key={task.task_id} className="text-sm p-2 border-b border-red-100 last:border-b-0">
                        <div className="font-medium text-red-800">❌ Oferta {task.offer_id}:</div>
                        <div className="text-red-600 mt-1">
                          {translateApiError(task.meta?.exc_message || task.result?.error || 'Nieznany błąd')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
} 