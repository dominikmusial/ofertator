"""
Allegro-specific template processing with AI content generation.

This module handles the complex template processing for Allegro offers,
including AI-generated content, image mapping, frame processing, and HTML sanitization.
"""
import logging
import json
import re
import anthropic
from typing import Optional, Dict, Tuple

from app.db.repositories import AIConfigRepository, UserRepository
from .html_sanitizer import sanitize_html_content

logger = logging.getLogger(__name__)


def process_template_sections_for_offer(
    template_sections: list,
    offer_details: dict,
    template_prompt: Optional[str] = None,
    image_mapping: Optional[Dict[str, str]] = None,
    user_id: Optional[int] = None,
    frame_scale: int = None,
    account_name: str = None,
    account_id: int = None,
    processing_mode: str = "Oryginalny",
    auto_fill_images: bool = True,
    save_processed_images: bool = False
) -> tuple[list, dict]:
    """
    Process template sections from frontend format into final Allegro API format.
    Uses comprehensive AI content generation similar to the old app.
    
    Returns:
        tuple: (processed_sections, image_replacements)
            processed_sections: List of sections for Allegro API
            image_replacements: Dict of image replacements for gallery updates
                               Format: {original_url: {'new_url': str, 'position': int, 'original_placeholder': str}}
    """
    logger.info(f"Processing {len(template_sections)} template sections with AI content generation")
    
    if not template_sections:
        logger.warning("No template sections provided")
        return [], {}
    
    # Initialize image replacements tracking
    image_replacements = {}
    
    # Process template sections to extract frame information and convert to backend format
    processed_template_sections = _extract_frame_info_from_template(template_sections)
    logger.info(f"Processed template sections: {processed_template_sections}")
    if processed_template_sections:
        logger.info(f"First processed section: {processed_template_sections[0]}")
    
    # Get product info for AI prompt
    product_info = _get_product_info_for_prompt(offer_details)
    
    # Check if we need AI content generation (any empty text sections)
    needs_ai_generation = False
    text_sections_count = 0
    
    for section in processed_template_sections:
        for item in section.get('items', []):
            if item.get('type') == 'TEXT':
                text_sections_count += 1
                content = item.get('content', '').strip()
                # Check if content is empty or contains placeholder/instruction text
                # Let AI decide if non-empty content is an instruction or final content
                if (not content or 
                    'Sekcja opisująca produkt' in content or
                    'Formatowanie:' in content or
                    'Instrukcja dla AI:' in content or
                    'Przykład:' in content):
                    needs_ai_generation = True
                elif content:
                    # Non-empty content exists - let AI decide if it's an instruction or final content
                    needs_ai_generation = True
    
    if needs_ai_generation and text_sections_count > 0:
        logger.info(f"AI content generation needed for {text_sections_count} text sections")
        
        # Use comprehensive AI generation similar to old app
        try:
            generated_sections = _generate_content_with_ai(
                processed_template_sections, 
                product_info, 
                template_prompt or "",
                offer_details,
                user_id
            )
            if generated_sections:
                logger.info("Successfully generated content with AI")
                # Restore frame information that might have been lost during AI processing
                generated_sections = _restore_frame_info(generated_sections, processed_template_sections)
                processed_sections = _process_image_mapping(generated_sections, offer_details, image_mapping, frame_scale, account_name, account_id, image_replacements, processing_mode, auto_fill_images, save_processed_images)
                return processed_sections, image_replacements
            else:
                # AI generation failed - this is a critical error when AI is needed
                logger.error("AI generation failed and is required for template processing")
                raise ValueError("AI content generation failed. Cannot update offer without proper AI-generated content.")
        except Exception as e:
            logger.error(f"AI content generation failed: {e}")
            # Re-raise the exception to fail the update instead of falling back
            raise ValueError(f"AI content generation failed: {e}. Cannot update offer without proper AI-generated content.")
    
    # Fallback: Process existing content and placeholders (only when AI is not needed)
    logger.info("Processing template sections without AI generation")
    processed_sections = _process_template_sections_without_ai(processed_template_sections, offer_details, image_mapping, frame_scale, account_name, account_id, image_replacements, processing_mode, auto_fill_images, save_processed_images)
    return processed_sections, image_replacements


