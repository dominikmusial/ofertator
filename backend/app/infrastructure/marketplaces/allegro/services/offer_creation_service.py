"""
Service for creating offers on Allegro based on EAN/product search.
"""
import requests
import logging
import uuid
from typing import Dict, List, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLEGRO_API_URL = "https://api.allegro.pl"


class OfferCreationServiceError(Exception):
    """Custom exception for offer creation service errors."""
    pass


def _get_headers(access_token: str) -> Dict[str, str]:
    """Returns standard headers for Allegro API requests."""
    return {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }


def search_product_by_ean(access_token: str, ean: str) -> Dict[str, Any]:
    """
    Search for a product in Allegro catalog by EAN (GTIN).
    
    Args:
        access_token: Allegro API access token
        ean: EAN/GTIN code to search for
        
    Returns:
        Dictionary with search results containing products
        
    Raises:
        OfferCreationServiceError: If search fails
    """
    url = f"{ALLEGRO_API_URL}/sale/products"
    params = {
        'phrase': ean,
        'mode': 'GTIN',  # Search by GTIN (EAN)
        'limit': 20
    }
    
    try:
        logger.info(f"Searching for product with EAN: {ean}")
        response = requests.get(url, headers=_get_headers(access_token), params=params)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Found {len(result.get('products', []))} products for EAN {ean}")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to search products: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while searching products: {e}")
        raise OfferCreationServiceError(f"Failed to search products: {e}")


def get_product_details(access_token: str, product_id: str, category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed information about a product from Allegro catalog.
    
    Args:
        access_token: Allegro API access token
        product_id: Product ID from Allegro catalog
        category_id: Optional category ID for context
        
    Returns:
        Dictionary with product details including parameters
        
    Raises:
        OfferCreationServiceError: If product fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/products/{product_id}"
    params = {}
    if category_id:
        params['category.id'] = category_id
    
    try:
        logger.info(f"Fetching product details for product_id: {product_id}")
        response = requests.get(url, headers=_get_headers(access_token), params=params)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully fetched product details for {product_id}")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get product details: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching product details: {e}")
        raise OfferCreationServiceError(f"Failed to get product details: {e}")


def get_category_parameters(access_token: str, category_id: str) -> Dict[str, Any]:
    """
    Get parameters supported by a category (required and optional offer parameters).
    
    Args:
        access_token: Allegro API access token
        category_id: Category ID
        
    Returns:
        Dictionary with category parameters
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/categories/{category_id}/parameters"
    
    try:
        logger.info(f"Fetching category parameters for category_id: {category_id}")
        response = requests.get(url, headers=_get_headers(access_token))
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully fetched category parameters for {category_id}")
        
        # Debug: Log dictionary parameters
        if result.get("parameters"):
            dict_params = [p for p in result["parameters"] if p.get("type") == "dictionary"]
            if dict_params:
                logger.info(f"Found {len(dict_params)} dictionary parameters")
                for param in dict_params:
                    if param.get("id") in ["3454", "3455", "250326"]:  # Rodzaj czekolady, Forma, Rodzaj
                        logger.info(f"Parameter {param.get('name')} ({param.get('id')}): has options.dictionary = {bool(param.get('options', {}).get('dictionary'))}, dictionary length = {len(param.get('options', {}).get('dictionary', []))}")
        
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get category parameters: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching category parameters: {e}")
        raise OfferCreationServiceError(f"Failed to get category parameters: {e}")


def get_shipping_rates(access_token: str) -> Dict[str, Any]:
    """
    Get available shipping rates for the account.
    
    Args:
        access_token: Allegro API access token
        
    Returns:
        Dictionary with shipping rates
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/shipping-rates"
    
    try:
        logger.info("Fetching shipping rates")
        response = requests.get(url, headers=_get_headers(access_token))
        response.raise_for_status()
        result = response.json()
        logger.info("Successfully fetched shipping rates")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get shipping rates: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching shipping rates: {e}")
        raise OfferCreationServiceError(f"Failed to get shipping rates: {e}")


