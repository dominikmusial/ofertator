import traceback
import requests
import tempfile
from fpdf import FPDF
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image
import os
import re
import logging
import io
from typing import Dict, List, Any, Optional, Tuple
import base64
from app.infrastructure.marketplaces.factory import factory
from app.db.repositories import AccountRepository

# Set up logging
logger = logging.getLogger(__name__)

class PDF(FPDF):
    def header(self):
        if hasattr(self, 'logo_path') and self.logo_path:
            try:
                # Calculate optimal logo size
                from PIL import Image
                with Image.open(self.logo_path) as img:
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                    
                    # Target max dimensions
                    max_width = 40  # Increased from 30
                    max_height = 25
                    
                    # Calculate size maintaining aspect ratio
                    if aspect_ratio > 1:  # Wider than tall
                        logo_width = min(max_width, max_height * aspect_ratio)
                        logo_height = logo_width / aspect_ratio
                    else:  # Taller than wide
                        logo_height = min(max_height, max_width / aspect_ratio)
                        logo_width = logo_height * aspect_ratio
                    
                    # Position logo with better placement
                    self.image(self.logo_path, x=10, y=8, w=logo_width, h=logo_height)
                    
            except Exception as e:
                logger.error(f"Error adding logo: {e}")
                # Fallback to original size if there's an error
                try:
                    self.image(self.logo_path, x=10, y=8, w=40)
                except:
                    pass

        self.set_font('DejaVu', '', 15)
        self.cell(50)  # Increased spacing to accommodate larger logo
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, self.company_name, ln=True, align='L')

        if hasattr(self, 'code_number') and self.code_number:
            self.add_barcode(self.code_number, x=self.w - 60, y=5)

        self.ln(10)
        self.set_line_width(0.5)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Strona {self.page_no()}', align='R')

    def add_image_gallery(self, image_paths, x_start=10, y_start=50, image_width=60, image_height=60, columns=3, spacing=5):
        self.set_xy(x_start, y_start)
        x, y = x_start, y_start
        count = 0
        for image_path in image_paths:
            try:
                self.image(image_path, x=x, y=y, w=image_width, h=image_height)
                x += image_width + spacing
                count += 1
                if count % columns == 0:
                    x = x_start
                    y += image_height + spacing
            except Exception as e:
                logger.error(f"Error adding image to gallery: {e}")

    def add_section_title(self, title):
        self.set_font('DejaVu', 'B', 14)
        self.set_text_color(40, 75, 99)
        self.cell(0, 10, title, ln=True)
        self.set_line_width(0.3)
        self.set_draw_color(40, 75, 99)
        self.line(10, self.get_y() - 2, self.w - 10, self.get_y() - 2)
        self.ln(5)

    def add_description(self, description):
        self.set_font('DejaVu', '', 12)
        self.set_text_color(50, 50, 50)
        
        # Split description into sections (separated by double newline)
        sections = description.split('\n\n')
        
        for i, section in enumerate(sections):
            if section.strip():  # Skip empty sections
                self.multi_cell(0, 8, section.strip())
                # Add spacing between sections (but not after the last one)
                if i < len(sections) - 1:
                    self.ln(8)  # Extra spacing between sections
        
        self.ln(5)

    def add_product_table(self, parameters):
        self.set_font('DejaVu', 'B', 12)
        col_widths = [self.w / 3 - 20, self.w / 3 * 2 + 10]
        row_height = 8
        self.set_fill_color(230, 230, 230)
        self.cell(col_widths[0], row_height, 'Parametr', border=0, fill=True)
        self.cell(col_widths[1], row_height, 'Wartość', border=0, fill=True)
        self.ln(row_height)
        self.set_font('DejaVu', '', 10)
        fill = False
        for param, value in parameters.items():
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            self.cell(col_widths[0], row_height, param, border=0, fill=True)
            self.cell(col_widths[1], row_height, str(value), border=0, fill=True)
            self.ln(row_height)
            fill = not fill
        self.ln(5)

    def add_barcode(self, code_number, x, y):
        try:
            ean = EAN13(code_number, writer=ImageWriter())
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                barcode_path = tmp_file.name
                ean.write(tmp_file)
            self.image(barcode_path, x=x, y=y, w=50)
            os.remove(barcode_path)
        except Exception as e:
            logger.error(f"Error adding barcode: {e}")

