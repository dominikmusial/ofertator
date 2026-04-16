export enum MarketplaceType {
  ALLEGRO = 'allegro',
  AMAZON = 'amazon',
  EMAG = 'emag',
  KAUFLAND = 'kaufland',
  DECATHLON = 'decathlon',
  CASTORAMA = 'castorama',
  LEROYMERLIN = 'leroymerlin'
}

export enum AuthenticationType {
  OAUTH = 'oauth',           // OAuth 2.0 with refresh tokens (expires, needs re-auth)
  API_KEY = 'api_key'        // Static API key (no expiry, no re-auth needed)
}

export interface MarketplaceConfig {
  icon: string
  name: string
  color: string
  authType: AuthenticationType  // Authentication mechanism
}

export const MARKETPLACE_CONFIGS: Record<string, MarketplaceConfig> = {
  allegro: {
    icon: '🟠',
    name: 'Allegro',
    color: '#ff5a00',
    authType: AuthenticationType.OAUTH
  },
  amazon: {
    icon: '📦',
    name: 'Amazon',
    color: '#ff9900',
    authType: AuthenticationType.OAUTH
  },
  emag: {
    icon: '🟣',
    name: 'eMAG',
    color: '#7b2cbf',
    authType: AuthenticationType.OAUTH
  },
  kaufland: {
    icon: '🔴',
    name: 'Kaufland',
    color: '#e30613',
    authType: AuthenticationType.OAUTH
  },
  decathlon: {
    icon: '🔵',
    name: 'Decathlon',
    color: '#0082c3',
    authType: AuthenticationType.API_KEY  // Mirakl uses API keys
  },
  castorama: {
    icon: '🟡',
    name: 'Castorama',
    color: '#ffd500',
    authType: AuthenticationType.API_KEY  // Mirakl uses API keys
  },
  leroymerlin: {
    icon: '🟢',
    name: 'Leroy Merlin',
    color: '#7ac143',
    authType: AuthenticationType.API_KEY  // Mirakl uses API keys
  }
}
