import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: false
})

// Add authentication interceptor
api.interceptors.request.use((config) => {
  // Get token from localStorage to avoid circular dependency
  const authStorage = localStorage.getItem('auth-storage')
  if (authStorage) {
    try {
      const { state } = JSON.parse(authStorage)
      if (state.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  // Add trailing slash only for collection endpoints to prevent 307 redirects
  if (config.url && !config.url.endsWith('/')) {
    // Split URL and query string
    const [baseUrl, queryString] = config.url.split('?')
    
    // Collection endpoints that need trailing slash (exact matches only)
    const needsTrailingSlash = [
      '/allegro/templates',
      '/accounts', 
      '/allegro/images',
      '/allegro/offers',
      '/allegro/promotions'
    ].some(endpoint => baseUrl === endpoint)
    
    if (needsTrailingSlash) {
      config.url = queryString ? `${baseUrl}/?${queryString}` : `${baseUrl}/`
    }
  }
  
  return config
})

// Add response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh by dispatching event to auth store
      window.dispatchEvent(new CustomEvent('auth:refresh-needed'))
    }
    return Promise.reject(error)
  }
)

export { api }
export default api 