def get_after_sales_services(access_token: str) -> Dict[str, Any]:
    """
    Get available after-sales services (returns and warranties) for the account.
    
    Args:
        access_token: Allegro API access token
        
    Returns:
        Dictionary with warranties and return policies
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    try:
        logger.info("Fetching after-sales services")
        
        # Get warranties
        warranties = []
        try:
            warranties_url = f"{ALLEGRO_API_URL}/after-sales-service-conditions/warranties"
            response = requests.get(warranties_url, headers=_get_headers(access_token))
            response.raise_for_status()
            warranties_data = response.json()
            if isinstance(warranties_data, dict) and 'warranties' in warranties_data:
                warranties = warranties_data['warranties']
            elif isinstance(warranties_data, list):
                warranties = warranties_data
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Failed to get warranties: {e.response.status_code if e.response else 'No response'}")
        
        # Get return policies
        returns = []
        try:
            returns_url = f"{ALLEGRO_API_URL}/after-sales-service-conditions/return-policies"
            response = requests.get(returns_url, headers=_get_headers(access_token))
            response.raise_for_status()
            returns_data = response.json()
            if isinstance(returns_data, dict) and 'returnPolicies' in returns_data:
                returns = returns_data['returnPolicies']
            elif isinstance(returns_data, list):
                returns = returns_data
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Failed to get return policies: {e.response.status_code if e.response else 'No response'}")
        
        result = {
            "warranties": warranties,
            "returns": returns
        }
        logger.info(f"Successfully fetched after-sales services: {len(warranties)} warranties, {len(returns)} return policies")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching after-sales services: {e}")
        raise OfferCreationServiceError(f"Failed to get after-sales services: {e}")


def get_responsible_producers(access_token: str) -> Dict[str, Any]:
    """
    Get list of responsible producers for the account.
    
    Args:
        access_token: Allegro API access token
        
    Returns:
        Dictionary with responsible producers list
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/responsible-producers"
    
    try:
        logger.info("Fetching responsible producers")
        response = requests.get(url, headers=_get_headers(access_token))
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully fetched {result.get('count', 0)} responsible producers")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get responsible producers: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching responsible producers: {e}")
        raise OfferCreationServiceError(f"Failed to get responsible producers: {e}")


