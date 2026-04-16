interface ImportError {
  row: number
  offer_id: string
  error: string
}

interface ImportResult {
  success: boolean
  message: string
  imported_count?: number
  deleted_count?: number
  errors?: ImportError[]
}

interface ImportProgressModalProps {
  isOpen: boolean
  onClose: () => void
  importResult: ImportResult | undefined
  isLoading: boolean
  error: Error | null
}

export default function ImportProgressModal({
  isOpen,
  onClose,
  importResult,
  isLoading,
  error
}: ImportProgressModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {isLoading ? 'Importowanie...' : 'Wynik Importu'}
          </h2>
          {!isLoading && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto flex-1">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-8">
              <svg className="animate-spin h-12 w-12 text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-gray-700 font-medium">Przetwarzanie pliku...</p>
              <p className="text-sm text-gray-500 mt-2">Proszę czekać, trwa walidacja i import danych</p>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="font-medium text-red-900 mb-1">Błąd podczas importu</h3>
                  <p className="text-sm text-red-700">{error.message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Success State */}
          {importResult && !isLoading && importResult.success && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-medium text-green-900 mb-1">Import zakończony sukcesem!</h3>
                    <p className="text-sm text-green-700">{importResult.message}</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-blue-700 mb-1">Zaimportowano</p>
                  <p className="text-2xl font-bold text-blue-900">{importResult.imported_count || 0}</p>
                  <p className="text-xs text-blue-600 mt-1">harmonogramów</p>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <p className="text-sm text-orange-700 mb-1">Usunięto</p>
                  <p className="text-2xl font-bold text-orange-900">{importResult.deleted_count || 0}</p>
                  <p className="text-xs text-orange-600 mt-1">starych harmonogramów</p>
                </div>
              </div>
            </div>
          )}

          {/* Validation Errors State */}
          {importResult && !isLoading && !importResult.success && importResult.errors && (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-medium text-red-900 mb-1">Import nieudany</h3>
                    <p className="text-sm text-red-700">{importResult.message}</p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-3">
                  Błędy walidacji ({importResult.errors.length}):
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {importResult.errors.map((err, idx) => (
                    <div key={idx} className="bg-white border border-red-200 rounded-lg p-3">
                      <div className="flex items-start gap-2">
                        <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded">
                          Wiersz {err.row}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">Oferta: {err.offer_id}</p>
                          <p className="text-sm text-red-600 mt-1">{err.error}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {!isLoading && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Zamknij
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
