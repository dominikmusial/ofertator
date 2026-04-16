import { useState, useRef } from 'react'
import { useDownloadTemplate } from '../../hooks/shared/templates'
import { useImportSchedules } from '../../hooks/shared/pricing'
import ImportProgressModal from './ImportProgressModal'

interface FileImportSectionProps {
  accountId: number
  onImportSuccess: () => void
}

export default function FileImportSection({ accountId, onImportSuccess }: FileImportSectionProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [showProgressModal, setShowProgressModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const downloadTemplate = useDownloadTemplate()
  const importMutation = useImportSchedules(accountId)

  const handleDownloadTemplate = (format: 'xlsx' | 'csv') => {
    downloadTemplate.mutate({ accountId, format })
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const validExtensions = ['.xlsx', '.csv']
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

      if (!validExtensions.includes(fileExtension)) {
        alert('Nieprawidłowy format pliku. Użyj .xlsx lub .csv')
        return
      }

      // Validate file size (max 5MB)
      const maxSize = 5 * 1024 * 1024 // 5MB
      if (file.size > maxSize) {
        alert('Plik jest za duży. Maksymalny rozmiar to 5MB')
        return
      }

      setSelectedFile(file)
    }
  }

  const handleImport = async () => {
    if (!selectedFile) {
      alert('Wybierz plik do zaimportowania')
      return
    }

    setShowProgressModal(true)

    try {
      await importMutation.mutateAsync(selectedFile)
      // Success is handled by the mutation's onSuccess callback
      onImportSuccess()
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      // Error is handled by the mutation's onError callback
      console.error('Import error:', error)
    } finally {
      setShowProgressModal(false)
    }
  }

  const handleClearFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Import Harmonogramów z Pliku</h2>

      {/* Download Template Section */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-medium text-blue-900 mb-2">Krok 1: Pobierz szablon</h3>
        <p className="text-sm text-blue-700 mb-3">
          Pobierz pusty szablon, wypełnij danymi i wgraj z powrotem
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => handleDownloadTemplate('xlsx')}
            disabled={downloadTemplate.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Pobierz Excel (.xlsx)
          </button>
          <button
            onClick={() => handleDownloadTemplate('csv')}
            disabled={downloadTemplate.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Pobierz CSV (.csv)
          </button>
        </div>
      </div>

      {/* File Format Info */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="font-medium text-gray-900 mb-2">Format pliku:</h3>
        <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
          <li>Kolumny: <code className="bg-gray-200 px-1 rounded">ID Oferty</code>, <code className="bg-gray-200 px-1 rounded">Nazwa Oferty</code>, <code className="bg-gray-200 px-1 rounded">Cena Promocyjna</code>, <code className="bg-gray-200 px-1 rounded">1</code> do <code className="bg-gray-200 px-1 rounded">31</code> (dni miesiąca)</li>
          <li>Zaznacz aktywne dni wpisując: <code className="bg-gray-200 px-1 rounded">x</code>, <code className="bg-gray-200 px-1 rounded">X</code>, <code className="bg-gray-200 px-1 rounded">1</code> lub <code className="bg-gray-200 px-1 rounded">true</code></li>
          <li>Pozostaw puste komórki dla nieaktywnych dni</li>
          <li>Maksymalny rozmiar pliku: 5MB</li>
        </ul>
      </div>

      {/* Upload Section */}
      <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
        <h3 className="font-medium text-yellow-900 mb-2">Krok 2: Wgraj wypełniony plik</h3>
        <p className="text-sm text-yellow-700 mb-3">
          <strong>UWAGA:</strong> Import usunie wszystkie istniejące harmonogramy dla tego konta i utworzy nowe na podstawie pliku!
        </p>

        <div className="flex items-center gap-3">
          <label className="flex-1">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.csv"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-medium
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                cursor-pointer"
            />
          </label>
        </div>

        {selectedFile && (
          <div className="mt-3 p-3 bg-white rounded border border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
            <button
              onClick={handleClearFile}
              className="text-red-600 hover:text-red-800"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Import Button */}
      <div className="flex justify-end">
        <button
          onClick={handleImport}
          disabled={!selectedFile || importMutation.isPending}
          className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          {importMutation.isPending ? (
            <>
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Importowanie...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Importuj Harmonogramy
            </>
          )}
        </button>
      </div>

      {/* Progress Modal */}
      {showProgressModal && (
        <ImportProgressModal
          isOpen={showProgressModal}
          onClose={() => setShowProgressModal(false)}
          importResult={importMutation.data}
          isLoading={importMutation.isPending}
          error={importMutation.error}
        />
      )}
    </div>
  )
}
