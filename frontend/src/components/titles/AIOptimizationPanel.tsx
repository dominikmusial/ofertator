import { useState } from 'react'
import { ChevronDown, ChevronUp, Sparkles, Info, AlertTriangle, Settings } from 'lucide-react'
import { Link } from 'react-router-dom'

interface AIConfigStatus {
  can_use_default: boolean
  has_config: boolean
  is_active: boolean
}

interface AIOptimizationPanelProps {
  onOptimize: () => void
  isProcessing: boolean
  disabled: boolean
  aiStatus?: AIConfigStatus | null
  includeOfferParameters: boolean
  onIncludeOfferParametersChange: (value: boolean) => void
  titleCount: number
}

export default function AIOptimizationPanel({ 
  onOptimize, 
  isProcessing, 
  disabled, 
  aiStatus, 
  includeOfferParameters, 
  onIncludeOfferParametersChange, 
  titleCount 
}: AIOptimizationPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 p-4 mb-4">
      {/* Main content - compact layout */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Sparkles className="w-5 h-5 text-purple-600" />
          <div>
            <h3 className="text-lg font-semibold text-purple-900">
              AI Tytułomat
            </h3>
            <p className="text-sm text-purple-700 mt-0.5">
              Optymalizuj tytuły według zasad Allegro
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onOptimize}
            disabled={disabled || isProcessing}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isProcessing ? 'Optymalizuję...' : 'Optymalizuj z AI'}</span>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 text-purple-600 hover:bg-purple-100 rounded-lg transition-colors"
            title={isExpanded ? 'Zwiń szczegóły' : 'Pokaż szczegóły'}
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>
      
      {/* Expandable content */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* AI Configuration Warnings */}
          {aiStatus && !aiStatus.can_use_default && !aiStatus.has_config && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-amber-800 font-medium">Brak dostępu do AI</h3>
                  <p className="text-amber-700 text-sm mt-1">
                    Aby korzystać z optymalizacji tytułów AI (Tytułomat), musisz skonfigurować własny klucz API.
                    Bez konfiguracji AI, możesz nadal używać standardowych funkcji zarządzania tytułami.
                  </p>
                  <Link
                    to="/profile/ai-config"
                    className="inline-flex items-center mt-3 px-3 py-1.5 bg-amber-600 text-white text-sm rounded-md hover:bg-amber-700 transition-colors"
                  >
                    <Settings className="h-4 w-4 mr-1.5" />
                    Skonfiguruj AI
                  </Link>
                </div>
              </div>
            </div>
          )}

          {aiStatus && !aiStatus.can_use_default && aiStatus.has_config && !aiStatus.is_active && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-yellow-800 font-medium">Konfiguracja AI nieaktywna</h3>
                  <p className="text-yellow-700 text-sm mt-1">
                    Twoja konfiguracja AI została zdezaktywowana. Sprawdź ustawienia i klucz API.
                  </p>
                  <Link
                    to="/profile/ai-config"
                    className="inline-flex items-center mt-3 px-3 py-1.5 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors"
                  >
                    <Settings className="h-4 w-4 mr-1.5" />
                    Sprawdź konfigurację
                  </Link>
                </div>
              </div>
            </div>
          )}
          
          {/* Parameters options */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="text-green-800 font-medium mb-3">Opcje optymalizacji</h4>
            <div className="space-y-3">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeOfferParameters}
                  onChange={(e) => onIncludeOfferParametersChange(e.target.checked)}
                  className="mt-1 w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-green-800">
                    Uwzględnij parametry ofert z API Allegro
                  </div>
                  <div className="text-xs text-green-600 mt-1">
                    Pobierz parametry produktów (marka, stan, kolor itp.) i dodaj je do kontekstu AI dla lepszej optymalizacji tytułów.
                    {includeOfferParameters && (
                      <span className="block mt-1 font-medium text-orange-600">
                        ⚠️ Limit: 20 tytułów (zamiast 100) przy tej opcji
                      </span>
                    )}
                  </div>
                </div>
              </label>
              
              {/* Current limit warning */}
              {includeOfferParameters && titleCount > 20 && (
                <div className="bg-orange-50 border border-orange-200 rounded p-2">
                  <div className="text-sm text-orange-800">
                    <strong>Uwaga:</strong> Masz {titleCount} tytułów, ale limit z parametrami to 20. 
                    Usuń część tytułów lub wyłącz opcję parametrów.
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* How it works */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-blue-800 font-medium mb-2">Jak to działa?</h4>
                <p className="text-sm text-blue-700 mb-3">
                  AI przeanalizuje wprowadzone tytuły i zaproponuje zoptymalizowane wersje według zasad Allegro używając sprawdzonego promptu vSprint.
                  Po optymalizacji zobaczysz porównanie i będziesz mógł zaakceptować lub odrzucić każdą propozycję.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-blue-700">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <span>
                      Maksymalnie 50 tytułów na raz (20 z parametrami)
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <span>Sprawdzony prompt vSprint</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

