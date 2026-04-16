"""Type definitions for Mirakl API"""
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class MiraklShopInfo:
    """Shop information from A01 endpoint"""
    id: int
    name: str
    currency_iso_code: Optional[str] = None
    description: Optional[str] = None
    is_professional: Optional[bool] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklShopInfo":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            currency_iso_code=data.get("currency_iso_code"),
            description=data.get("description"),
            is_professional=data.get("is_professional")
        )


@dataclass
class MiraklHierarchy:
    """Category hierarchy from H11 endpoint"""
    code: str
    label: str
    type: Optional[str] = None
    children: Optional[List["MiraklHierarchy"]] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklHierarchy":
        children = None
        if "children" in data and data["children"]:
            children = [cls.from_api_response(child) for child in data["children"]]
        
        return cls(
            code=data.get("code", ""),
            label=data.get("label", ""),
            type=data.get("type"),
            children=children
        )


@dataclass
class MiraklOffer:
    """Offer information from OF21/OF22 endpoints"""
    offer_id: int
    product_sku: str
    offer_state_code: str
    price: Optional[float] = None
    quantity: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklOffer":
        return cls(
            offer_id=data.get("offer_id"),
            product_sku=data.get("product_sku", ""),
            offer_state_code=data.get("offer_state_code", ""),
            price=data.get("price"),
            quantity=data.get("quantity")
        )


@dataclass
class MiraklOrder:
    """Order information from OR11 endpoint"""
    order_id: str
    order_state: str
    creation_date: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklOrder":
        return cls(
            order_id=data.get("order_id", ""),
            order_state=data.get("order_state", ""),
            creation_date=data.get("creation_date", "")
        )


@dataclass
class MiraklImportResponse:
    """Response from async import operations (OF01, OF24, OF04)"""
    import_id: int
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklImportResponse":
        return cls(import_id=data.get("import_id"))


OrderStateCode = Literal[
    "STAGING",
    "WAITING_ACCEPTANCE",
    "WAITING_DEBIT",
    "WAITING_DEBIT_PAYMENT",
    "SHIPPING",
    "SHIPPED",
    "TO_COLLECT",
    "RECEIVED",
    "CLOSED",
    "REFUSED",
    "CANCELED"
]