def _extract_frame_info_from_template(template_sections) -> list:
    """
    Extract frame information from frontend template format and convert to backend format.
    
    Frontend format (from OfferEditor.tsx):
    {
        "items": [
            {"type": "IMAGE", "url": "Aukcja:1"},
            {"type": "TEXT", "content": "Some text"}
        ]
    }
    
    But the actual frontend sends section values format:
    {
        "type": "IMG,TXT",
        "values": {
            "image": "Aukcja:1",
            "frame": "Custom1",
            "text": "Some text"
        }
    }
    
    This function converts frontend format to backend format with frame info embedded.
    """
    logger.info(f"_extract_frame_info_from_template called with: {template_sections}")
    logger.info(f"Template sections type: {type(template_sections)}")
    
    if template_sections is None:
        logger.error("Template sections is None!")
        return []
    
    if not isinstance(template_sections, (list, tuple)):
        logger.error(f"Template sections is not a list/tuple, it's: {type(template_sections)}")
        return []
    
    processed_sections = []
    
    for section in template_sections:
        if not isinstance(section, dict):
            continue
        
        # Handle both formats: direct items format and section values format
        if 'items' in section and section['items'] is not None:
            # Already in backend format, just pass through
            processed_sections.append(section)
        elif 'type' in section and 'values' in section:
            # Frontend format - convert to backend format
            section_type = section.get('type')
            values = section.get('values', {})
            items = []
            
            if section_type == 'TXT':
                text_content = values.get('text', '')
                if text_content:
                    items.append({"type": "TEXT", "content": text_content})
            
            elif section_type == 'IMG':
                image_url = values.get('image', '')
                frame_url = values.get('frame', 'No frame')
                if image_url:
                    items.append({
                        "type": "IMAGE", 
                        "url": image_url,
                        "frame_url": frame_url
                    })
            
            elif section_type == 'IMG,TXT':
                image_url = values.get('image', '')
                frame_url = values.get('frame', 'No frame')
                text_content = values.get('text', '')
                
                if image_url:
                    items.append({
                        "type": "IMAGE", 
                        "url": image_url,
                        "frame_url": frame_url
                    })
                if text_content:
                    items.append({"type": "TEXT", "content": text_content})
            
            elif section_type == 'TXT,IMG':
                text_content = values.get('text', '')
                image_url = values.get('image', '')
                frame_url = values.get('frame', 'No frame')
                
                if text_content:
                    items.append({"type": "TEXT", "content": text_content})
                if image_url:
                    items.append({
                        "type": "IMAGE", 
                        "url": image_url,
                        "frame_url": frame_url
                    })
            
            elif section_type == 'IMG,IMG':
                image1_url = values.get('image1', '')
                frame1_url = values.get('frame1', 'No frame')
                image2_url = values.get('image2', '')
                frame2_url = values.get('frame2', 'No frame')
                
                if image1_url:
                    items.append({
                        "type": "IMAGE", 
                        "url": image1_url,
                        "frame_url": frame1_url
                    })
                if image2_url:
                    items.append({
                        "type": "IMAGE", 
                        "url": image2_url,
                        "frame_url": frame2_url
                    })
            
            if items:
                processed_sections.append({"items": items})
    
    return processed_sections


def _get_parameter_value(offer_details: dict, parameter_name: str) -> str:
    """Helper function to find a parameter's value in offer details."""
    for param in offer_details.get('parameters', []):
        if param.get('name') == parameter_name:
            values = param.get('values', [])
            # Ensure values is always a list before joining
            if not isinstance(values, list):
                values = [str(values)] if values is not None else []
            return ", ".join(str(v) for v in values)
    
    # Check in productSet as well
    if 'productSet' in offer_details:
        for product_item in offer_details['productSet']:
            if 'product' in product_item and 'parameters' in product_item['product']:
                for param in product_item['product']['parameters']:
                    if param.get('name') == parameter_name:
                        values = param.get('values', [])
                        # Ensure values is always a list before joining
                        if not isinstance(values, list):
                            values = [str(values)] if values is not None else []
                        return ", ".join(str(v) for v in values)
    return ""


