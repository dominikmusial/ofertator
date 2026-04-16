import { useState, useEffect } from 'react'
import { useImageProcess, ImageOperation } from '../../hooks/shared/images'
import { useToastStore } from '../../store/toastStore'
import Modal from '../ui/Modal'

interface ImageProcessorProps {
  imageUrl: string
  isOpen: boolean
  onClose: () => void
  onProcessed: () => void
}

export default function ImageProcessor({ imageUrl, isOpen, onClose, onProcessed }: ImageProcessorProps) {
  const [selectedOperations, setSelectedOperations] = useState<ImageOperation[]>([])
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [step, setStep] = useState<'select' | 'preview' | 'processing'>('select')
  
  const processMutation = useImageProcess()
  const { addToast } = useToastStore()

  useEffect(() => {
    if (isOpen) {
      setSelectedOperations([])
      setPreviewUrl(null)
      setStep('select')
    }
  }, [isOpen])

  const operations = [
    {
      id: 'remove_background' as ImageOperation,
      name: 'Usuń tło',
      description: 'Automatycznie usuwa tło z obrazu',
      icon: '🎯',
      intensive: true
    },
    {
      id: 'crop_to_square' as ImageOperation,
      name: 'Kadruj do kwadratu',
      description: 'Przycina obraz do kwadratu (1:1)',
      icon: '⏹️',
      intensive: false
    },
    {
      id: 'add_blur_effect' as ImageOperation,
      name: 'Dodaj rozmyte tło',
      description: 'Dodaje rozmyte tło do obrazu',
      icon: '🌫️',
      intensive: false
    }
  ]

  const handleOperationToggle = (operationId: ImageOperation) => {
    setSelectedOperations(prev => 
      prev.includes(operationId)
        ? prev.filter(op => op !== operationId)
        : [...prev, operationId]
    )
  }

  const handlePreview = async () => {
    if (selectedOperations.length === 0) {
      addToast('Wybierz przynajmniej jedną operację', 'error')
      return
    }

    setStep('processing')
    
    try {
      const result = await processMutation.mutateAsync({
        image_url: imageUrl,
        operations: selectedOperations
      })
      
      setPreviewUrl(result.url)
      setStep('preview')
    } catch (error) {
      addToast('Błąd podczas przetwarzania obrazu', 'error')
      setStep('select')
    }
  }

  const handleConfirm = () => {
    onProcessed()
    onClose()
    addToast('Obraz został przetworzony i zapisany', 'success')
  }

  const handleReset = () => {
    setStep('select')
    setPreviewUrl(null)
    setSelectedOperations([])
  }

  if (!isOpen) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Przetwarzanie obrazu">
      <div className="space-y-6">
        {/* Oryginalny obraz */}
        <div className="text-center">
          <img
            src={imageUrl}
            alt="Oryginalny obraz"
            className="mx-auto max-w-full max-h-64 rounded-lg border"
          />
          <p className="text-sm text-gray-500 mt-2">Oryginalny obraz</p>
        </div>

        {step === 'select' && (
          <>
            {/* Wybór operacji */}
            <div className="space-y-3">
              <h3 className="font-medium">Wybierz operacje do wykonania:</h3>
              {operations.map((operation) => (
                <div
                  key={operation.id}
                  className={`
                    border rounded-lg p-4 cursor-pointer transition-all
                    ${selectedOperations.includes(operation.id)
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                  `}
                  onClick={() => handleOperationToggle(operation.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">{operation.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{operation.name}</h4>
                        {operation.intensive && (
                          <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                            Może potrwać dłużej
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{operation.description}</p>
                    </div>
                    <div className={`
                      w-5 h-5 rounded-full border-2 flex items-center justify-center
                      ${selectedOperations.includes(operation.id)
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                      }
                    `}>
                      {selectedOperations.includes(operation.id) && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Przyciski akcji */}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Anuluj
              </button>
              <button
                onClick={handlePreview}
                disabled={selectedOperations.length === 0}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Przetwórz obraz
              </button>
            </div>
          </>
        )}

        {step === 'processing' && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Przetwarzanie obrazu...</p>
            <p className="text-sm text-gray-500 mt-2">To może potrwać kilka sekund</p>
          </div>
        )}

        {step === 'preview' && previewUrl && (
          <>
            {/* Porównanie before/after */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <img
                  src={imageUrl}
                  alt="Przed"
                  className="w-full max-h-48 object-contain rounded-lg border"
                />
                <p className="text-sm text-gray-500 mt-2">Przed</p>
              </div>
              <div className="text-center">
                <img
                  src={previewUrl}
                  alt="Po"
                  className="w-full max-h-48 object-contain rounded-lg border"
                />
                <p className="text-sm text-gray-500 mt-2">Po</p>
              </div>
            </div>

            {/* Wykonane operacje */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-2">Wykonane operacje:</h4>
              <div className="flex flex-wrap gap-2">
                {selectedOperations.map(op => {
                  const operation = operations.find(o => o.id === op)
                  return (
                    <span key={op} className="bg-white px-3 py-1 rounded-full text-sm border">
                      {operation?.icon} {operation?.name}
                    </span>
                  )
                })}
              </div>
            </div>

            {/* Przyciski akcji */}
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Spróbuj ponownie
              </button>
              <button
                onClick={handleConfirm}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Potwierdź i zapisz
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  )
} 