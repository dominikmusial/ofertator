/**
 * App - Main application component with dynamic routing
 * 
 * SOLID Principles:
 * - Single Responsibility: Manages routing and authentication flow
 * - Open/Closed: Add modules to registry, routes generated automatically
 * - Dependency Inversion: Routes generated from configuration (moduleRegistry)
 */

import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute'
import MainLayout from './components/layout/MainLayout'
import ToastContainer from './components/ui/ToastContainer'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import { FeatureFlagProvider, useFeatureFlags } from './contexts/FeatureFlagContext'
import { generateModuleRoutes, generateSpecialRoutes } from './config/routeGenerator'

// Auth pages (not in registry - always public)
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import VerifyEmail from './pages/auth/VerifyEmail'
import ResendVerification from './pages/auth/ResendVerification'
import ForgotPassword from './pages/auth/ForgotPassword'
import ResetPassword from './pages/auth/ResetPassword'
import SetupAccount from './pages/auth/SetupAccount'
import AuthError from './pages/auth/AuthError'
import AuthSuccess from './pages/auth/AuthSuccess'

function AppRoutes() {
  const { isMarketplaceEnabled, isAIConfigEnabled, isTeamAnalyticsEnabled, isAIUsageEnabled, isUserAIConfigEnabled, isLoading } = useFeatureFlags()
  
  // Show loading state while feature flags are loading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Ładowanie konfiguracji...</p>
        </div>
      </div>
    )
  }
  
  return (
    <Routes>
        {/* Public auth routes */}
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />
        <Route path="/auth/verify/:token" element={<VerifyEmail />} />
        <Route path="/auth/resend-verification" element={<ResendVerification />} />
        <Route path="/auth/forgot-password" element={<ForgotPassword />} />
        <Route path="/auth/reset-password/:token" element={<ResetPassword />} />
        
        {/* Asystenciai integration routes */}
        <Route path="/setup-account" element={<SetupAccount />} />
        <Route path="/auth/error" element={<AuthError />} />
        <Route path="/auth/success" element={<AuthSuccess />} />
        
        {/* Protected application routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Routes>
                  {/* 
                    Dynamic routes generated from moduleRegistry 
                    - Includes main routes and legacy backward-compatible routes
                    - Automatically protected based on module configuration
                    - Filtered by feature flags (hides disabled marketplaces)
                  */}
                  {generateModuleRoutes(isMarketplaceEnabled)}
                  {generateSpecialRoutes({
                    isAIConfigEnabled,
                    isTeamAnalyticsEnabled,
                    isAIUsageEnabled,
                    isUserAIConfigEnabled
                  })}
                  
                  {/* Catch all - redirect to home */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
  )
}

export default function App() {
  const initializePermissions = useAuthStore((state) => state.initializePermissions)

  // Initialize permissions on app start if user is already logged in
  useEffect(() => {
    initializePermissions()
  }, [initializePermissions])

  return (
    <FeatureFlagProvider>
      <AppRoutes />
      
      {/* Toast notifications - shown globally */}
      <ToastContainer />
      <Toaster position="top-right" />
    </FeatureFlagProvider>
  )
}
