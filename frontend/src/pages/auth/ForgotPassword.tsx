import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const { forgotPassword, isLoading } = useAuthStore()
  const { addToast } = useToastStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim()) {
      addToast('Email jest wymagany', 'error')
      return
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      addToast('Nieprawidłowy format email', 'error')
      return
    }

    try {
      await forgotPassword(email)
      setIsSubmitted(true)
      addToast('Jeśli email istnieje, link resetujący został wysłany', 'success')
    } catch (error: any) {
      addToast(error.message, 'error')
    }
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              Email wysłany
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Jeśli konto z adresem{' '}
              <span className="font-medium">{email}</span> istnieje,{' '}
              wysłaliśmy link do resetowania hasła.
            </p>
            <p className="mt-4 text-sm text-gray-600">
              Sprawdź swoją skrzynkę email i kliknij w link resetujący.
            </p>
            <div className="mt-6">
              <Link
                to="/auth/login"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Wróć do logowania
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Resetuj hasło
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Wpisz swój adres email, a wyślemy Ci link do resetowania hasła
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Adres email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Wprowadź adres email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                'Wyślij link resetujący'
              )}
            </button>
          </div>

          <div className="text-center space-y-2">
            <Link
              to="/auth/login"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Wróć do logowania
            </Link>
            <div className="text-sm text-gray-500">
              Nie masz konta?{' '}
              <Link
                to="/auth/register"
                className="text-blue-600 hover:text-blue-500"
              >
                Zarejestruj się
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
} 