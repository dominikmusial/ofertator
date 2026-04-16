import { useToastStore } from '../../store/toastStore'

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()
  
  if (toasts.length === 0) return null

  const getToastStyles = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-600 border-l-4 border-green-400'
      case 'error':
        return 'bg-red-600 border-l-4 border-red-400'
      case 'info':
        return 'bg-blue-600 border-l-4 border-blue-400'
      default:
        return 'bg-gray-600 border-l-4 border-gray-400'
    }
  }

  const getToastIcon = (type: string) => {
    switch (type) {
      case 'success':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        )
      case 'error':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        )
      case 'info':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="fixed top-4 right-4 space-y-2 z-50">
      {toasts.map(toast => (
        <div 
          key={toast.id} 
          className={`
            flex items-center justify-between px-4 py-3 rounded-lg shadow-lg text-white min-w-[300px] max-w-[400px]
            transform transition-all duration-300 ease-in-out
            ${getToastStyles(toast.type)}
          `}
        >
          <div className="flex items-center space-x-3">
            {/* Icon */}
            <div className="flex-shrink-0">
              {getToastIcon(toast.type)}
            </div>
            
            {/* Message */}
            <div className="text-sm font-medium leading-relaxed">
              {toast.message}
            </div>
          </div>
          
          {/* Close button */}
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 ml-3 text-white/80 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
} 