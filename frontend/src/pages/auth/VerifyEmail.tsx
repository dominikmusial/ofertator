import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'

export default function VerifyEmail() {
  const { token } = useParams<{ token: string }>()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const { verifyEmail } = useAuthStore()
  const { addToast } = useToastStore()
  const hasExecuted = useRef(false)

  useEffect(() => {
    const verify = async () => {
      if (!token || hasExecuted.current) {
        if (!token) setStatus('error')
        return
      }
      
      hasExecuted.current = true

      try {
        await verifyEmail(token)
        setStatus('success')
        addToast('Email został pomyślnie zweryfikowany!', 'success')
      } catch (error: any) {
        setStatus('error')
        addToast(error.message, 'error')
      }
    }

    verify()
  }, [token, verifyEmail, addToast])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Weryfikowanie email...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Proszę czekać, weryfikujemy Twój adres email.
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Email zweryfikowany!
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Twój email został zweryfikowany. Poczekaj na zatwierdzenie konta przez administratora - otrzymasz email z potwierdzeniem.
              </p>
              <div className="mt-6">
                <Link
                  to="/auth/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Przejdź do logowania
                </Link>
              </div>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Błąd weryfikacji
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Link weryfikacyjny jest nieprawidłowy lub wygasł.
              </p>
              <div className="mt-6 space-y-3">
                <Link
                  to="/auth/resend-verification"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Wyślij nowy link weryfikacyjny
                </Link>
                <div className="flex space-x-4 justify-center">
                  <Link
                    to="/auth/register"
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Zarejestruj się ponownie
                  </Link>
                  <span className="text-sm text-gray-400">|</span>
                  <Link
                    to="/auth/login"
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Wróć do logowania
                  </Link>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
} 