def get_responsible_persons(access_token: str) -> Dict[str, Any]:
    """
    Get list of responsible persons for the account.
    
    Args:
        access_token: Allegro API access token
        
    Returns:
        Dictionary with responsible persons list
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/responsible-persons"
    
    try:
        logger.info("Fetching responsible persons")
        response = requests.get(url, headers=_get_headers(access_token))
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully fetched {result.get('count', 0)} responsible persons")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get responsible persons: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching responsible persons: {e}")
        raise OfferCreationServiceError(f"Failed to get responsible persons: {e}")


def get_tax_settings(access_token: str, category_id: str) -> Dict[str, Any]:
    """
    Get tax settings for a category.
    
    Args:
        access_token: Allegro API access token
        category_id: Category ID
        
    Returns:
        Dictionary with tax settings (subjects, rates, exemptions)
        
    Raises:
        OfferCreationServiceError: If fetch fails
    """
    url = f"{ALLEGRO_API_URL}/sale/tax-settings"
    params = {"category.id": category_id}
    
    try:
        logger.info(f"Fetching tax settings for category {category_id}")
        response = requests.get(url, headers=_get_headers(access_token), params=params)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully fetched tax settings for category {category_id}")
        return result
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to get tax settings: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching tax settings: {e}")
        raise OfferCreationServiceError(f"Failed to get tax settings: {e}")


def create_offer_from_product(
    access_token: str,
    product_id: str,
    offer_data: Dict[str, Any],
    account_id: int
) -> Dict[str, Any]:
    """
    Create an offer on Allegro based on a product from catalog.
    
    Args:
        access_token: Allegro API access token
        product_id: Product ID from Allegro catalog
        offer_data: Offer configuration (name, price, stock, etc.)
        account_id: Account ID for logging purposes
        
    Returns:
        Dictionary with created offer details
        
    Raises:
        OfferCreationServiceError: If offer creation fails
    """
    url = f"{ALLEGRO_API_URL}/sale/product-offers"
    
    # Product parameters come from product details and go in productSet[].product.parameters
    # These should be passed separately as product_parameters in offer_data
    product_parameters = []
    
    if offer_data.get("product_parameters"):
        # Product parameters from product details
        for param in offer_data["product_parameters"]:
            param_obj = {"id": param["id"]}
            if param.get("valuesIds"):
                param_obj["valuesIds"] = param["valuesIds"] if isinstance(param["valuesIds"], list) else [param["valuesIds"]]
            elif param.get("values"):
                param_obj["values"] = param["values"] if isinstance(param["values"], list) else [param["values"]]
            product_parameters.append(param_obj)
    
    # Build the offer payload according to Allegro API documentation
    product_obj = {
        "id": product_id
    }
    
    # Add product parameters if any
    if product_parameters:
        product_obj["parameters"] = product_parameters
    
    # Build productSet with responsible producer/person and safety information
    product_set_item = {
        "product": product_obj,
        "quantity": {
            "value": offer_data.get("quantity", 1)
        }
    }
    
    # Add responsible producer or responsible person to productSet (GPSR requirement)
    if offer_data.get("responsible_producer_id"):
        # If ID is provided, use type: ID format
        product_set_item["responsibleProducer"] = {
            "type": "ID",
            "id": offer_data["responsible_producer_id"]
        }
    elif offer_data.get("responsible_person_id"):
        # If person ID is provided, use id + name format
        product_set_item["responsiblePerson"] = {
            "id": offer_data["responsible_person_id"],
            "name": offer_data.get("responsible_person_name", "")
        }
    
    # Add safety information to productSet
    if offer_data.get("safety_information"):
        product_set_item["safetyInformation"] = offer_data["safety_information"]
    
    payload = {
        "productSet": [product_set_item],
        "name": offer_data.get("name", ""),
        "category": {
            "id": offer_data.get("category_id")
        },
        "sellingMode": {
            "format": "BUY_NOW",
            "price": {
                "amount": str(offer_data.get("price", "0.00")),
                "currency": "PLN"
            }
        },
        "stock": {
            "available": offer_data.get("stock", 1),
            "unit": "UNIT"
        },
        "publication": {
            "status": offer_data.get("publication_status", "ACTIVE")  # "ACTIVE" for published, "INACTIVE" for draft
        },
        "language": "pl-PL"
    }
    
    # Add duration only if provided (optional - if not provided, offer is until stock runs out)
    if offer_data.get("duration"):
        payload["publication"]["duration"] = offer_data["duration"]
    
    # Add optional fields if provided
    if offer_data.get("images"):
        payload["images"] = offer_data["images"]
    
    if offer_data.get("description"):
        payload["description"] = offer_data["description"]
    
    if offer_data.get("location"):
        payload["location"] = offer_data["location"]
    
    # Build delivery object
    delivery_obj = {}
    if offer_data.get("delivery"):
        delivery_obj.update(offer_data["delivery"])
    
    # Add handling time if provided
    if offer_data.get("handling_time"):
        delivery_obj["handlingTime"] = offer_data["handling_time"]
    
    if delivery_obj:
        payload["delivery"] = delivery_obj
    
    # Add payments.invoice (required for tax settings)
    if offer_data.get("invoice_type"):
        payload["payments"] = {
            "invoice": offer_data["invoice_type"]  # "VAT" or "NONE"
        }
    
    # Add tax settings (required when invoice is VAT)
    if offer_data.get("tax_settings"):
        payload["taxSettings"] = offer_data["tax_settings"]
    
    if offer_data.get("afterSalesServices"):
        payload["afterSalesServices"] = offer_data["afterSalesServices"]
    
    # Add offer parameters (not product parameters) - these go in main payload
    offer_parameters = []
    if offer_data.get("parameters"):
        for param in offer_data["parameters"]:
            param_obj = {"id": param["id"]}
            if param.get("valuesIds"):
                param_obj["valuesIds"] = param["valuesIds"] if isinstance(param["valuesIds"], list) else [param["valuesIds"]]
            elif param.get("values"):
                param_obj["values"] = param["values"] if isinstance(param["values"], list) else [param["values"]]
            offer_parameters.append(param_obj)
    
    if offer_parameters:
        payload["parameters"] = offer_parameters
    
    if offer_data.get("external_id"):
        payload["external"] = {"id": offer_data["external_id"]}
    
    headers = _get_headers(access_token)
    # Generate command_id if not provided
    command_id = offer_data.get("command_id") or str(uuid.uuid4())
    headers['Idempotency-Key'] = command_id
    
    try:
        logger.info(f"Creating offer for product {product_id} on account {account_id}")
        logger.debug(f"Offer payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code not in [201, 202]:
            error_msg = f"Failed to create offer: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data}"
                logger.error(f"Offer creation error: {error_msg}")
            except:
                error_msg += f" - {response.text}"
                logger.error(f"Offer creation error: {error_msg}")
            raise OfferCreationServiceError(error_msg)
        
        result = response.json()
        logger.info(f"Successfully created offer {result.get('id')} for product {product_id}")
        return result
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error while creating offer: {e.response.status_code if e.response else 'No response'}"
        if e.response:
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
        logger.error(error_msg)
        raise OfferCreationServiceError(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while creating offer: {e}")
        raise OfferCreationServiceError(f"Failed to create offer: {e}")
