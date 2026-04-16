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
            id=data.get("shop_id"),  # API returns 'shop_id', not 'id'
            name=data.get("shop_name", ""),  # API returns 'shop_name', not 'name'
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
class MiraklProduct:
    """Product information from P31 endpoint"""
    product_sku: str
    product_id: str
    product_id_type: str
    product_title: str
    category_code: Optional[str] = None
    category_label: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklProduct":
        return cls(
            product_sku=data.get("product_sku", ""),
            product_id=data.get("product_id", ""),
            product_id_type=data.get("product_id_type", ""),
            product_title=data.get("product_title", ""),
            category_code=data.get("category_code"),
            category_label=data.get("category_label")
        )


@dataclass
class MiraklAttributeRole:
    """Attribute role definition"""
    role_type: str
    parameters: Dict[str, str]
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklAttributeRole":
        params = {}
        for param in data.get("parameters", []):
            params[param.get("name", "")] = param.get("value", "")
        return cls(
            role_type=data.get("type", ""),
            parameters=params
        )


@dataclass
class MiraklProductAttribute:
    """Product attribute configuration from PM11 endpoint"""
    code: str
    label: str
    attribute_type: str
    requirement_level: Optional[str] = None
    hierarchy_code: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None
    default_value: Optional[str] = None
    values_list_code: Optional[str] = None
    type_parameters: Optional[Dict[str, str]] = None
    roles: Optional[List[MiraklAttributeRole]] = None
    validations: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklProductAttribute":
        # Parse type_parameters
        type_params = {}
        for param in data.get("type_parameters", []):
            type_params[param.get("name", "")] = param.get("value", "")
        
        # Parse roles
        roles = None
        if "roles" in data and data["roles"]:
            roles = [MiraklAttributeRole.from_api_response(r) for r in data["roles"]]
        
        return cls(
            code=data.get("code", ""),
            label=data.get("label", ""),
            attribute_type=data.get("type", ""),
            requirement_level=data.get("requirement_level"),
            hierarchy_code=data.get("hierarchy_code"),
            description=data.get("description"),
            example=data.get("example"),
            default_value=data.get("default_value"),
            values_list_code=data.get("values_list"),
            type_parameters=type_params if type_params else None,
            roles=roles,
            validations=data.get("validations")
        )


@dataclass
class MiraklOffer:
    """Offer information from OF21/OF22 endpoints"""
    offer_id: int
    product_sku: str
    state_code: str  # Offer condition (not offer_state_code!)
    price: Optional[float] = None
    quantity: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklOffer":
        return cls(
            offer_id=data.get("offer_id"),
            product_sku=data.get("product_sku", ""),
            state_code=data.get("state_code", ""),  # API returns 'state_code', not 'offer_state_code'
            price=data.get("price"),
            quantity=data.get("quantity")
        )


@dataclass
class MiraklOrder:
    """Order information from OR11 endpoint"""
    order_id: str
    order_state: str
    created_date: str  # API returns 'created_date', not 'creation_date'
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "MiraklOrder":
        return cls(
            order_id=data.get("order_id", ""),
            order_state=data.get("order_state", ""),
            created_date=data.get("created_date", "")  # API returns 'created_date', not 'creation_date'
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
