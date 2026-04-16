import { X, Plus } from 'lucide-react'

interface StopSequencesEditorProps {
  sequences: string[]
  onChange: (sequences: string[]) => void
  maxSequences?: number
}

export default function StopSequencesEditor({
  sequences,
  onChange,
  maxSequences = 4,
}: StopSequencesEditorProps) {
  const handleAdd = () => {
    if (sequences.length < maxSequences) {
      onChange([...sequences, ''])
    }
  }

  const handleRemove = (index: number) => {
    onChange(sequences.filter((_, i) => i !== index))
  }

  const handleChange = (index: number, value: string) => {
    const newSequences = [...sequences]
    newSequences[index] = value
    onChange(newSequences)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Sekwencje stop
          <span className="ml-2 text-xs text-gray-500">(opcjonalne, max {maxSequences})</span>
        </label>
        <button
          type="button"
          onClick={handleAdd}
          disabled={sequences.length >= maxSequences}
          className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-3 h-3 mr-1" />
          Dodaj
        </button>
      </div>

      {sequences.length === 0 ? (
        <div className="text-sm text-gray-500 italic py-2">
          Brak zdefiniowanych sekwencji stop. Kliknij "Dodaj" aby utworzyć.
        </div>
      ) : (
        <div className="space-y-2">
          {sequences.map((sequence, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={sequence}
                onChange={(e) => handleChange(index, e.target.value)}
                placeholder={`Sekwencja ${index + 1}`}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="inline-flex items-center justify-center w-8 h-8 text-red-600 bg-red-50 rounded hover:bg-red-100"
                title="Usuń sekwencję"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-500 mt-2">
        Sekwencje stop to ciągi tekstowe, które powodują zatrzymanie generowania przez AI. Pozostaw puste jeśli nie są potrzebne.
      </p>
    </div>
  )
}

