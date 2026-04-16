import { ReactNode, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'
import { usePermissionGuard } from '../../hooks/shared/auth'
import Sidebar from './Sidebar'
import ToastContainer from '../ui/ToastContainer'

interface Props {
  children: ReactNode
}

export default function MainLayout({ children }: Props) {
  const { user, logout } = useAuthStore()
  const { addToast } = useToastStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [showUserMenu, setShowUserMenu] = useState(false)

  // Refresh permissions on route navigation
  usePermissionGuard()

  const handleLogout = () => {
    logout()
    addToast('Wylogowano pomyślnie', 'success')
    navigate('/auth/login')
  }

  const getRoleDisplay = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator'
      default:
        return 'Użytkownik'
    }
  }

  const getPageTitle = (pathname: string) => {
    const routes: Record<string, string> = {
      '/': 'Dashboard',
      '/accounts': 'Integracje',
      // Old routes (backward compatibility)
      '/offer-editor': 'Edytor Ofert - Allegro',
      '/copy-offers': 'Kopiowanie Ofert - Allegro',
      '/promotions': 'Promocje - Allegro',
      '/price-scheduler': 'Harmonogram Cen - Allegro',
      '/create-offer': 'Wystawianie Ofert - Allegro',
      '/titles': 'Tytuły - Allegro',
      '/thumbnails': 'Miniatury - Allegro',
      '/replace-images': 'Podmiana Zdjęć - Allegro',
      '/disable-offers': 'Wyłączanie Ofert - Allegro',
      '/banner-images': 'Zdjęcia na Banerach - Allegro',
      '/product-cards': 'Karty Produktowe - Allegro',
      '/images': 'Dodawanie Grafik - Allegro',
      '/saved-images': 'Zapisane Zdjęcia - Allegro',
      // Allegro routes
      '/allegro/offer-editor': 'Edytor Ofert - Allegro',
      '/allegro/copy-offers': 'Kopiowanie Ofert - Allegro',
      '/allegro/promotions': 'Promocje - Allegro',
      '/allegro/price-scheduler': 'Harmonogram Cen - Allegro',
      '/allegro/create-offer': 'Wystawianie Ofert - Allegro',
      '/allegro/titles': 'Tytuły - Allegro',
      '/allegro/thumbnails': 'Miniatury - Allegro',
      '/allegro/replace-images': 'Podmiana Zdjęć - Allegro',
      '/allegro/disable-offers': 'Wyłączanie Ofert - Allegro',
      '/allegro/banner-images': 'Zdjęcia na Banerach - Allegro',
      '/allegro/product-cards': 'Karty Produktowe - Allegro',
      '/allegro/images': 'Dodawanie Grafik - Allegro',
      '/allegro/saved-images': 'Zapisane Zdjęcia - Allegro',
      // Decathlon routes
      '/decathlon/offer-editor': 'Edytor Ofert - Decathlon',
      '/decathlon/create-offer': 'Wystawianie Ofert - Decathlon',
      // Other routes
      '/profile': 'Profil Użytkownika',
      '/usage': 'Zużycie AI',
      '/team-analytics': 'Analityka Zespołu',
      '/admin/users': 'Zarządzanie użytkownikami',
      '/admin/ai-prompts': 'Konfiguracja AI'
    }

    return routes[pathname] || 'Ofertator'
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Content area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
          <div className="flex items-center space-x-4">
            <h1 className="text-lg font-semibold text-gray-900">
              {getPageTitle(location.pathname)}
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                  {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
                </div>
                <svg 
                  className="w-4 h-4 text-gray-400" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M19 9l-7 7-7-7" 
                  />
                </svg>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border">
                  <div className="px-4 py-2 text-sm text-gray-700 border-b">
                    <div className="font-medium">{user?.email}</div>
                    <div className="text-xs text-gray-500">{getRoleDisplay(user?.role || 'user')}</div>
                  </div>
                  
                  <Link
                    to="/profile"
                    onClick={() => setShowUserMenu(false)}
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Profil użytkownika
                  </Link>
                  
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Wyloguj się
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-8">{children}</main>
        <ToastContainer />
      </div>

      {/* Close user menu when clicking outside */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </div>
  )
} 