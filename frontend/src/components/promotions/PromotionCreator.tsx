import { useState } from 'react'
import FileImportButton from '../ui/FileImportButton'
import OfferSelectorButton from '../ui/OfferSelectorButton'
import { FileImportResult } from '../../hooks/shared/pricing'

interface PromotionCreatorProps {
  accountId: number
  onSave: (data: {
    offer_ids: string[]
    for_each_quantity: number
    percentage: number
    group_size: number
  }) => void
  onCancel: () => void
  onInputChange?: () => void
}

function PromotionCreator({ accountId, onSave, onCancel, onInputChange }: PromotionCreatorProps) {
  const [formData, setFormData] = useState({
    for_each_quantity: 2,
    percentage: 15,
    group_size: 10,
    offer_ids_text: ''
  })
  const [importError, setImportError] = useState<string | null>(null)

  const handleFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setFormData(prev => ({
        ...prev,
        offer_ids_text: result.offerIds!.join('\n')
      }))
      setImportError(null)
      onInputChange?.()
    } else {
      setImportError('Nie znaleziono ID ofert w pliku')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Parse offer IDs from text
    const offer_ids = formData.offer_ids_text
      .split('\n')
      .map(id => id.trim())
      .filter(id => id.length > 0)
    
    if (offer_ids.length > 0) {
      onSave({
        offer_ids,
        for_each_quantity: formData.for_each_quantity,
        percentage: formData.percentage,
        group_size: formData.group_size
      })
    }
  }

  // Wrapper functions for OfferSelectorButton integration
  const handleOfferIdsChange = (newOfferIds: string) => {
    setFormData(prev => ({ ...prev, offer_ids_text: newOfferIds }))
    if (importError) setImportError(null)
    onInputChange?.()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Co która sztuka (2-5):
          </label>
          <input
            type="number"
            value={formData.for_each_quantity}
            onChange={(e) => {
            setFormData(prev => ({ ...prev, for_each_quantity: parseInt(e.target.value) }))
            onInputChange?.()
          }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="2"
            max="5"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Procent rabatu (15-100):
          </label>
          <input
            type="number"
            value={formData.percentage}
            onChange={(e) => {
            setFormData(prev => ({ ...prev, percentage: parseInt(e.target.value) }))
            onInputChange?.()
          }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="15"
            max="100"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Liczba ofert w grupie (1-1000):
          </label>
          <input
            type="number"
            value={formData.group_size}
            onChange={(e) => {
            setFormData(prev => ({ ...prev, group_size: parseInt(e.target.value) }))
            onInputChange?.()
          }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1"
            max="1000"
            required
          />
        </div>
      </div>

      <div className="bg-blue-50 p-3 rounded-md">
        <p className="text-sm text-blue-700">
          <strong>Jak to działa:</strong> Oferty zostaną podzielone na grupy po {formData.group_size} sztuk. 
          Każda grupa otrzyma osobny rabat {formData.percentage}% przy zakupie {formData.for_each_quantity} produktów.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lista ID ofert (jedna na linię):
        </label>
        <textarea
          value={formData.offer_ids_text}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, offer_ids_text: e.target.value }))
            if (importError) setImportError(null)
            onInputChange?.()
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={12}
          placeholder="Wprowadź ID ofert, każde w nowej linii&#10;np:&#10;12345678901&#10;12345678902&#10;12345678903"
          required
        />
        <div className="mt-2 flex justify-between items-center">
          <div className="flex space-x-2">
            <OfferSelectorButton
              accountId={accountId}
              offerIds={formData.offer_ids_text}
              setOfferIds={handleOfferIdsChange}
              setError={setImportError}
            />
            <FileImportButton
              label="Importuj z pliku"
              onImport={handleFileImport}
              onError={setImportError}
              config={{ extractOfferIds: true, validateOfferIds: true }}
            />
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, offer_ids_text: '' }))}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              Wyczyść
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Liczba ofert: {formData.offer_ids_text.split('\n').filter(id => id.trim()).length}
          </div>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          💡 Obsługiwane formaty plików: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
        </div>
        
        {/* Import Error Display */}
        {importError && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-start">
              <div className="text-red-600 text-sm">
                <span className="font-medium">Błąd:</span> {importError}
              </div>
              <button
                onClick={() => setImportError(null)}
                className="ml-auto text-red-400 hover:text-red-600"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Anuluj
        </button>
        <button
          type="submit"
          disabled={!formData.offer_ids_text.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Utwórz rabat ilościowy
        </button>
      </div>
    </form>
  )
}

export default PromotionCreator 