def create_product_sheet(title, description, image_paths, parameters, code_number, output_pdf,
                         company_name='Nazwa Firmy', logo_path=None):
    try:
        pdf = PDF()
        
        # Fonts are mounted at /app/fonts in Docker
        font_dir = '/app/fonts'
        
        os.makedirs(font_dir, exist_ok=True)
        
        fonts = {
            'regular': ('DejaVuSans.ttf', 'https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf'),
            'bold': ('DejaVuSans-Bold.ttf', 'https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans-Bold.ttf'),
            'italic': ('DejaVuSans-Oblique.ttf', 'https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans-Oblique.ttf')
        }
        
        font_paths = {}
        for font_type, (filename, url) in fonts.items():
            font_path = os.path.join(font_dir, filename)
            font_paths[font_type] = font_path
            
            if not os.path.exists(font_path) or os.path.getsize(font_path) == 0:
                logger.info(f"Pobieranie {filename}...")
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Pomyślnie pobrano {filename}")
                except Exception as e:
                    logger.error(f"Nie udało się pobrać {filename}: {str(e)}")
                    raise Exception(f"Nie można pobrać wymaganej czcionki {filename}")
        
        try:
            pdf.add_font('DejaVu', '', font_paths['regular'], uni=True)
            pdf.add_font('DejaVu', 'B', font_paths['bold'], uni=True)
            pdf.add_font('DejaVu', 'I', font_paths['italic'], uni=True)
        except Exception as e:
            logger.error(f"Błąd podczas dodawania czcionek do PDF: {str(e)}")
            raise
        
        pdf.company_name = company_name
        pdf.logo_path = logo_path
        pdf.code_number = code_number

        pdf.add_page()
        pdf.set_font('DejaVu', 'B', 20)
        pdf.set_text_color(40, 75, 99)

        title_width = pdf.w - 20
        title_height = pdf.font_size * 1.5
        
        title_lines = []
        words = title.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if pdf.get_string_width(test_line) <= title_width:
                current_line = test_line
            else:
                if current_line:
                    title_lines.append(current_line)
                current_line = word
        
        if current_line:
            title_lines.append(current_line)
        
        for line in title_lines:
            pdf.cell(0, title_height, line, ln=True, align='C')
        
        pdf.ln(5)

        # Match old app layout exactly: Gallery first, then Description, then Parameters
        pdf.add_section_title('Galeria Produktu')
        pdf.add_image_gallery(image_paths, x_start=15, y_start=pdf.get_y(), image_width=60, image_height=60, columns=3, spacing=5)
        pdf.ln(65)

        pdf.add_section_title('Opis Produktu')
        pdf.add_description(description)

        pdf.add_section_title('Parametry Techniczne')
        pdf.add_product_table(parameters)

        pdf.output(output_pdf)
        logger.info(f"PDF utworzony pomyślnie: {output_pdf}")

    except Exception as e:
        logger.error(f"Błąd podczas tworzenia karty produktowej: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def extract_product_info(data, skip_description=False):
    logger.info(f"extract_product_info called with data type: {type(data)}")
    logger.info(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    # Extract title
    product_name = data.get('name', 'Brak tytułu')
    logger.info(f"Product name: {product_name}")
    
    # Extract description - following old app logic (sections 2-3, not 0-1)
    description = 'Brak opisu'
    if not skip_description:
        description_texts = []
        if 'description' in data and 'sections' in data['description']:
            sections = data['description']['sections']
            logger.info(f"Total sections found: {len(sections)}")
            
            # Find first 2 sections with TEXT content, starting from index 2
            # This skips sections 0-1 and finds actual text sections (not just empty or image-only)
            sections_to_check = sections[2:] if len(sections) > 2 else sections
            logger.info(f"Searching for 2 text sections starting from index 2, checking {len(sections_to_check)} sections")
            
            target_text_sections = 2  # We want 2 text sections
            
            for section_index, section in enumerate(sections_to_check):
                actual_index = section_index + 2  # Adjust for starting at index 2
                
                if len(description_texts) >= target_text_sections:
                    logger.info(f"Already collected {len(description_texts)} text sections, stopping")
                    break
                    
                logger.info(f"Checking section at index {actual_index} (collected {len(description_texts)}/{target_text_sections} so far)")
                
                if 'items' in section:
                    section_content = []
                    for item in section['items']:
                        if item.get('type') == 'TEXT' and 'content' in item:
                            section_content.append(item['content'])
                            logger.info(f"Found text in section {actual_index}: {item['content'][:100]}...")
                    
                    # If this section has text content, add it
                    if section_content:
                        joined_content = ' '.join(section_content)
                        description_texts.append(joined_content)
                        logger.info(f"Section {actual_index} added to description ({len(joined_content)} chars) - total collected: {len(description_texts)}")
                    else:
                        logger.info(f"Section {actual_index} has no TEXT items, skipping")
                else:
                    logger.warning(f"Section {actual_index} has no 'items' key")
        
        # Join sections with double newline for visual separation
        description = '\n\n'.join(description_texts) if description_texts else 'Brak opisu'
        logger.info(f"Final description length: {len(description)}")
    else:
        logger.info("Skipping description extraction (will use custom description)")
    
    # Extract images - use direct images array like old app
    images = data.get('images', [])
    logger.info(f"Found {len(images)} images directly from offer")
    
    # Extract parameters - following old app logic: productSet first, then parameters
    parameters = {}
    
    # First, extract from productSet like old app
    if 'productSet' in data:
        logger.info(f"Found productSet with {len(data['productSet'])} items")
        for product_item in data['productSet']:
            if 'product' in product_item and 'parameters' in product_item['product']:
                for param in product_item['product']['parameters']:
                    name = param.get('name')
                    values = param.get('values', [])
                    if name and values:
                        # Ensure values is always a list before joining
                        if not isinstance(values, list):
                            values = [str(values)] if values is not None else []
                        value_str = ', '.join(str(v) for v in values)
                        parameters[name] = value_str
                        logger.info(f"Added parameter from productSet: {name} = {value_str}")
    
    # Then, extract from main parameters (may override productSet parameters)
    if 'parameters' in data:
        logger.info(f"Found main parameters: {len(data['parameters'])} items")
        for param in data['parameters']:
            name = param.get('name')
            values = param.get('values', [])
            if name and values:
                # Ensure values is always a list before joining
                if not isinstance(values, list):
                    values = [str(values)] if values is not None else []
                value_str = ', '.join(str(v) for v in values)
                parameters[name] = value_str
                logger.info(f"Added parameter from main: {name} = {value_str}")
    
    logger.info(f"Total parameters extracted: {len(parameters)}")
    
    # Extract code number - following old app logic
    code_number = None
    for param_name in ['EAN (GTIN)', 'Kod producenta']:
        if param_name in parameters:
            code_number = parameters[param_name]
            logger.info(f"Found code number from {param_name}: {code_number}")
            break
    
    if not code_number:
        # Fallback to the new app's logic if old app's logic doesn't work
        for param in data.get('parameters', []):
            if param.get('name', '').lower() in ['ean', 'kod kreskowy', 'kod produktu']:
                values = param.get('values', [])
                if values and len(values[0]) >= 12:
                    code_number = values[0]
                    logger.info(f"Found code number from fallback: {code_number}")
                    break
    
    # Convert images to URLs if they're objects (to match old app format)
    image_urls = []
    if isinstance(images, list):
        for image in images:
            if isinstance(image, dict) and 'url' in image:
                image_urls.append(image['url'])
            elif isinstance(image, str):
                image_urls.append(image)
    
    logger.info(f"Extracted {len(image_urls)} image URLs")
    
    return product_name, description, parameters, image_urls, code_number

def download_images(image_urls):
    image_paths = []
    # Limit to first 3 images like the old app
    for url in image_urls[:3]:
        if not url:
            continue
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    image_paths.append(tmp_file.name)
            else:
                logger.warning(f"Failed to download image: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Exception while downloading image: {url}. Error: {e}")
    
    return image_paths

def download_image_from_url(url):
    """Download an image from URL and return local file path"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            try:
                img = Image.open(io.BytesIO(response.content))
                
                # Verify image is valid
                img.verify()
                img = Image.open(io.BytesIO(response.content))  # Need to reopen after verify
                
                # Determine file extension based on image format
                if img.format == 'PNG':
                    file_ext = '.png'
                else:
                    file_ext = '.jpg'
                
                # For PNG with transparency, preserve the transparency
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # Keep the transparency for PNG
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                        img.save(tmp_file.name, 'PNG')
                        return tmp_file.name
                else:
                    # For non-transparent images, convert to RGB for compatibility
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Save as JPEG with error handling
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        img.save(tmp_file.name, 'JPEG', quality=95)
                        return tmp_file.name
                        
            except Exception as img_error:
                logger.error(f"Failed to process image from {url}: {img_error}")
                return None
        else:
            logger.warning(f"Failed to download image from {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception while downloading image from {url}. Error: {e}")
        return None
    
    return None

def strip_html_tags(text):
    import re
    from html import unescape
    
    # First, unescape HTML entities (like &amp; → &)
    text = unescape(text)
    
    # Replace paragraph and heading closing tags with newline (to separate blocks)
    text = re.sub(r'</(?:p|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    
    # Replace other block-level closing tags with space to preserve word boundaries
    text = re.sub(r'</(?:div|li|tr|td|th)>', ' ', text, flags=re.IGNORECASE)
    
    # Replace <br> tags with newline to preserve line breaks
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up multiple spaces on the same line (preserve newlines)
    # Split by newlines, clean each line, then rejoin
    lines = text.split('\n')
    lines = [re.sub(r' +', ' ', line).strip() for line in lines]
    # Keep empty lines to preserve paragraph spacing
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def create_attachment_object(access_token, attachment_type, file_name):
    url = 'https://api.allegro.pl/sale/offer-attachments'
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'type': attachment_type,
        'file': {
            'name': file_name
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            attachment_id = response.json()['id']
            upload_url = response.headers['Location']
            logger.info(f"Attachment ID: {attachment_id}")
            logger.info(f"Upload URL: {upload_url}")
            return attachment_id, upload_url
        else:
            logger.error(f"Failed to create attachment object: {response.status_code}")
            logger.error(response.json())
            return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {e}")
        return None, None

def upload_file(upload_url, file_path, access_token, content_type='application/pdf'):
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': content_type,
        'Authorization': f'Bearer {access_token}'
    }

    try:
        with open(file_path, 'rb') as file:
            response = requests.put(upload_url, headers=headers, data=file)
        if response.status_code == 200:
            logger.info("File uploaded successfully")
            return True
        else:
            logger.error(f"Failed to upload file: {response.status_code}")
            logger.error(response.text)
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {e}")
        return False

def upload_file_content(upload_url, file_content, access_token, content_type='application/pdf'):
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': content_type,
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.put(upload_url, headers=headers, data=file_content)
        if response.status_code == 200:
            logger.info("File content uploaded successfully")
            return True
        else:
            logger.error(f"Failed to upload file content: {response.status_code}")
            logger.error(response.text)
            
            # Try to parse error details for better error messages
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        if error.get('message') == 'Invalid file format':
                            logger.error(f"Invalid file format for content type: {content_type}")
                            logger.error("Make sure the file format matches the attachment type requirements")
            except:
                pass
            
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {e}")
        return False

def update_existing_attachment(access_token, existing_attachment_id, file_path, offer_id):
    """
    Update an existing attachment using the PUT endpoint.
    This uploads new file content to replace the existing attachment.
    """
    # Step 1: Create a new attachment object to get upload URL
    import os
    filename = os.path.basename(file_path)
    
    logger.info(f"Creating new attachment object for updating {existing_attachment_id}")
    new_attachment_id, upload_url = create_attachment_object(access_token, 'PRODUCT_INFORMATION_SHEET', filename)
    
    if not new_attachment_id or not upload_url:
        logger.error("Failed to create new attachment object for update")
        return False
    
    # Step 2: Upload the file to the new attachment
    logger.info(f"Uploading file to new attachment {new_attachment_id}")
    if not upload_file(upload_url, file_path, access_token):
        logger.error("Failed to upload file to new attachment")
        return False
    
    # Step 3: Update the offer to replace old attachment ID with new one
    from app.infrastructure.marketplaces.factory import factory
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        provider = factory.get_provider_for_account(db, account_id)
        offer_data = provider.get_offer(offer_id)
    finally:
        db.close()
    if not offer_data:
        logger.error(f"Failed to get offer data for {offer_id}")
        return False
    
    current_attachments = offer_data.get('attachments', [])
    
    # Replace the old attachment ID with the new one
    updated_attachments = []
    for attachment in current_attachments:
        if isinstance(attachment, dict) and attachment.get('id') == existing_attachment_id:
            updated_attachments.append({'id': new_attachment_id})
            logger.info(f"Replaced attachment {existing_attachment_id} with {new_attachment_id}")
        else:
            updated_attachments.append(attachment)
    
    # Update the offer with the new attachments array
    url = f'https://api.allegro.pl/sale/product-offers/{offer_id}'
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'attachments': updated_attachments
    }
    
    try:
        logger.info(f"Updating offer {offer_id} with new attachment array")
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"Successfully updated offer {offer_id} with new attachment")
            return True
        else:
            logger.error(f"Failed to update offer: {response.status_code}")
            logger.error(response.text)
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error while updating offer: {e}")
        return False

def attach_to_offer(access_token, offer_id, attachment_id, account_id):
    from app.infrastructure.marketplaces.factory import factory
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        provider = factory.get_provider_for_account(db, account_id)
        offer_data = provider.get_offer(offer_id)
    finally:
        db.close()
    if not offer_data:
        logger.error(f"Failed to get offer data for {offer_id}")
        return False
    
    current_attachments = offer_data.get('attachments', [])
    logger.info(f"Current attachments structure: {current_attachments}")
    
    # Log each attachment in detail
    for i, attachment in enumerate(current_attachments):
        logger.info(f"Attachment {i}: {attachment} (type: {type(attachment)})")
        if isinstance(attachment, dict):
            for key, value in attachment.items():
                logger.info(f"  {key}: {value}")
    
    # Check if there are any existing PRODUCT_INFORMATION_SHEET attachments
    # Since attachments don't include type info, we need to fetch it
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }
    
    existing_product_cards = []
    for attachment in current_attachments:
        if isinstance(attachment, dict):
            attachment_id_existing = attachment.get('id')
            if attachment_id_existing:
                try:
                    # Get attachment details to check its type
                    details_url = f'https://api.allegro.pl/sale/offer-attachments/{attachment_id_existing}'
                    response = requests.get(details_url, headers=headers)
                    if response.status_code == 200:
                        details = response.json()
                        attachment_type = details.get('type')
                        attachment_name = details.get('file', {}).get('name', 'Unknown')
                        logger.info(f"Existing attachment {attachment_id_existing} type: {attachment_type}, name: {attachment_name}")
                        
                        # Check if it's a product information sheet
                        if attachment_type == 'PRODUCT_INFORMATION_SHEET':
                            existing_product_cards.append({
                                'id': attachment_id_existing,
                                'name': attachment_name
                            })
                    else:
                        logger.warning(f"Could not get details for attachment {attachment_id_existing}")
                except Exception as e:
                    logger.error(f"Error checking attachment {attachment_id_existing}: {e}")
    
    # If there are existing product cards, replace the first one using PUT endpoint
    if existing_product_cards:
        existing_names = [card['name'] for card in existing_product_cards]
        logger.info(f"Offer {offer_id} already has product card(s): {existing_names}. Will update the first one.")
        
        # Use the existing attachment ID for the PUT request
        existing_attachment_id = existing_product_cards[0]['id']
        logger.info(f"Updating existing attachment {existing_attachment_id}")
        
        return existing_attachment_id  # Return the existing ID to signal update mode
    
    # If we get here, there are no existing product cards, so we can add the new one
    all_attachments = current_attachments + [{'id': attachment_id}]
    logger.info(f"Adding new product card. Final attachments: {all_attachments}")
    
    url = f'https://api.allegro.pl/sale/product-offers/{offer_id}'
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'attachments': all_attachments
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info("Offer updated successfully with attachment")
            return True
        else:
            logger.error(f"Failed to update offer: {response.status_code}")
            logger.error(response.text)
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {e}")
        return False

def generate_single_product_card(access_token, offer_id, account_id, custom_description=None):
    from app.db.session import SessionLocal
    
    try:
        # Get account info from database
        db = SessionLocal()
        try:
            account = AccountRepository.get_by_id(db, account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            account_name = account.nazwa_konta
            logger.info(f"Processing product card for account: {account_name}")
            
            # Get logo from database
            account_logo = AccountRepository.get_logo(db, account_id)
            logo_path = None
            if account_logo:
                logger.info(f"Found logo in database: {account_logo.url}")
                
                # Convert proxy URL to MinIO URL if needed
                logo_url = account_logo.url
                if logo_url.startswith('/images/account/') and '/proxy/' in logo_url:
                    try:
                        # Extract filename from proxy URL
                        # Format: /images/account/{account_id}/proxy/{filename}
                        url_parts = logo_url.split('/')
                        if len(url_parts) >= 6 and url_parts[1] == 'images' and url_parts[2] == 'account' and url_parts[4] == 'proxy':
                            filename = url_parts[5]
                            
                            # Get MinIO URL
                            from app.services.minio_service import minio_service
                            bucket_name = "account-images"
                            minio_url = minio_service.get_public_url(bucket_name, filename)
                            logo_url = minio_url
                            logger.info(f"Converted proxy URL to MinIO URL: {minio_url}")
                    except Exception as e:
                        logger.warning(f"Could not convert proxy URL '{account_logo.url}': {e}")
                
                # Download logo from URL
                logo_path = download_image_from_url(logo_url)
                logger.info(f"Downloaded logo to: {logo_path}")
            else:
                logger.warning(f"No logo found for account {account_id}")
        finally:
            db.close()
        
        logger.info(f"Fetching offer details for {offer_id} via marketplace provider")
        provider = factory.get_provider_for_account(db, account_id)
        offer_data = provider.get_offer(offer_id)
        if not offer_data:
            logger.error(f"Failed to get offer data for {offer_id}")
            return False

        logger.info(f"Pobrano dane oferty {offer_id}")
        
        # Use custom description if provided (AI-generated), otherwise extract from offer
        if custom_description:
            logger.info(f"Using provided custom description (AI-generated): {len(custom_description)} characters")
            title, _, parameters, image_urls, code_number = extract_product_info(offer_data, skip_description=True)
            description = custom_description
        else:
            logger.info("Extracting description from offer data")
            title, description, parameters, image_urls, code_number = extract_product_info(offer_data)
        
        # Always strip HTML tags for PDF (PDF doesn't render HTML, only plain text)
        logger.info("Usuwanie tagów HTML z opisu...")
        description = strip_html_tags(description)
        
        logger.info(f"Pobieranie obrazów dla oferty {offer_id}...")
        image_paths = download_images(image_urls)
        logger.info(f"Pobrano {len(image_paths)} obrazów")

        company_name = account_name
        # Create safe filename - remove only truly problematic characters, keep Polish chars
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)  # Remove only file system forbidden chars
        safe_title = safe_title[:100]  # Limit length to avoid filesystem issues
        # Create PDF in temporary directory to avoid permission issues
        import tempfile
        temp_dir = tempfile.gettempdir()
        output_pdf = os.path.join(temp_dir, f"{safe_title}.pdf")

        try:
            logger.info(f"Tworzenie karty produktowej dla oferty {offer_id}...")
            create_product_sheet(
                title=title,
                description=description,
                image_paths=image_paths,
                parameters=parameters,
                code_number=code_number,
                output_pdf=output_pdf,
                company_name=company_name,
                logo_path=logo_path
            )
            logger.info(f"Karta produktowa pomyślnie utworzona: {output_pdf}")
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia karty produktowej: {e}")
            return False

        logger.info(f"Przygotowywanie załącznika dla oferty {offer_id}...")
        attachment_type = 'PRODUCT_INFORMATION_SHEET'
        # Use just the filename without the full path for the attachment
        filename = f"{safe_title}.pdf"
        attachment_id, upload_url = create_attachment_object(access_token, attachment_type, filename)
        if not attachment_id or not upload_url:
            logger.error("Nie udało się utworzyć obiektu załącznika.")
            return False

        logger.info(f"Przesyłanie karty produktowej do Allegro...")
        if not upload_file(upload_url, output_pdf, access_token):
            logger.error("Nie udało się przesłać pliku")
            return False
            
        logger.info(f"Dołączanie karty produktowej do oferty {offer_id}...")
        result = attach_to_offer(access_token, offer_id, attachment_id, account_id)
        
        # Check if we got an existing attachment ID to update
        if isinstance(result, str) and result != "already_exists":
            # This is an existing attachment ID, update it with new content
            logger.info(f"Updating existing attachment {result} with new content")
            if not update_existing_attachment(access_token, result, output_pdf, offer_id):
                logger.error("Nie udało się zaktualizować istniejącej karty produktowej")
                return False
            logger.info(f"Karta produktowa pomyślnie zaktualizowana dla oferty {offer_id}")
        elif result == True:
            # New attachment was added successfully
            logger.info(f"Karta produktowa pomyślnie dołączona do oferty {offer_id}")
        else:
            # Something went wrong
            logger.error("Nie udało się dołączyć karty do oferty")
            return False

        for path in image_paths:
            try:
                os.remove(path)
            except:
                pass
        if logo_path:
            try:
                os.remove(logo_path)
            except:
                pass
        try:
            os.remove(output_pdf)
        except:
            pass
        
        logger.info(f"Usunięto tymczasowe pliki")
        return True

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors and return meaningful error messages
        logger.error(f"HTTP error podczas generowania karty produktowej dla oferty {offer_id}: {str(e)}")
        logger.error(f"HTTP error status code: {e.response.status_code}")
        
        # Return specific error message based on HTTP status code
        if e.response.status_code == 403:
            return f"Brak uprawnień do odczytu oferty {offer_id}. Sprawdź czy oferta należy do tego konta i czy masz odpowiednie uprawnienia."
        elif e.response.status_code == 404:
            return f"Oferta {offer_id} nie istnieje lub została usunięta z Allegro."
        elif e.response.status_code == 400:
            return f"Nieprawidłowe dane dla oferty {offer_id}. Sprawdź format ID oferty."
        elif e.response.status_code == 429:
            return f"Zbyt wiele zapytań dla oferty {offer_id}. Spróbuj ponownie za chwilę."
        else:
            return f"Błąd HTTP {e.response.status_code} dla oferty {offer_id}: {str(e)}"
    except Exception as e:
        logger.error(f"Błąd podczas generowania karty produktowej dla oferty {offer_id}: {str(e)}")
        return False

class PdfGeneratorService:
    def __init__(self):
        pass

    def generate_pdf(
        self,
        title: str,
        description: str,
        images: List[str],
        parameters: Dict[str, Any]
    ) -> bytes:
        # Always strip HTML tags for PDF (PDF doesn't render HTML, only plain text)
        description = strip_html_tags(description)
        
        image_paths = download_images(images)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_pdf = tmp_file.name
        
        try:
            create_product_sheet(
                title=title,
                description=description,
                image_paths=image_paths,
                parameters=parameters,
                code_number=None,
                output_pdf=output_pdf
            )
            
            with open(output_pdf, 'rb') as f:
                pdf_bytes = f.read()
            
            return pdf_bytes
            
        finally:
            for path in image_paths:
                try:
                    os.remove(path)
                except:
                    pass
            try:
                os.remove(output_pdf)
            except:
                pass

pdf_generator_service = PdfGeneratorService() 
