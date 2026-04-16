import { ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface Props {
  open?: boolean
  isOpen?: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
}

export default function Modal({ open, isOpen, onClose, title, children, className = "" }: Props) {
  const isModalOpen = isOpen ?? open ?? false
  
  if (!isModalOpen) return null
  
  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50" onClick={onClose}>
      <div 
        className={`bg-white rounded-lg shadow-lg w-full max-h-[90vh] overflow-hidden ${className || 'max-w-2xl'}`} 
        onClick={e => e.stopPropagation()}
      >
        {title && (
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">{title}</h2>
          </div>
        )}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-4rem)]">
          {children}
        </div>
      </div>
    </div>
  )
  
  return createPortal(modalContent, document.body)
} 