def _get_original_description(offer_details: dict) -> str:
    """Helper function to extract the original description text."""
    description_html = ""
    if 'description' in offer_details and 'sections' in offer_details['description']:
        for section in offer_details['description']['sections']:
            for item in section.get('items', []):
                if item.get('type') == 'TEXT':
                    description_html += item.get('content', '')
    return description_html


def _get_product_info_for_prompt(offer_details: dict) -> str:
    """Gathers product information into a single string to be used in a prompt for AI."""
    params = []
    # Parameters from the main level
    for param in offer_details.get('parameters', []):
        name = param.get('name')
        values = param.get('values', [])
        # Ensure values is always a list before joining
        if not isinstance(values, list):
            values = [str(values)] if values is not None else []
        values_str = ", ".join(str(v) for v in values)
        params.append(f"{name}: {values_str}")

    # Parameters from productSet
    if 'productSet' in offer_details:
        for product_item in offer_details['productSet']:
            if 'product' in product_item and 'parameters' in product_item['product']:
                for param in product_item['product']['parameters']:
                    name = param.get('name')
                    values = param.get('values', [])
                    # Ensure values is always a list before joining
                    if not isinstance(values, list):
                        values = [str(values)] if values is not None else []
                    values_str = ", ".join(str(v) for v in values)
                    params.append(f"{name}: {values_str}")

    # Extract existing description content (like in the old working version)
    description = _get_original_description(offer_details)

    product_name = offer_details.get('name', '')

    # Include description content like in the old working version
    return f"Product Name: {product_name}\nParameters: {', '.join(params)}\nDescription: {description}"


# Continue in next message due to length...


