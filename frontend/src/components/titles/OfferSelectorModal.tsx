import {  useEffect, useCallback, useRef } from 'react'
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import { useEnhancedOffers } from '../../hooks/shared/offers'
import { useOfferSelector } from '../../hooks/shared/offers'
import OfferFilterPanel from './OfferFilterPanel'

interface OfferSelectorModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (selectedOfferIds: string[]) => void
  accountId: number
  initialSelectedIds?: string[]
}

export default function OfferSelectorModal({
  isOpen,
  onClose,
  onConfirm,
  accountId,
  initialSelectedIds = []
}: OfferSelectorModalProps) {
  const selectAllCheckboxRef = useRef<HTMLInputElement>(null)
  const {
    selectedOffers,
    selectedOfferIds,
    toggleOffer,
    selectAll,
    deselectAll,
    clearSelection,
    loadFromText,
    filters,
    apiFilters,
    updateFilter,
    clearFilters
  } = useOfferSelector()

  // Sync with initial selected IDs (always respect text field state)
  useEffect(() => {
    loadFromText(initialSelectedIds.join('\n'))
  }, [initialSelectedIds, loadFromText])

  // Fetch offers with current filters
  const { data: offersData, isLoading, error } = useEnhancedOffers(accountId, apiFilters)

  // Pagination calculations
  const currentOffers = offersData?.items || []
  const totalOffers = offersData?.total || 0
  const totalPages = Math.ceil(totalOffers / filters.pageSize)
  const currentPage = filters.page

  // Selection state for current page
  const currentPageSelectedCount = currentOffers.filter(offer => selectedOffers.has(offer.id)).length
  const isAllCurrentPageSelected = currentOffers.length > 0 && currentPageSelectedCount === currentOffers.length

  // Handle indeterminate state for select all checkbox
  useEffect(() => {
    if (selectAllCheckboxRef.current) {
      selectAllCheckboxRef.current.indeterminate = currentPageSelectedCount > 0 && !isAllCurrentPageSelected
    }
  }, [currentPageSelectedCount, isAllCurrentPageSelected])

  // Handle pagination
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      updateFilter('page', page)
    }
  }, [totalPages, updateFilter])

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    updateFilter('pageSize', newPageSize)
    updateFilter('page', 1) // Reset to first page
  }, [updateFilter])

  // Handle selection actions
  const handleToggleAll = useCallback(() => {
    if (isAllCurrentPageSelected) {
      deselectAll(currentOffers)
    } else {
      selectAll(currentOffers)
    }
  }, [isAllCurrentPageSelected, deselectAll, selectAll, currentOffers])

  const handleConfirm = useCallback(() => {
    onConfirm(selectedOfferIds)
    onClose()
  }, [onConfirm, selectedOfferIds, onClose])

  const handleCancel = useCallback(() => {
    clearSelection()
    onClose()
  }, [clearSelection, onClose])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return

      if (event.key === 'Escape') {
        handleCancel()
      } else if (event.ctrlKey && event.key === 'a') {
        event.preventDefault()
        handleToggleAll()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, handleCancel, handleToggleAll])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={handleCancel}
        />

        {/* Modal panel */}
        <div className="inline-block w-full max-w-6xl p-6 my-8 overflow-hidden text-left transition-all transform bg-white shadow-xl rounded-lg sm:align-middle">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Wybierz oferty
            </h3>
            <button
              onClick={handleCancel}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Filter panel */}
          <div className="mt-6">
            <OfferFilterPanel
              accountId={accountId}
              filters={filters}
              onFilterChange={updateFilter}
              onClearFilters={clearFilters}
            />
          </div>

          {/* Results section */}
          <div className="mt-6">
            {/* Results header with selection controls */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-700">
                  Znaleziono: <span className="font-semibold">{totalOffers}</span> ofert
                </span>
                {selectedOfferIds.length > 0 && (
                  <span className="text-sm text-blue-600">
                    Wybrano: <span className="font-semibold">{selectedOfferIds.length}</span> ofert
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {/* Page size selector */}
                <select
                  value={filters.pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={25}>25 na stronę</option>
                  <option value={50}>50 na stronę</option>
                  <option value={100}>100 na stronę</option>
                </select>

                {/* Select all/none button */}
                {currentOffers.length > 0 && (
                  <button
                    onClick={handleToggleAll}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    {isAllCurrentPageSelected ? 'Odznacz wszystkie' : 'Zaznacz wszystkie'}
                  </button>
                )}
              </div>
            </div>

            {/* Loading state */}
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Ładowanie ofert...</p>
                </div>
              </div>
            )}

            {/* Error state */}
            {error && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center text-red-600">
                  <p className="text-sm">Wystąpił błąd podczas ładowania ofert</p>
                  <p className="text-xs mt-1">{error instanceof Error ? error.message : String(error)}</p>
                </div>
              </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && currentOffers.length === 0 && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center text-gray-500">
                  <p className="text-sm">Brak ofert spełniających kryteria wyszukiwania</p>
                  <p className="text-xs mt-1">Spróbuj zmienić filtry lub wyczyścić je</p>
                </div>
              </div>
            )}

            {/* Offers table */}
            {!isLoading && !error && currentOffers.length > 0 && (
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <div className="max-h-96 overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="w-12 p-3 text-left border-b border-gray-300">
                          <input
                            ref={selectAllCheckboxRef}
                            type="checkbox"
                            checked={isAllCurrentPageSelected}
                            onChange={handleToggleAll}
                            className="w-4 h-4 cursor-pointer"
                          />
                        </th>
                        <th className="w-16 p-3 text-center border-b border-gray-300 font-semibold text-gray-700">
                          Zdjęcie
                        </th>
                        <th className="p-3 text-left border-b border-gray-300 font-semibold text-gray-700">
                          Nazwa oferty
                        </th>
                        <th className="p-3 text-left border-b border-gray-300 font-semibold text-gray-700">
                          ID
                        </th>
                        <th className="p-3 text-right border-b border-gray-300 font-semibold text-gray-700">
                          Cena
                        </th>
                        <th className="p-3 text-center border-b border-gray-300 font-semibold text-gray-700">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentOffers.map((offer) => (
                        <tr
                          key={offer.id}
                          className={`border-t border-gray-200 cursor-pointer hover:bg-gray-50 transition ${
                            selectedOffers.has(offer.id) ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => toggleOffer(offer.id)}
                        >
                          <td className="p-3">
                            <input
                              type="checkbox"
                              checked={selectedOffers.has(offer.id)}
                              onChange={() => toggleOffer(offer.id)}
                              className="w-4 h-4 cursor-pointer"
                            />
                          </td>
                          <td className="p-3 text-center">
                            {offer.image_url ? (
                              <div className="w-12 h-12 rounded-md overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center">
                                <img
                                  src={offer.image_url}
                                  alt={offer.name}
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    // Hide broken images gracefully
                                    e.currentTarget.style.display = 'none';
                                  }}
                                />
                              </div>
                            ) : (
                              <div className="w-12 h-12 rounded-md border border-gray-200 bg-gray-100 flex items-center justify-center">
                                <div className="w-6 h-6 bg-gray-300 rounded"></div>
                              </div>
                            )}
                          </td>
                          <td className="p-3">
                            <div className="max-w-md truncate" title={offer.name}>
                              {offer.name}
                            </div>
                          </td>
                          <td className="p-3 text-gray-500 text-sm font-mono">
                            <a
                              href={`https://allegro.pl/oferta/${offer.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 hover:underline"
                              onClick={(e) => e.stopPropagation()} // Prevent row selection when clicking link
                            >
                              {offer.id}
                            </a>
                          </td>
                          <td className="p-3 text-right font-medium">
                            {offer.price ? `${offer.price} PLN` : '-'}
                          </td>
                          <td className="p-3 text-center">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              offer.status === 'ACTIVE' 
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {offer.status === 'ACTIVE' ? 'Aktywna' : offer.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Pagination */}
            {!isLoading && !error && totalOffers > 0 && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-700">
                  {totalPages > 1 ? (
                    <>Strona {currentPage} z {totalPages} • </>
                  ) : null}
                  Znaleziono: <span className="font-semibold">{totalOffers} ofert</span>
                  {totalPages > 1 ? <> • Wyświetlanych: {currentOffers.length}</> : null}
                </div>
                
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => goToPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="p-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    
                    {/* Page numbers */}
                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i
                        return (
                          <button
                            key={pageNum}
                            onClick={() => goToPage(pageNum)}
                            className={`px-3 py-1 text-sm border rounded-md transition-colors ${
                              pageNum === currentPage
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        )
                      })}
                    </div>
                    
                    <button
                      onClick={() => goToPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="p-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200 mt-6">
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600">
                {selectedOfferIds.length > 0 ? (
                  <span>
                    Wybrano <span className="font-semibold">{selectedOfferIds.length}</span> ofert
                  </span>
                ) : (
                  <span>Nie wybrano żadnych ofert</span>
                )}
              </div>
              
              {selectedOfferIds.length > 0 && (
                <button
                  onClick={clearSelection}
                  className="px-3 py-1 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Wyczyść wszystko
                </button>
              )}
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              >
                Anuluj
              </button>
              <button
                onClick={handleConfirm}
                disabled={selectedOfferIds.length === 0}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Check className="w-4 h-4" />
                Potwierdź wybór ({selectedOfferIds.length})
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
