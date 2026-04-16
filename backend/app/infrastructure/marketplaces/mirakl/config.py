"""Mirakl marketplace configuration"""
from dataclasses import dataclass
from app.db.models import MarketplaceType


@dataclass
class MiraklConfig:
    """Configuration for a Mirakl-based marketplace"""
    base_url: str
    marketplace_name: str
    marketplace_type: MarketplaceType
    icon: str
    color: str


# Marketplace configurations
DECATHLON_CONFIG = MiraklConfig(
    base_url="https://marketplace-decathlon-eu.mirakl.net/api",
    marketplace_name="Decathlon",
    marketplace_type=MarketplaceType.decathlon,
    icon="🔵",
    color="#0082c3"
)

CASTORAMA_CONFIG = MiraklConfig(
    base_url="https://marketplace.castorama.pl/api",
    marketplace_name="Castorama",
    marketplace_type=MarketplaceType.castorama,
    icon="🟡",
    color="#ffd500"
)

LEROYMERLIN_CONFIG = MiraklConfig(
    base_url="https://adeo-marketplace.mirakl.net/api",
    marketplace_name="Leroy Merlin",
    marketplace_type=MarketplaceType.leroymerlin,
    icon="🟢",
    color="#7ac143"
)
