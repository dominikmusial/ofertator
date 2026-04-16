import { useState, useEffect } from 'react'
import { Info, RotateCcw } from 'lucide-react'
import StopSequencesEditor from './StopSequencesEditor'
import type { AIPromptConfig } from '../../hooks/shared/ai'

interface AIConfigFormProps {
  provider: 'anthropic' | 'gemini'
  config: AIPromptConfig
  onSave: (config: any) => void
  isSaving: boolean
}

export default function AIConfigForm({
  provider,
  config,
  onSave,
  isSaving,
}: AIConfigFormProps) {
  // Local state for form values
  const [formValues, setFormValues] = useState(config)
  const [hasChanges, setHasChanges] = useState(false)
  
  // Track which optional params are enabled
  const [enabledParams, setEnabledParams] = useState({
    temperature: config.temperature !== null && config.temperature !== undefined,
    top_p: config.top_p !== null && config.top_p !== undefined,
    top_k: config.top_k !== null && config.top_k !== undefined && config.top_k !== '',
  })

  // Update form values when config changes
  useEffect(() => {
    setFormValues(config)
    setHasChanges(false)
    setEnabledParams({
      temperature: config.temperature !== null && config.temperature !== undefined,
      top_p: config.top_p !== null && config.top_p !== undefined,
      top_k: config.top_k !== null && config.top_k !== undefined && config.top_k !== '',
    })
  }, [config])

  // Track changes
  useEffect(() => {
    setHasChanges(JSON.stringify(formValues) !== JSON.stringify(config))
  }, [formValues, config])

  const handleChange = (field: string, value: any) => {
    setFormValues((prev: any) => ({ ...prev, [field]: value }))
  }
  
  const toggleParam = (param: 'temperature' | 'top_p' | 'top_k') => {
    const newEnabled = !enabledParams[param]
    setEnabledParams((prev) => ({ ...prev, [param]: newEnabled }))
    
    if (!newEnabled) {
      // Disable: set to null
      handleChange(param, null)
    } else {
      // Enable: set to default value
      const defaults = {
        temperature: provider === 'gemini' ? 1.0 : 0.5,
        top_p: 0.9,
        top_k: 40,
      }
      handleChange(param, defaults[param])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formValues)
  }

  const handleReset = () => {
    setFormValues(config)
    setHasChanges(false)
  }

  // Get temperature range based on provider
  const tempMax = provider === 'gemini' ? 2.0 : 1.0
  const tempStep = 0.1

  // Tooltip helper
  const Tooltip = ({ text }: { text: string }) => (
    <div className="group relative inline-block ml-1">
      <Info className="w-4 h-4 text-gray-400 cursor-help" />
      <div className="hidden group-hover:block absolute z-10 w-64 p-2 text-xs text-white bg-gray-900 rounded shadow-lg -top-2 left-6">
        {text}
      </div>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Prompt */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Prompt
          <Tooltip text="Główne instrukcje dla AI do optymalizacji tytułów produktów." />
        </label>
        <textarea
          value={formValues.prompt}
          onChange={(e) => handleChange('prompt', e.target.value)}
          rows={15}
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
          placeholder="Wprowadź prompt do optymalizacji tytułów..."
        />
      </div>

      {/* API Parameters */}
      <div className="border-t pt-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Parametry API</h3>
        
        {/* Anthropic Temperature/Top_P Warning */}
        {provider === 'anthropic' && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-md p-3">
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-amber-800">
                  <strong>Uwaga Anthropic:</strong> API Anthropic nie pozwala na jednoczesne użycie <code className="bg-amber-100 px-1 rounded">temperature</code> i <code className="bg-amber-100 px-1 rounded">top_p</code>.
                </p>
                {enabledParams.temperature && enabledParams.top_p && (
                  <p className="text-sm text-amber-800 mt-1 font-medium">
                    ⚠️ Masz włączone OBA parametry - system użyje tylko <strong>temperature</strong>.
                  </p>
                )}
                <p className="text-xs text-amber-700 mt-1">
                  Zalecenie: Wyłącz jeden z parametrów używając checkboxa obok nazwy.
                </p>
              </div>
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Temperature */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <input
                type="checkbox"
                checked={enabledParams.temperature}
                onChange={() => toggleParam('temperature')}
                className="mr-2 h-4 w-4 text-blue-600 rounded"
              />
              Temperature
              <Tooltip text={`Kontroluje losowość. Niższa = bardziej deterministyczna. Zakres: 0.0-${tempMax}`} />
              {!enabledParams.temperature && (
                <span className="ml-2 text-xs text-gray-500 italic">(wyłączone)</span>
              )}
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="0"
                max={tempMax}
                step={tempStep}
                value={enabledParams.temperature ? formValues.temperature : 0}
                onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                disabled={!enabledParams.temperature}
                className="flex-1 disabled:opacity-40 disabled:cursor-not-allowed"
              />
              <input
                type="number"
                min="0"
                max={tempMax}
                step={tempStep}
                value={enabledParams.temperature ? formValues.temperature : ''}
                onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                disabled={!enabledParams.temperature}
                className="w-20 px-2 py-1 text-sm border border-gray-300 rounded disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Max Output Tokens */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              Maksymalna liczba tokenów wyjściowych
              <Tooltip text="Maksymalna liczba tokenów w odpowiedzi. Wyższe wartości pozwalają na dłuższe odpowiedzi." />
            </label>
            <input
              type="number"
              min="1"
              max={provider === 'gemini' ? 8192 : 4096}
              value={formValues.max_output_tokens}
              onChange={(e) => handleChange('max_output_tokens', parseInt(e.target.value))}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Top P */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <input
                type="checkbox"
                checked={enabledParams.top_p}
                onChange={() => toggleParam('top_p')}
                className="mr-2 h-4 w-4 text-blue-600 rounded"
              />
              Top P
              <Tooltip text="Próg próbkowania jądrowego. Kontroluje różnorodność. Zakres: 0.0-1.0" />
              {!enabledParams.top_p && (
                <span className="ml-2 text-xs text-gray-500 italic">(wyłączone)</span>
              )}
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={enabledParams.top_p ? formValues.top_p : 0}
                onChange={(e) => handleChange('top_p', parseFloat(e.target.value))}
                disabled={!enabledParams.top_p}
                className="flex-1 disabled:opacity-40 disabled:cursor-not-allowed"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={enabledParams.top_p ? formValues.top_p : ''}
                onChange={(e) => handleChange('top_p', parseFloat(e.target.value))}
                disabled={!enabledParams.top_p}
                className="w-20 px-2 py-1 text-sm border border-gray-300 rounded disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Top K */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <input
                type="checkbox"
                checked={enabledParams.top_k}
                onChange={() => toggleParam('top_k')}
                className="mr-2 h-4 w-4 text-blue-600 rounded"
              />
              Top K (opcjonalne)
              <Tooltip text="Ogranicza wybór tokenów do K najlepszych kandydatów." />
              {!enabledParams.top_k && (
                <span className="ml-2 text-xs text-gray-500 italic">(wyłączone)</span>
              )}
            </label>
            <input
              type="number"
              min="1"
              value={enabledParams.top_k ? (formValues.top_k || '') : ''}
              onChange={(e) => handleChange('top_k', e.target.value ? parseInt(e.target.value) : null)}
              disabled={!enabledParams.top_k}
              placeholder={enabledParams.top_k ? "np. 40" : "Wyłączone"}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {/* Stop Sequences */}
      <div className="border-t pt-6">
        <StopSequencesEditor
          sequences={formValues.stop_sequences || []}
          onChange={(sequences) => handleChange('stop_sequences', sequences)}
          maxSequences={4}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between border-t pt-6">
        <button
          type="button"
          onClick={handleReset}
          disabled={!hasChanges || isSaving}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Resetuj
        </button>

        <button
          type="submit"
          disabled={!hasChanges || isSaving}
          className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Zapisywanie...' : 'Zapisz zmiany'}
        </button>
      </div>

      {hasChanges && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <p className="text-sm text-yellow-800">
            Masz niezapisane zmiany. Kliknij "Zapisz zmiany" aby je zastosować.
          </p>
        </div>
      )}
    </form>
  )
}

