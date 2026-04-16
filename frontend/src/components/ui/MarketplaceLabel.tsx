import { MARKETPLACE_CONFIGS } from '../../types/marketplace'

interface MarketplaceLabelProps {
  type: string
  showIcon?: boolean
  showName?: boolean
}

export default function MarketplaceLabel({ 
  type, 
  showIcon = true, 
  showName = true 
}: MarketplaceLabelProps) {
  const marketplace = MARKETPLACE_CONFIGS[type] || MARKETPLACE_CONFIGS.allegro
  
  return (
    <span className="inline-flex items-center gap-1">
      {showIcon && <span>{marketplace.icon}</span>}
      {showName && <span>{marketplace.name}</span>}
    </span>
  )
}
