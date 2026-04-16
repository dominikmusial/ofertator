"""
API endpoints for creating offers on Allegro.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import uuid
from io import BytesIO
import pandas as pd

from app.db import models
from app.db.session import get_db
from app.core.auth import get_current_user
from app.infrastructure.marketplaces.allegro.services import offer_creation_service
from app.infrastructure.marketplaces.allegro.services.offer_creation_service import OfferCreationServiceError
from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling

router = APIRouter()
logger = logging.getLogger(__name__)


def get_valid_token(db: Session, current_user: models.User, account_id: int) -> str:
    """Helper to get a valid access token for an account."""
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    return get_valid_token_with_reauth_handling(db, account_id)


class SearchProductRequest(BaseModel):
    account_id: int
    ean: str


class ProductDetailsRequest(BaseModel):
    account_id: int
    product_id: str
    category_id: Optional[str] = None


class CreateOfferRequest(BaseModel):
    account_id: int
    product_id: str
    name: str
    category_id: str
    price: str
    stock: int = 1
    quantity: int = 1
    duration: Optional[str] = None  # Optional - if not provided, offer is until stock runs out
    images: Optional[List[str]] = None
    description: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    delivery: Optional[Dict[str, Any]] = None
    product_parameters: Optional[List[Dict[str, Any]]] = None  # Product parameters (go in productSet[].product.parameters)
    parameters: Optional[List[Dict[str, Any]]] = None  # Offer parameters (go in main payload.parameters)
    afterSalesServices: Optional[Dict[str, Any]] = None
    external_id: Optional[str] = None
    handling_time: Optional[str] = None  # ISO 8601 duration (e.g., "PT24H")
    invoice_type: Optional[str] = None  # "VAT" or "NONE" - required for tax settings
    tax_settings: Optional[Dict[str, Any]] = None  # Tax settings with rates for multiple countries
    responsible_producer_id: Optional[str] = None  # ID of responsible producer from account list
    responsible_person_id: Optional[str] = None  # ID of responsible person from account list
    responsible_person_name: Optional[str] = None  # Name of responsible person (optional, can be fetched from API)
    safety_information: Optional[Dict[str, Any]] = None  # Safety information (type: TEXT, description: string)
    publication_status: Optional[str] = "ACTIVE"  # "ACTIVE" for published offer, "INACTIVE" for draft


@router.post("/search-product")
def search_product_by_ean(
    request: SearchProductRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for a product in Allegro catalog by EAN.
    """
    try:
        access_token = get_valid_token(db, current_user, request.account_id)
        result = offer_creation_service.search_product_by_ean(access_token, request.ean)
        
        logger.info(f"User {current_user.id} searched for EAN {request.ean} on account {request.account_id}")
        return {
            "success": True,
            "products": result.get("products", []),
            "count": len(result.get("products", []))
        }
    except OfferCreationServiceError as e:
        logger.error(f"Error searching product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error searching product: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/product-details")
