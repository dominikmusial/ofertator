import React from 'react'
import { Link } from 'react-router-dom'
import { Package, TrendingUp } from 'lucide-react'

export const GettingStarted: React.FC = () => {
  return (
    <Link
      to="/accounts"
      className="block group relative bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden"
    >
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-32 h-32 bg-white opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity"></div>
      
      <div className="relative flex items-center justify-between z-10">
        <div className="flex items-center gap-6">
          <div className="bg-white/20 rounded-xl p-4 backdrop-blur-sm">
            <Package className="h-8 w-8 text-white" />
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-white">
              Połącz swoje pierwsze konto
            </h3>
            <p className="text-blue-100 max-w-lg">
              Aby rozpocząć pracę z Ofertatorem, dodaj integrację z wybranym marketplace.
              System automatycznie pobierze Twoje oferty.
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold shadow-sm group-hover:bg-blue-50 transition-colors">
          Rozpocznij
          <TrendingUp className="h-4 w-4" />
        </div>
      </div>
    </Link>
  )
}
