import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { useOfferCategories } from '../../hooks/shared/offers'
import { OfferFilters } from '../../hooks/shared/offers'

interface OfferFilterPanelProps {
  accountId: number
  filters: OfferFilters
  onFilterChange: <K extends keyof OfferFilters>(key: K, value: OfferFilters[K]) => void
  onClearFilters: () => void
}

export default function OfferFilterPanel({ 
  accountId, 
  filters, 
  onFilterChange, 
  onClearFilters 
}: OfferFilterPanelProps) {
  // Fetch top-level categories (without search)
  const { data: categoriesData, isLoading: categoriesLoading } = useOfferCategories(accountId)

  const [priceErrors, setPriceErrors] = useState<{ from?: string; to?: string }>({})

  // Validate price inputs
  const validatePrice = (value: string, type: 'from' | 'to') => {
    if (!value) {
      setPriceErrors(prev => ({ ...prev, [type]: undefined }))
      return true
    }

    const num = parseFloat(value)
    if (isNaN(num) || num < 0) {
      setPriceErrors(prev => ({ ...prev, [type]: 'Cena musi być liczbą >= 0' }))
      return false
    }

    if (type === 'to' && num < 1) {
      setPriceErrors(prev => ({ ...prev, [type]: 'Cena musi być >= 1 PLN' }))
      return false
    }

    // Cross-validation
    const otherValue = type === 'from' ? filters.price_to : filters.price_from
    if (otherValue) {
      const otherNum = parseFloat(otherValue)
      if (!isNaN(otherNum)) {
        if (type === 'from' && num > otherNum) {
          setPriceErrors(prev => ({ ...prev, [type]: 'Cena od nie może być większa niż cena do' }))
          return false
        }
        if (type === 'to' && num < parseFloat(filters.price_from || '0')) {
          setPriceErrors(prev => ({ ...prev, [type]: 'Cena do nie może być mniejsza niż cena od' }))
          return false
        }
      }
    }

    setPriceErrors(prev => ({ ...prev, [type]: undefined }))
    return true
  }

  const handlePriceChange = (value: string, type: 'from' | 'to') => {
    const key = type === 'from' ? 'price_from' : 'price_to'
    onFilterChange(key, value)
    validatePrice(value, type)
  }

  const handleCategoryChange = (categoryId: string) => {
    onFilterChange('category_id', categoryId)
  }

  const hasActiveFilters = !!(
    filters.search || 
    filters.category_id || 
    filters.price_from || 
    filters.price_to || 
    filters.offer_ids
  )

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filtry wyszukiwania</h3>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
            Wyczyść filtry
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Title search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tytuł zawiera
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => onFilterChange('search', e.target.value)}
              placeholder="Wyszukaj w tytułach ofert..."
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Category selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Kategoria
          </label>
          <select
            value={filters.category_id}
            onChange={(e) => handleCategoryChange(e.target.value)}
            disabled={categoriesLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            <option value="">Wszystkie kategorie</option>
            {categoriesLoading ? (
              <option disabled>Ładowanie kategorii...</option>
            ) : categoriesData && Array.isArray(categoriesData.categories) ? (
              categoriesData.categories.map((category: { id: string; name: string }) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))
            ) : null}
          </select>
        </div>

        {/* Price range */}
        <div className="md:col-span-2 lg:col-span-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Zakres cen (PLN)
          </label>
          <div className="flex gap-2">
            <div className="flex-1">
              <input
                type="number"
                value={filters.price_from}
                onChange={(e) => handlePriceChange(e.target.value, 'from')}
                placeholder="Cena od"
                min="0"
                step="0.01"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  priceErrors.from ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {priceErrors.from && (
                <p className="text-xs text-red-600 mt-1">{priceErrors.from}</p>
              )}
            </div>
            <div className="flex-1">
              <input
                type="number"
                value={filters.price_to}
                onChange={(e) => handlePriceChange(e.target.value, 'to')}
                placeholder="Cena do"
                min="1"
                step="0.01"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  priceErrors.to ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {priceErrors.to && (
                <p className="text-xs text-red-600 mt-1">{priceErrors.to}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Offer IDs input - full width */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          ID ofert (oddzielone przecinkami)
        </label>
        <textarea
          value={filters.offer_ids}
          onChange={(e) => onFilterChange('offer_ids', e.target.value)}
          placeholder="Wprowadź ID ofert oddzielone przecinkami, np: 12345678901, 12345678902, 12345678903"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
        />
        <p className="text-xs text-gray-500 mt-1">
          Możesz wprowadzić wiele ID ofert oddzielonych przecinkami lub nową linią
        </p>
      </div>

    </div>
  )
}