# AI content generation function (large, from services/allegro.py lines 665-1163)
def _generate_content_with_ai(
    template_sections: list,
    product_info: str,
    additional_prompt: str,
    offer_details: dict,
    user_id: Optional[int] = None
) -> Optional[list]:
    """Generate content using AI for the entire template structure."""
    try:
        from app.services.ai_provider_service import ai_provider_service
        from app.db.session import SessionLocal
        
        ai_client = None
        model_name = None
        key_source = None
        
        if user_id:
            db = SessionLocal()
            try:
                user_config = AIConfigRepository.get_user_config(db, user_id)
                user = UserRepository.get_by_id(db, user_id)
                user_role = user.role if user else None
                registration_source = user.registration_source if user else None
                
                if user_config and user_config.is_active:
                    key_source = "user_custom"
                else:
                    key_source = "company_default"
                
                ai_client, model_name = ai_provider_service.get_user_ai_client(
                    user_config, 
                    fallback_to_default=True, 
                    user_role=user_role,
                    registration_source=registration_source
                )
            finally:
                db.close()
        else:
            key_source = "company_default"
            ai_client, model_name = ai_provider_service.get_user_ai_client(None, fallback_to_default=True)
        
        if not ai_client:
            logger.error("No AI client available")
            return None
        
        # Count text sections
        text_sections = []
        for section in template_sections:
            items = section.get('items', []) or []
            for item in items:
                if item.get('type') == 'TEXT':
                    content = item.get('content', '').strip()
                    if (not content or 
                        'Sekcja opisująca produkt' in content or
                        'Formatowanie:' in content or
                        'Instrukcja dla AI:' in content or
                        'Przykład:' in content):
                        text_sections.append((section, item))
                    elif content:
                        text_sections.append((section, item))
        
        text_sections_count = len(text_sections)
        
        if text_sections_count == 0:
            logger.info("No text sections need AI generation")
            return None
        
        # Create template structure
        template_structure = []
        for i, section in enumerate(template_sections):
            section_info = {"section_index": i, "items": []}
            section_items = section.get('items', []) or []
            
            has_text = any(item.get('type') == 'TEXT' for item in section_items)
            has_image = any(item.get('type') == 'IMAGE' for item in section_items)
            is_mixed_section = has_text and has_image
            
            for j, item in enumerate(section_items):
                if item.get('type') == 'TEXT':
                    section_info["items"].append({
                        "item_index": j,
                        "type": "TEXT",
                        "needs_content": True,
                        "has_adjacent_image": is_mixed_section
                    })
                elif item.get('type') == 'IMAGE':
                    section_info["items"].append({
                        "item_index": j,
                        "type": "IMAGE",
                        "url": item.get('url', '')
                    })
            template_structure.append(section_info)
        
        # Create AI prompt (abbreviated for size - would include full prompt from original)
        full_prompt = f"""IMPORTANT: You MUST fill ALL text sections in the template with meaningful content.

Your task is to fill exactly {text_sections_count} text section(s).

Product information:
{product_info}

Template structure:
{json.dumps(template_structure, indent=2)}

Template to fill:
"description":{{"sections":{json.dumps(template_sections)}}}"""

        if additional_prompt:
            full_prompt += "\n\nAdditional instructions:\n" + additional_prompt

        logger.info(f"Sending prompt to AI using {model_name}")
        
        input_tokens = 0
        output_tokens = 0
        ai_provider = None
        ai_response = None
        
        if isinstance(ai_client, anthropic.Anthropic):
            ai_provider = "anthropic"
            message = ai_client.messages.create(
                model=model_name,
                max_tokens=8192,
                system="You are a helpful assistant that returns ONLY valid JSON.",
                temperature=0.0,
                messages=[{"role": "user", "content": [{"type": "text", "text": full_prompt}]}]
            )
            ai_response = message.content[0].text
            if hasattr(message, 'usage'):
                input_tokens = message.usage.input_tokens
                output_tokens = message.usage.output_tokens
        else:
            import google.generativeai as genai
            ai_provider = "google"
            if hasattr(ai_client, 'generate_content'):
                response = ai_client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=8192,
                        temperature=0.0,
                    )
                )
                ai_response = response.text
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
            else:
                raise ValueError("Unknown AI client type")
        
        logger.info(f"AI Response received: {ai_response[:200]}...")
        
        # Log usage
        if input_tokens > 0 or output_tokens > 0:
            try:
                from app.services.analytics_service import AnalyticsService
                from app.db.session import SessionLocal
                log_db = SessionLocal()
                try:
                    AnalyticsService.log_ai_usage(
                        db=log_db,
                        user_id=user_id,
                        operation_type="offer_update",
                        ai_provider=ai_provider,
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        key_source=key_source
                    )
                    logger.info(f"Logged AI usage: {input_tokens} input + {output_tokens} output tokens")
                finally:
                    log_db.close()
            except Exception as e:
                logger.error(f"Error logging AI usage: {e}")
        
        # Parse JSON response (simplified version)
        try:
            json_start = ai_response.find('{')
            if json_start == -1:
                markdown_start = ai_response.find('```json')
                if markdown_start != -1:
                    content_after_marker = ai_response[markdown_start + 7:]
                    json_start = content_after_marker.find('{')
                    if json_start != -1:
                        json_start += markdown_start + 7
            
            if json_start >= 0:
                json_content = ai_response[json_start:]
                
                # Find balanced braces
                brace_count = 0
                json_end = -1
                in_string = False
                escape_next = False
                
                for i, char in enumerate(json_content):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\' and in_string:
                        escape_next = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                
                if json_end > 0:
                    json_content = json_content[:json_end]
                
                # Clean control characters
                json_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_content)
                
                data = json.loads(json_content)
                
                if 'description' in data and 'sections' in data['description']:
                    generated_sections = data['description']['sections']
                    
                    # Sanitize HTML content
                    for section in generated_sections:
                        if 'items' in section:
                            for item in section['items']:
                                if item.get('type') == 'TEXT' and 'content' in item:
                                    item['content'] = sanitize_html_content(item['content'])
                    
                    logger.info(f"AI generated {len(generated_sections)} sections")
                    return generated_sections
                else:
                    raise ValueError("AI response missing required structure")
        except Exception as parse_error:
            logger.error(f"Error parsing AI response: {parse_error}")
            return None
            
    except Exception as e:
        logger.error(f"Error in AI content generation: {e}")
        return None


