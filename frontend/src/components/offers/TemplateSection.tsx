import { useState } from 'react'
import { useAccountImages } from '../../hooks/shared/accounts'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'

interface Section {
  id: string
  type: 'TXT' | 'IMG' | 'IMG,TXT' | 'TXT,IMG' | 'IMG,IMG'
  values: Record<string, any>
}

interface TemplateSectionProps {
  section: Section
  index: number
  accountId?: number
  onUpdate: (values: Record<string, any>) => void
  onRemove: () => void
  validationErrors?: string[]
}

export default function TemplateSection({ section, index, accountId, onUpdate, onRemove, validationErrors = [] }: TemplateSectionProps) {
  // Fetch account images for the selected account
  const { data: accountImages } = useAccountImages(accountId || 0);
  
  // Set up sortable functionality
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };
  const updateValue = (key: string, value: string) => {
    onUpdate({
      ...section.values,
      [key]: value
    })
  }

  const applyFormatting = (textKey: string, tag: string) => {
    const textElement = document.getElementById(`${section.id}-${textKey}`) as HTMLTextAreaElement
    if (!textElement) return

    const start = textElement.selectionStart
    const end = textElement.selectionEnd
    const selectedText = textElement.value.substring(start, end)
    
    if (!selectedText) return

    let formattedText = ''
    switch (tag) {
      case 'h1':
        formattedText = `<h1>${selectedText}</h1>`
        break
      case 'h2':
        formattedText = `<h2>${selectedText}</h2>`
        break
      case 'p':
        formattedText = `<p>${selectedText}</p>`
        break
      case 'b':
        formattedText = `<b>${selectedText}</b>`
        break
      case 'ul':
        const ulLines = selectedText.split('\n').filter(line => line.trim())
        formattedText = '<ul>\n' + ulLines.map(line => `<li>${line}</li>`).join('\n') + '\n</ul>'
        break
      case 'ol':
        const olLines = selectedText.split('\n').filter(line => line.trim())
        formattedText = '<ol>\n' + olLines.map(line => `<li>${line}</li>`).join('\n') + '\n</ol>'
        break
      case 'org':
        formattedText = `[org>${selectedText}[<org]`
        break
      default:
        return
    }

    const newValue = textElement.value.substring(0, start) + formattedText + textElement.value.substring(end)
    updateValue(textKey, newValue)
    
    // Restore cursor position after the formatting
    setTimeout(() => {
      const newCursorPosition = start + formattedText.length
      textElement.focus()
      textElement.setSelectionRange(newCursorPosition, newCursorPosition)
    }, 10)
  }

  const renderImageSelector = (key: string, label: string) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}:</label>
      <select
        value={section.values[key] || ''}
        onChange={(e) => updateValue(key, e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
      >
        <option value="">Wybierz obraz</option>
        
        {/* Offer images (Aukcja:1-16) */}
        {Array.from({ length: 16 }, (_, i) => (
          <option key={i} value={`Aukcja:${i + 1}`}>Aukcja:{i + 1}</option>
        ))}
        
        {/* Account uploaded images */}
        {accountImages && accountImages.length > 0 && (
          <>
            <option disabled>─── Uploaded Images ───</option>
            {accountImages.map((image) => (
              <option key={image.id} value={image.url}>
                {image.original_filename}
              </option>
            ))}
          </>
        )}
      </select>
    </div>
  )

  const renderFrameSelector = (key: string, label: string) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}:</label>
      <select
        value={section.values[key] || 'No frame'}
        onChange={(e) => updateValue(key, e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
      >
        <option value="No frame">No frame</option>
        
        {/* Only account uploaded images can be used as frames */}
        {accountImages && accountImages.length > 0 && 
          accountImages.map((image) => (
            <option key={image.id} value={image.url}>
              {image.original_filename}
            </option>
          ))
        }
      </select>
    </div>
  )

  const renderTextEditor = (key: string, label: string) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}:</label>
      <textarea
        id={`${section.id}-${key}`}
        value={section.values[key] || ''}
        onChange={(e) => updateValue(key, e.target.value)}
        className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
        placeholder="Wprowadź tekst..."
      />
      
      {/* Formatting Toolbar */}
      <div className="flex flex-wrap gap-1">
        <button
          type="button"
          onClick={() => applyFormatting(key, 'h1')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Nagłówek 1
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'h2')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Nagłówek 2
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'p')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Tekst
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'b')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          B
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'ul')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          •
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'ol')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          1.
        </button>
        <button
          type="button"
          onClick={() => applyFormatting(key, 'org')}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Zostaw
        </button>
      </div>
    </div>
  )

  const renderSectionContent = () => {
    switch (section.type) {
      case 'TXT':
        return (
          <div className="space-y-4">
            {renderTextEditor('text', 'Tekst')}
          </div>
        )

      case 'IMG':
        return (
          <div className="grid grid-cols-2 gap-4">
            {renderImageSelector('image', 'Obraz')}
            {renderFrameSelector('frame', 'Ramka')}
          </div>
        )

      case 'IMG,TXT':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="space-y-4">
              {renderImageSelector('image', 'Obraz')}
              {renderFrameSelector('frame', 'Ramka')}
            </div>
            <div className="lg:col-span-2">
              {renderTextEditor('text', 'Tekst')}
            </div>
          </div>
        )

      case 'TXT,IMG':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              {renderTextEditor('text', 'Tekst')}
            </div>
            <div className="space-y-4">
              {renderImageSelector('image', 'Obraz')}
              {renderFrameSelector('frame', 'Ramka')}
            </div>
          </div>
        )

      case 'IMG,IMG':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-700">Obraz 1:</h4>
              {renderImageSelector('image1', 'Obraz 1')}
              {renderFrameSelector('frame1', 'Ramka 1')}
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-700">Obraz 2:</h4>
              {renderImageSelector('image2', 'Obraz 2')}
              {renderFrameSelector('frame2', 'Ramka 2')}
            </div>
          </div>
        )

      default:
        return <div>Nieznany typ sekcji</div>
    }
  }

  return (
    <div 
      ref={setNodeRef} 
      style={style}
      className={`border rounded-lg p-4 transition-shadow ${
        isDragging 
          ? 'shadow-lg opacity-50 border-blue-300 bg-blue-50' 
          : validationErrors.length > 0 
            ? 'border-red-300 bg-red-50' 
            : 'border-gray-200 bg-gray-50'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center flex-1">
          {/* Drag Handle */}
          <button
            {...attributes}
            {...listeners}
            className="mr-3 p-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
            title="Przeciągnij, aby zmienić kolejność"
          >
            <GripVertical className="h-5 w-5" />
          </button>
          
          <div className="flex-1">
            <h3 className={`text-lg font-medium ${validationErrors.length > 0 ? 'text-red-900' : 'text-gray-900'}`}>
              Sekcja {index + 1} - {section.type}
            </h3>
            {validationErrors.length > 0 && (
              <div className="mt-2 space-y-1">
                {validationErrors.map((error, errorIndex) => (
                  <div key={errorIndex} className="flex items-center text-sm text-red-700">
                    <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    {error}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <button
          onClick={onRemove}
          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
        >
          X
        </button>
      </div>
      
      {renderSectionContent()}
    </div>
  )
} 