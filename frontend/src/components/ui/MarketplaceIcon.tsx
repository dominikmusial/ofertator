import { MARKETPLACE_CONFIGS } from '../../types/marketplace'

interface Props {
  type: string
  size?: 'sm' | 'md' | 'lg'
  showName?: boolean
  className?: string
}

export default function MarketplaceIcon({ type, size = 'md', showName = false, className = '' }: Props) {
  const config = MARKETPLACE_CONFIGS[type]
  
  if (!config) {
    return <span className={className}>❓</span>
  }

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-4xl'
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <span className={sizeClasses[size]}>{config.icon}</span>
      {showName && <span className="font-medium">{config.name}</span>}
    </div>
  )
}