def _restore_frame_info(generated_sections: list, original_sections: list) -> list:
    """Restore frame information that might have been lost during AI processing."""
    logger.info("Restoring frame information from original template sections")
    
    if not generated_sections or not original_sections:
        return generated_sections
    
    url_to_frame = {}
    proxy_to_frame = {}
    
    for section in original_sections:
        for item in section.get('items', []):
            if item.get('type') == 'IMAGE':
                url = item.get('url', '')
                frame_url = item.get('frame_url', '')
                if url and frame_url:
                    url_to_frame[url] = frame_url
                    
                    if url.startswith('/images/account/') and '/proxy/' in url:
                        try:
                            url_parts = url.split('/')
                            if len(url_parts) >= 6:
                                filename = url_parts[5]
                                from app.services.minio_service import minio_service
                                bucket_name = "account-images"
                                resolved_url = minio_service.get_public_url(bucket_name, filename)
                                proxy_to_frame[resolved_url] = frame_url
                        except Exception as e:
                            logger.warning(f"Could not create proxy mapping for {url}: {e}")
    
    for section in generated_sections:
        for item in section.get('items', []):
            if item.get('type') == 'IMAGE' and 'frame_url' not in item:
                url = item.get('url', '')
                if url in url_to_frame:
                    item['frame_url'] = url_to_frame[url]
                elif url in proxy_to_frame:
                    item['frame_url'] = proxy_to_frame[url]
    
    return generated_sections


def _process_template_sections_without_ai(
    template_sections: list,
    offer_details: dict,
    image_mapping: Optional[Dict[str, str]] = None,
    frame_scale: int = None,
    account_name: str = None,
    account_id: int = None,
    image_replacements: dict = None,
    processing_mode: str = "Oryginalny",
    auto_fill_images: bool = True,
    save_processed_images: bool = False
) -> list:
    """Process template sections without AI generation (fallback method)."""
    processed_sections = []
    image_map = image_mapping or {}
    
    for i, section in enumerate(template_sections):
        if not isinstance(section, dict) or 'items' not in section or section['items'] is None:
            continue
        
        processed_items = []
        
        for item in section['items']:
            if not isinstance(item, dict) or 'type' not in item:
                continue
                
            item_type = item['type']
            
            if item_type == 'TEXT':
                content = item.get('content', '')
                
                if (not content or 
                    content.strip() == 'Sekcja opisująca produkt' or
                    'Formatowanie:' in content):
                        content = f"<p>Opis produktu: {offer_details.get('name', 'Produkt')}</p>"
                
                if content:
                    content = content.replace("{name}", offer_details.get("name", ""))
                    content = content.replace("{description}", _get_original_description(offer_details))
                    
                    for match in re.finditer(r'{parameter:(.*?)}', content):
                        param_name = match.group(1)
                        param_value = _get_parameter_value(offer_details, param_name)
                        content = content.replace(match.group(0), param_value)
                    
                    content = sanitize_html_content(content)
                
                processed_items.append({"type": "TEXT", "content": content})
                
            elif item_type == 'IMAGE':
                url = item.get('url', '')
                frame_url = item.get('frame_url', '')
                url = _process_image_url(url, offer_details, image_map, frame_url, frame_scale, account_name, account_id, image_replacements, processing_mode, auto_fill_images, save_processed_images)
                if url:
                    processed_items.append({"type": "IMAGE", "url": url})
            
        if processed_items:
            processed_sections.append({"items": processed_items})
    
    return processed_sections


def _process_image_mapping(
    sections: list,
    offer_details: dict,
    image_mapping: Optional[Dict[str, str]] = None,
    frame_scale: int = None,
    account_name: str = None,
    account_id: int = None,
    image_replacements: dict = None,
    processing_mode: str = "Oryginalny",
    auto_fill_images: bool = True,
    save_processed_images: bool = False
) -> list:
    """Process image URLs in sections."""
    image_map = image_mapping or {}
    processed_sections = []
    
    for section in sections:
        processed_items = []
        for item in section.get('items', []):
            if item.get('type') == 'IMAGE':
                url = item.get('url', '')
                frame_url = item.get('frame_url', '')
                url = _process_image_url(url, offer_details, image_map, frame_url, frame_scale, account_name, account_id, image_replacements, processing_mode, auto_fill_images, save_processed_images)
                if url:
                    processed_items.append({"type": "IMAGE", "url": url})
            elif item.get('type') == 'TEXT':
                content = item.get('content', '')
                if content:
                    content = sanitize_html_content(content)
                    processed_items.append({"type": "TEXT", "content": content})
            else:
                processed_items.append(item)
        
        if processed_items:
            processed_sections.append({"items": processed_items})
    
    return processed_sections