def get_product_details(
    request: ProductDetailsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a product from Allegro catalog.
    Also fetches category parameters and available settings.
    """
    try:
        access_token = get_valid_token(db, current_user, request.account_id)
        result = offer_creation_service.get_product_details(
            access_token,
            request.product_id,
            request.category_id
        )
        
        # Get category parameters (required and optional offer parameters)
        category_id = result.get('category', {}).get('id') or request.category_id
        category_params = {}
        shipping_rates = {}
        
        if category_id:
            try:
                category_params = offer_creation_service.get_category_parameters(access_token, category_id)
            except Exception as e:
                logger.warning(f"Failed to get category parameters: {e}")
        
        # Get shipping rates
        try:
            shipping_rates = offer_creation_service.get_shipping_rates(access_token)
        except Exception as e:
            logger.warning(f"Failed to get shipping rates: {e}")
        
        # Get after-sales services (returns and warranties)
        after_sales_services = {}
        try:
            after_sales_services = offer_creation_service.get_after_sales_services(access_token)
        except Exception as e:
            logger.warning(f"Failed to get after-sales services: {e}")
        
        # Get responsible producers
        responsible_producers = {}
        try:
            responsible_producers = offer_creation_service.get_responsible_producers(access_token)
        except Exception as e:
            logger.warning(f"Failed to get responsible producers: {e}")
        
        # Get responsible persons
        responsible_persons = {}
        try:
            responsible_persons = offer_creation_service.get_responsible_persons(access_token)
        except Exception as e:
            logger.warning(f"Failed to get responsible persons: {e}")
        
        # Get tax settings for category
        tax_settings = {}
        if category_id:
            try:
                tax_settings = offer_creation_service.get_tax_settings(access_token, category_id)
            except Exception as e:
                logger.warning(f"Failed to get tax settings: {e}")
        
        logger.info(f"User {current_user.id} fetched product details for {request.product_id} on account {request.account_id}")
        logger.debug(f"Product details response: {result}")
        return {
            "success": True,
            "product": result,
            "categoryParameters": category_params,
            "shippingRates": shipping_rates,
            "afterSalesServices": after_sales_services,
            "responsibleProducers": responsible_producers,
            "responsiblePersons": responsible_persons,
            "taxSettings": tax_settings
        }
    except OfferCreationServiceError as e:
        logger.error(f"Error getting product details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting product details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/create")
def create_offer(
    request: CreateOfferRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an offer on Allegro based on a product from catalog.
    """
    try:
        access_token = get_valid_token(db, current_user, request.account_id)
        
        # Prepare offer data
        offer_data = {
            "name": request.name,
            "category_id": request.category_id,
            "price": request.price,
            "stock": request.stock,
            "quantity": request.quantity,
            "duration": request.duration,  # Optional - if None, offer is until stock runs out
            "command_id": str(uuid.uuid4()),
            "images": request.images,
            "description": request.description,
            "location": request.location,
            "delivery": request.delivery,
            "product_parameters": request.product_parameters,  # Product parameters (go in productSet[].product.parameters)
            "parameters": request.parameters,  # Offer parameters (go in main payload.parameters)
            "afterSalesServices": request.afterSalesServices,
            "external_id": request.external_id,
            "handling_time": request.handling_time,
            "invoice_type": request.invoice_type,  # "VAT" or "NONE"
            "tax_settings": request.tax_settings,  # Tax settings with rates for multiple countries
            "responsible_producer_id": request.responsible_producer_id,
            "responsible_person_id": request.responsible_person_id,
            "responsible_person_name": request.responsible_person_name,
            "safety_information": request.safety_information,
            "publication_status": request.publication_status or "ACTIVE"
        }
        
        result = offer_creation_service.create_offer_from_product(
            access_token,
            request.product_id,
            offer_data,
            request.account_id
        )
        
        logger.info(
            f"User {current_user.id} created offer {result.get('id')} "
            f"for product {request.product_id} on account {request.account_id}"
        )
        
        return {
            "success": True,
            "offer": result,
            "offer_id": result.get("id"),
            "message": "Oferta została utworzona pomyślnie"
        }
    except OfferCreationServiceError as e:
        logger.error(f"Error creating offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating offer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/template")
def download_template(
    format: str = 'xlsx',  # 'xlsx' or 'csv'
    current_user: models.User = Depends(get_current_user),
):
    """
    Download empty template for offer creation import.
    
    Query params:
    - format: 'xlsx' (default) or 'csv'
    """
    try:
        headers = [
            'EAN',
            'Tytuł',
            'Cena',
            'SKU',
            'Ilość',
            'Cennik dostawy',
            'Czas dostawy',
            'Typ trwania',
            'Okres trwania',
            'Warunki zwrotów',
            'Producent odpowiedzialny',
            'Osoba odpowiedzialna',
            'Informacje o bezpieczeństwie',
            'Typ faktury',
            'Przedmiot opodatkowania',
            'Stawka VAT PL',
            'Zwolnienie z VAT'
        ]
        
        example_row = [
            '7622201386160',
            'Czekolada mleczna Milka 300 g',
            '19.99',
            'MILKA-300G',
            '10',
            '',
            'PT24H',
            'fixed',
            'PT720H',
            '',
            '',
            '',
            'Produkt bezpieczny dla konsumentów',
            'NO_INVOICE',
            '',
            '',
            ''
        ]
        
        if format == 'csv':
            csv_content = [
                ','.join(headers),
                ','.join(example_row)
            ]
            content = '\ufeff' + '\n'.join(csv_content)
            media_type = 'text/csv;charset=utf-8;'
            filename = 'szablon_ofert.csv'
            output = BytesIO(content.encode('utf-8'))
        else:  # xlsx
            df = pd.DataFrame([example_row], columns=headers)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Oferty')
                
                # Get workbook and worksheet for styling
                workbook = writer.book
                worksheet = writer.sheets['Oferty']
                
                # Auto-size columns
                for idx, col in enumerate(df.columns, start=1):
                    col_letter = worksheet.cell(row=1, column=idx).column_letter
                    worksheet.column_dimensions[col_letter].width = max(len(str(col)), 15)
            
            output.seek(0)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'szablon_ofert.xlsx'
            content = output.read()
            output = BytesIO(content)
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas generowania szablonu: {str(e)}"
        )
