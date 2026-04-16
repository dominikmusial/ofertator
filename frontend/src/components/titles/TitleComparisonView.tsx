import { useState } from 'react'
import { Check, X, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, ArrowRight, Info } from 'lucide-react'
import type { OptimizedTitleResult } from '../../hooks/shared/ai'

interface TitleComparisonViewProps {
  results: OptimizedTitleResult[]
  onAcceptAll: () => void
  onRejectAll: () => void
  onAcceptSingle: (offerId: string) => void
  onRejectSingle: (offerId: string) => void
  onCancel: () => void
  acceptedOfferIds: Set<string>
}

export default function TitleComparisonView({
  results,
  onAcceptAll,
  onRejectAll,
  onAcceptSingle,
  onRejectSingle,
  onCancel,
  acceptedOfferIds,
}: TitleComparisonViewProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  
  const toggleExpanded = (offerId: string) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(offerId)) {
      newExpanded.delete(offerId)
    } else {
      newExpanded.add(offerId)
    }
    setExpandedIds(newExpanded)
  }
  
  const successfulResults = results.filter(r => r.success)
  const failedResults = results.filter(r => !r.success)
  const acceptedCount = successfulResults.filter(r => acceptedOfferIds.has(r.offer_id)).length
  
  return (
    <div className="mt-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Compact Header */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-sm font-semibold text-gray-900">Wyniki optymalizacji AI</h3>
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-green-700 font-medium">✓ {acceptedCount}/{successfulResults.length}</span>
              <span className="text-gray-600">Sukces: {results.filter(r => r.success).length}</span>
              {results.filter(r => !r.success).length > 0 && (
                <span className="text-red-600">Błędy: {results.filter(r => !r.success).length}</span>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={onAcceptAll}
              className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors flex items-center space-x-1"
            >
              <CheckCircle2 className="w-3 h-3" />
              <span>Wszystkie</span>
            </button>
            <button
              onClick={onRejectAll}
              className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded hover:bg-gray-300 transition-colors flex items-center space-x-1"
            >
              <X className="w-3 h-3" />
              <span>Żadne</span>
            </button>
            <button
              onClick={onCancel}
              className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200 transition-colors flex items-center space-x-1"
              title="Anuluj optymalizację AI i zamknij"
            >
              <X className="w-3 h-3" />
              <span>Anuluj</span>
            </button>
          </div>
        </div>
      </div>
      
      {/* Compact Results List */}
      <div className="max-h-[400px] overflow-y-auto">
        {successfulResults.map((result) => {
          const isExpanded = expandedIds.has(result.offer_id)
          const isAccepted = acceptedOfferIds.has(result.offer_id)
          
          return (
            <div
              key={result.offer_id}
              className={`border-b border-gray-100 last:border-b-0 transition-colors ${
                isAccepted ? 'bg-green-50' : 'bg-white hover:bg-gray-50'
              }`}
            >
              <div className="px-4 py-2">
                {/* Compact single-row layout */}
                <div className="flex items-start space-x-3">
                  {/* Accept/Reject button */}
                  <button
                    onClick={() => isAccepted ? onRejectSingle(result.offer_id) : onAcceptSingle(result.offer_id)}
                    className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors flex-shrink-0 mt-1 ${
                      isAccepted 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-gray-200 text-gray-600 hover:bg-green-100 hover:text-green-600'
                    }`}
                    title={isAccepted ? 'Odrzuć' : 'Zaakceptuj'}
                  >
                    {isAccepted ? <Check className="w-3 h-3" /> : <Check className="w-3 h-3" />}
                  </button>
                  
                  {/* Content area */}
                  <div className="flex-1 min-w-0">
                    {/* Offer ID and character counts */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-gray-500 font-mono">
                        ID: {result.offer_id}
                      </div>
                      <div className="flex items-center space-x-2 text-xs">
                        <span className="text-gray-500">{result.current_title.length} → </span>
                        <span className={result.character_count > 75 ? 'text-red-600 font-bold' : 'text-green-600'}>
                          {result.character_count} znaków {result.character_count > 75 ? '⚠️' : '✓'}
                        </span>
                        {result.analysis && (
                          <button
                            onClick={() => toggleExpanded(result.offer_id)}
                            className="p-0.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
                            title={isExpanded ? 'Ukryj analizę' : 'Pokaż analizę'}
                          >
                            <Info className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {/* Titles comparison - horizontal layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 text-sm">
                      {/* Original title */}
                      <div className="bg-gray-50 p-2 rounded border">
                        <div className="text-xs font-medium text-gray-600 mb-1">Aktualny:</div>
                        <div className="text-gray-800 break-words leading-tight">
                          {result.current_title}
                        </div>
                      </div>
                      
                      {/* Optimized title */}
                      <div className={`p-2 rounded border ${
                        result.character_count > 75
                          ? 'bg-red-50 border-red-200'
                          : 'bg-green-50 border-green-200'
                      }`}>
                        <div className="text-xs font-medium text-gray-600 mb-1">Zoptymalizowany:</div>
                        <div className={`break-words leading-tight ${
                          result.character_count > 75 ? 'text-red-800' : 'text-green-800'
                        }`}>
                          {result.optimized_title}
                        </div>
                      </div>
                    </div>
                    
                    {/* Expanded analysis */}
                    {isExpanded && result.analysis && (
                      <div className="mt-2 text-xs text-gray-700 bg-blue-50 p-2 rounded border border-blue-200">
                        <div className="font-medium text-blue-800 mb-1">Analiza AI:</div>
                        <div className="whitespace-pre-wrap">{result.analysis}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
        
        {/* Compact Failed results */}
        {failedResults.length > 0 && (
          <div className="bg-red-50 border-t border-red-200">
            <div className="px-4 py-2">
              <div className="flex items-center space-x-2 mb-1">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <h4 className="text-sm font-medium text-red-800">Błędy optymalizacji ({failedResults.length}):</h4>
              </div>
              <div className="space-y-1">
                {failedResults.map((result) => (
                  <div key={result.offer_id} className="text-xs">
                    <span className="font-medium text-red-700">{result.offer_id}:</span>
                    <span className="text-red-600 ml-1">{result.error}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

