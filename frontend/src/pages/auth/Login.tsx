import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'
import { useFeatureFlags } from '../../hooks/shared/useFeatureFlags'

declare global {
  interface Window {
    google: any
  }
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  
  const { login, googleLogin, isLoading } = useAuthStore()
  const { addToast } = useToastStore()
  const { isRegistrationEnabled, isGoogleSSOEnabled, isLoading: flagsLoading } = useFeatureFlags()
  const navigate = useNavigate()
  const location = useLocation()
  
  const from = location.state?.from?.pathname || '/'

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await login(email, password)
      addToast('Zalogowano pomyślnie', 'success')
      navigate(from, { replace: true })
    } catch (error: any) {
      addToast(error.message, 'error')
      
      // Show link to resend verification if email is not verified
      if (error.message.includes('nie został zweryfikowany')) {
        setTimeout(() => {
          addToast(
            <div>
              Potrzebujesz nowy link weryfikacyjny?{' '}
              <Link 
                to="/auth/resend-verification" 
                className="font-medium underline text-white hover:text-blue-100"
              >
                Kliknij tutaj
              </Link>
            </div>,
            'info',
            7000
          )
        }, 1000)
      }
    }
  }

  const handleGoogleLogin = async (credentialResponse: any) => {
    try {
      await googleLogin(credentialResponse.credential)
      addToast('Zalogowano przez Google', 'success')
      navigate(from, { replace: true })
    } catch (error: any) {
      addToast(error.message, 'error')
    }
  }

  // Initialize Google Sign-In (only if enabled)
  useEffect(() => {
    // Wait for feature flags to load
    if (flagsLoading) return
    if (!isGoogleSSOEnabled()) return
    
    const initializeGoogleSignIn = () => {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
      
      if (!clientId) {
        console.error('VITE_GOOGLE_CLIENT_ID is not set!')
        addToast('Konfiguracja Google OAuth nie jest dostępna', 'error')
        return
      }
      
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleLogin,
          auto_select: false,
          cancel_on_tap_outside: true,
        })
        
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          { 
            theme: 'outline',
            size: 'large',
            width: '384',
            text: 'signin_with'
          }
        )
      }
    }

    // Load Google Script if not already loaded
    if (!window.google) {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.onload = initializeGoogleSignIn
      document.body.appendChild(script)
    } else {
      initializeGoogleSignIn()
    }
  }, [flagsLoading, isGoogleSSOEnabled])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Zaloguj się do Ofertator
          </h2>
          {!flagsLoading && isRegistrationEnabled() && (
            <p className="mt-2 text-center text-sm text-gray-600">
              Lub{' '}
              <Link
                to="/auth/register"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                utwórz nowe konto
              </Link>
            </p>
          )}
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleEmailLogin}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Adres email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Adres email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only">
                Hasło
              </label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Hasło"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Link
              to="/auth/forgot-password"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Zapomniałeś hasła?
            </Link>
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
                'Zaloguj się'
              )}
            </button>
          </div>

          {isGoogleSSOEnabled() && (
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-gray-50 text-gray-500">
                    Lub zaloguj się przez
                  </span>
                </div>
              </div>

              <div className="mt-6">
                <div 
                  id="google-signin-button" 
                  className="w-full flex justify-center"
                ></div>
                <p className="mt-2 text-xs text-gray-500 text-center">
                  Logowanie przez Google dostępne tylko dla pracowników @vsprint.pl
                </p>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  )
} 