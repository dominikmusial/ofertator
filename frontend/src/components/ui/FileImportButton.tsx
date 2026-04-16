import { useFileImport, FileImportConfig, FileImportResult } from '../../hooks/shared/pricing'

interface FileImportButtonProps {
  label?: string
  onImport: (result: FileImportResult) => void
  onError?: (error: string) => void
  config?: FileImportConfig
  className?: string
  disabled?: boolean
  showError?: boolean
}

export default function FileImportButton({
  label = 'Importuj z pliku',
  onImport,
  onError,
  config = {},
  className = '',
  disabled = false,
  showError = false
}: FileImportButtonProps) {
  const { importFile, isLoading, error, clearError } = useFileImport(config)

  const handleImport = async () => {
    try {
      const result = await importFile()
      if (result) {
        onImport(result)
      }
    } catch (error: any) {
      if (onError) {
        onError(error.message)
      }
    }
  }

  // Clear error when component unmounts or error changes
  if (error && onError) {
    onError(error)
    clearError()
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleImport}
        disabled={disabled || isLoading}
        className={`px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      >
        {isLoading ? 'Przetwarzanie...' : label}
      </button>
      
      {/* Centralized Error Display */}
      {showError && error && (
        <div className="p-3 bg-red-50 rounded-lg border border-red-200">
          <div className="flex items-start">
            <div className="text-red-600 text-sm">
              <span className="font-medium">Błąd:</span> {error}
            </div>
            <button
              onClick={clearError}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  )
} 