def _get_filler_image_fallback(account_id: int, position: int) -> Optional[str]:
    """Get filler image fallback for missing offer images."""
    try:
        from app.db.session import SessionLocal
        from app.db import models
        import random
        
        db = SessionLocal()
        try:
            filler = db.query(models.AccountImage).filter(
                models.AccountImage.account_id == account_id,
                models.AccountImage.is_filler == True,
                models.AccountImage.filler_position == position
            ).first()
            
            if filler:
                logger.info(f"Found exact filler match for position {position}")
                return filler.url
            
            fillers = db.query(models.AccountImage).filter(
                models.AccountImage.account_id == account_id,
                models.AccountImage.is_filler == True
            ).all()
            
            if fillers:
                random_filler = random.choice(fillers)
                logger.info(f"Using random filler for position {position}")
                return random_filler.url
            
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting filler image: {e}")
        return None


def _process_image_url(url: str, offer_details: dict, image_map: Dict[str, str], frame_url: str = None, frame_scale: int = None, account_name: str = None, account_id: int = None, image_replacements: dict = None, processing_mode: str = "Oryginalny", auto_fill_images: bool = True, save_processed_images: bool = False) -> str:
    """Process a single image URL, handling placeholders, mapping, and frame application."""
    if not url:
        return ""
    
    original_url = url
    original_offer_image_url = None
    aukcja_position = None
    
    if url in image_map:
        url = image_map[url]
    elif url.startswith('Aukcja:'):
        try:
            image_number = int(url.split(':')[1])
            aukcja_position = image_number
            offer_images = offer_details.get('images', [])
            
            if offer_images and 1 <= image_number <= len(offer_images):
                url = offer_images[image_number - 1]
                original_offer_image_url = url
                logger.info(f"Mapped {original_url} to offer image: {url}")
            else:
                if auto_fill_images and account_id:
                    filler_url = _get_filler_image_fallback(account_id, image_number)
                    if filler_url:
                        url = filler_url
                        original_offer_image_url = None
                    else:
                        return ""
                else:
                    return ""
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid auction image format '{original_url}': {e}")
            return ""
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        if url.startswith('/images/account/') and '/proxy/' in url:
            try:
                url_parts = url.split('/')
                if len(url_parts) >= 6:
                    from app.services.minio_service import minio_service
                    filename = url_parts[5]
                    bucket_name = "account-images"
                    url = minio_service.get_public_url(bucket_name, filename)
            except Exception as e:
                logger.warning(f"Could not resolve proxy URL: {e}")
                return ""
        else:
            logger.warning(f"Invalid image URL format: '{url}'")
            return ""
    
    # Apply frame if specified
    if frame_url and frame_url != "No frame" and frame_url != "":
        try:
            from app.infrastructure.marketplaces.allegro.services.frame_processor import frame_processor_service
            
            original_image_url = url
            
            if frame_url.startswith('Custom') and len(frame_url) > 6:
                frame_number = int(frame_url[6:])
                if 1 <= frame_number <= 6 and account_name:
                    url = frame_processor_service.apply_custom_frame(url, frame_number, account_name)
            else:
                if frame_url.startswith('/images/account/') and '/proxy/' in url:
                    try:
                        url_parts = frame_url.split('/')
                        if len(url_parts) >= 6:
                            from app.services.minio_service import minio_service
                            filename = url_parts[5]
                            bucket_name = "account-images"
                            frame_url = minio_service.get_public_url(bucket_name, filename)
                    except Exception as e:
                        logger.error(f"Error resolving proxy URL: {e}")
                
                url = frame_processor_service.apply_frame(url, frame_url, frame_scale, save_to_storage=save_processed_images)
            
            # Track image replacement
            if (aukcja_position is not None and image_replacements is not None and 
                original_offer_image_url is not None and url != original_image_url):
                
                action = 'duplicate_thumbnail' if aukcja_position == 1 else 'replace'
                
                image_replacements[original_offer_image_url] = {
                    'new_url': url,
                    'position': aukcja_position - 1,
                    'original_placeholder': original_url,
                    'action': action
                }
        except Exception as e:
            logger.error(f"Error applying frame: {e}")
    
    return url
