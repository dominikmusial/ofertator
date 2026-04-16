import React, { createContext, useContext, useEffect, useState } from 'react'
import api from '../lib/api'

interface FeatureFlags {
  marketplace: {
    allegro: boolean
    decathlon: boolean
    castorama: boolean
    leroymerlin: boolean
  }
  auth: {
    registration: boolean
    google_sso: boolean
  }
  admin: {
    ai_config: boolean
    team_analytics: boolean
  }
  modules: {
    ai_usage: boolean
  }
  user: {
    ai_config: boolean
  }
}

interface FeatureFlagContextType {
  flags: FeatureFlags
  isLoading: boolean
  isMarketplaceEnabled: (marketplace: string) => boolean
  isRegistrationEnabled: () => boolean
  isGoogleSSOEnabled: () => boolean
  isAIConfigEnabled: () => boolean
  isTeamAnalyticsEnabled: () => boolean
  isAIUsageEnabled: () => boolean
  isUserAIConfigEnabled: () => boolean
  refresh: () => Promise<void>
}

const defaultFlags: FeatureFlags = {
  marketplace: {
    allegro: true,
    decathlon: true,
    castorama: true,
    leroymerlin: true,
  },
  auth: {
    registration: true,
    google_sso: true,
  },
  admin: {
    ai_config: true,
    team_analytics: true,
  },
  modules: {
    ai_usage: true,
  },
  user: {
    ai_config: true,
  },
}

const FeatureFlagContext = createContext<FeatureFlagContextType | undefined>(undefined)

export const FeatureFlagProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [flags, setFlags] = useState<FeatureFlags>(defaultFlags)
  const [isLoading, setIsLoading] = useState(true)

  const fetchFlags = async () => {
    try {
      const response = await api.get<FeatureFlags>('/config/feature-flags')
      setFlags(response.data)
    } catch (error) {
      console.error('Failed to fetch feature flags:', error)
      // Keep default flags on error
      setFlags(defaultFlags)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchFlags()
  }, [])

  const isMarketplaceEnabled = (marketplace: string): boolean => {
    const normalizedMarketplace = marketplace.toLowerCase() as keyof FeatureFlags['marketplace']
    return flags.marketplace[normalizedMarketplace] ?? true
  }

  const isRegistrationEnabled = (): boolean => {
    return flags.auth.registration
  }

  const isGoogleSSOEnabled = (): boolean => {
    return flags.auth.google_sso
  }

  const isAIConfigEnabled = (): boolean => {
    return flags.admin.ai_config
  }

  const isTeamAnalyticsEnabled = (): boolean => {
    return flags.admin.team_analytics
  }

  const isAIUsageEnabled = (): boolean => {
    return flags.modules.ai_usage
  }

  const isUserAIConfigEnabled = (): boolean => {
    return flags.user.ai_config
  }

  const refresh = async () => {
    setIsLoading(true)
    await fetchFlags()
  }

  return (
    <FeatureFlagContext.Provider
      value={{
        flags,
        isLoading,
        isMarketplaceEnabled,
        isRegistrationEnabled,
        isGoogleSSOEnabled,
        isAIConfigEnabled,
        isTeamAnalyticsEnabled,
        isAIUsageEnabled,
        isUserAIConfigEnabled,
        refresh,
      }}
    >
      {children}
    </FeatureFlagContext.Provider>
  )
}

export const useFeatureFlags = (): FeatureFlagContextType => {
  const context = useContext(FeatureFlagContext)
  if (context === undefined) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider')
  }
  return context
}
