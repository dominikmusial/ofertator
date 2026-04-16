"""
Title Optimizer Service for AI-powered title optimization
Adapted from the original Tytułomat system
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.services.ai_provider_service import ai_provider_service
from app.services.ai_config_service import ai_config_service
from app.db import schemas
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Cache for offer parameters (in-memory cache per user session)
_offer_params_cache = {
    "data": {},  # {user_id: {offer_id: params_string}}
    "expiry": {},  # {user_id: {offer_id: timestamp}}
    "cache_duration_seconds": 1800  # 30 minutes session cache
}

# Import Allegro-specific prompts
from ..prompts import ALLEGRO_TITLE_OUTPUT_INSTRUCTIONS


class TitleOptimizerService:
    """Service for optimizing product titles using AI"""
    
    @staticmethod
    def _get_cached_offer_params(user_id: int, offer_id: str) -> Optional[str]:
        """Get cached offer parameters if available and not expired"""
        if user_id not in _offer_params_cache["data"]:
            return None
        
        if offer_id not in _offer_params_cache["data"][user_id]:
            return None
        
        # Check if cache is expired
        if user_id in _offer_params_cache["expiry"] and offer_id in _offer_params_cache["expiry"][user_id]:
            expiry_time = _offer_params_cache["expiry"][user_id][offer_id]
            if datetime.now() > expiry_time:
                # Remove expired entry
                del _offer_params_cache["data"][user_id][offer_id]
                del _offer_params_cache["expiry"][user_id][offer_id]
                return None
        
        return _offer_params_cache["data"][user_id][offer_id]
    
    @staticmethod
    def _cache_offer_params(user_id: int, offer_id: str, params: str):
        """Cache offer parameters for user session"""
        if user_id not in _offer_params_cache["data"]:
            _offer_params_cache["data"][user_id] = {}
        
        if user_id not in _offer_params_cache["expiry"]:
            _offer_params_cache["expiry"][user_id] = {}
        
        _offer_params_cache["data"][user_id][offer_id] = params
        _offer_params_cache["expiry"][user_id][offer_id] = datetime.now() + timedelta(
            seconds=_offer_params_cache["cache_duration_seconds"]
        )
    
    @staticmethod
    def _fetch_offer_parameters(account_id: int, offer_ids: List[str], user_id: Optional[int] = None) -> Dict[str, str]:
        """
        Fetch offer parameters for multiple offers with caching support.
        Fetches uncached offers IN PARALLEL for better performance.
        
        Args:
            account_id: Account ID to fetch offers from
            offer_ids: List of offer IDs to fetch parameters for
            user_id: Optional user ID for caching
            
        Returns dict {offer_id: parameters_string}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        offer_params = {}
        offers_to_fetch = []
        
        # Check cache first if user_id is provided
        if user_id:
            for offer_id in offer_ids:
                cached_params = TitleOptimizerService._get_cached_offer_params(user_id, offer_id)
                if cached_params is not None:
                    offer_params[offer_id] = cached_params
                    logger.info(f"Używanie zbuforowanych parametrów dla oferty {offer_id}")
                else:
                    offers_to_fetch.append(offer_id)
        else:
            offers_to_fetch = offer_ids
        
        # Fetch parameters for uncached offers IN PARALLEL
        if offers_to_fetch:
            logger.info(f"Pobieranie parametrów dla {len(offers_to_fetch)} ofert równolegle...")
            
            def fetch_single_offer(offer_id):
                """Helper function to fetch a single offer's parameters"""
                try:
                    from app.infrastructure.marketplaces.factory import factory
                    from app.db.session import SessionLocal
                    
                    db = SessionLocal()
                    try:
                        provider = factory.get_provider_for_account(db, account_id)
                        offer_details = provider.get_offer(offer_id)
                        
                        # Extract product params (Allegro-specific format)
                        # This extracts only parameters, without name and description
                        params = []
                        for param in offer_details.get('parameters', []):
                            name = param.get('name')
                            values = param.get('values', [])
                            if not isinstance(values, list):
                                values = [str(values)] if values is not None else []
                            values_str = ", ".join(str(v) for v in values)
                            if name and values_str:
                                params.append(f"{name}: {values_str}")
                        
                        # Check productSet as well
                        if 'productSet' in offer_details:
                            for product_item in offer_details['productSet']:
                                if 'product' in product_item and 'parameters' in product_item['product']:
                                    for param in product_item['product']['parameters']:
                                        name = param.get('name')
                                        values = param.get('values', [])
                                        if not isinstance(values, list):
                                            values = [str(values)] if values is not None else []
                                        values_str = ", ".join(str(v) for v in values)
                                        if name and values_str:
                                            params.append(f"{name}: {values_str}")
                        
                        params_str = ", ".join(params) if params else ""
                        return (offer_id, params_str, None)
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f"Błąd pobierania parametrów dla oferty {offer_id}: {e}")
                    return (offer_id, "", str(e))
            
            # Use ThreadPoolExecutor to fetch multiple offers in parallel
            # Max 10 concurrent requests to avoid overwhelming the API
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_offer = {executor.submit(fetch_single_offer, offer_id): offer_id 
                                  for offer_id in offers_to_fetch}
                
                for future in as_completed(future_to_offer):
                    offer_id, params, error = future.result()
                    offer_params[offer_id] = params
                    
                    # Cache the result if user_id is provided
                    if user_id and not error:
                        TitleOptimizerService._cache_offer_params(user_id, offer_id, params)
        
        return offer_params
    
    @staticmethod
    def _prepare_titles_for_prompt(titles: List[schemas.TitleToOptimize]) -> str:
        """Prepare titles in JSON format for the AI prompt"""
        titles_data = [
            {
                "offer_id": t.offer_id,
                "current_title": t.current_title
            }
            for t in titles
        ]
        return json.dumps(titles_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def _validate_title(title: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a title according to Allegro rules
        Returns (is_valid, warning_message)
        """
        warnings = []
        
        # Check length
        if len(title) > 75:
            warnings.append(f"Tytuł jest za długi ({len(title)} znaków, maksymalnie 75)")
        
        # Check for excessive caps
        if title.isupper() and len(title) > 10:
            warnings.append("Tytuł zawiera zbyt dużo wielkich liter")
        
        # Check for emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        if emoji_pattern.search(title):
            warnings.append("Tytuł zawiera emotikony (niedozwolone na Allegro)")
        
        return len(warnings) == 0, "; ".join(warnings) if warnings else None
    
    @staticmethod
    def _extract_json_from_response(response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract JSON array from AI response, handling markdown code blocks
        """
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    async def _optimize_single_batch(
        titles: List[schemas.TitleToOptimize],
        ai_client,
        model_name: str,
        user_prompt: str,
        gen_params: dict,
        include_offer_parameters: bool = False,
        access_token: Optional[str] = None,
        user_id: Optional[int] = None,
        offer_params: Optional[Dict[str, str]] = None
    ) -> Tuple[List[schemas.OptimizedTitleResult], int, int]:
        """
        Optimize a single batch of titles
        Returns: (results, successful_count, failed_count)
        """
        try:
            # Build parameters section if needed
            parameters_section = ""
            if include_offer_parameters and offer_params:
                param_lines = []
                for offer_id, params in offer_params.items():
                    if offer_id in [t.offer_id for t in titles] and params.strip():
                        param_lines.append(f"Oferta {offer_id}: {params}")
                
                if param_lines:
                    parameters_section = "\n\nParametry produktów do uwzględnienia w optymalizacji:\n" + "\n".join(param_lines) + "\n"
            
            # Prepare titles JSON
            titles_json = TitleOptimizerService._prepare_titles_for_prompt(titles)
            
            # Combine user prompt with parameters section and Allegro-specific output instructions
            full_prompt = user_prompt + parameters_section + ALLEGRO_TITLE_OUTPUT_INSTRUCTIONS.replace("{titles_json}", titles_json)
            
            # Call AI based on provider type
            response_text = None
            
            # Check if it's Anthropic
            if hasattr(ai_client, 'messages'):
                # Anthropic client
                api_params = {
                    "model": model_name,
                    "max_tokens": gen_params.get('max_output_tokens', 4000),
                    "messages": [{"role": "user", "content": full_prompt}]
                }
                
                # Anthropic doesn't allow both temperature and top_p simultaneously
                # Priority: temperature > top_p (as per Anthropic best practices)
                if 'temperature' in gen_params:
                    api_params['temperature'] = gen_params['temperature']
                elif 'top_p' in gen_params:
                    # Only use top_p if temperature is not specified
                    api_params['top_p'] = gen_params['top_p']
                
                if 'top_k' in gen_params and gen_params['top_k']:
                    api_params['top_k'] = gen_params['top_k']
                if 'stop_sequences' in gen_params and gen_params['stop_sequences']:
                    api_params['stop_sequences'] = gen_params['stop_sequences']
                
                response = ai_client.messages.create(**api_params)
                response_text = response.content[0].text
            
            # Check if it's Google Gemini
            elif hasattr(ai_client, 'generate_content'):
                import google.generativeai as genai
                
                generation_config = {}
                if 'max_output_tokens' in gen_params:
                    generation_config['max_output_tokens'] = gen_params['max_output_tokens']
                if 'temperature' in gen_params:
                    generation_config['temperature'] = gen_params['temperature']
                if 'top_p' in gen_params:
                    generation_config['top_p'] = gen_params['top_p']
                if 'top_k' in gen_params and gen_params['top_k']:
                    generation_config['top_k'] = gen_params['top_k']
                if 'stop_sequences' in gen_params and gen_params['stop_sequences']:
                    generation_config['stop_sequences'] = gen_params['stop_sequences']
                
                if generation_config:
                    response = ai_client.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(**generation_config)
                    )
                else:
                    response = ai_client.generate_content(full_prompt)
                
                # Check if response has valid content before accessing .text
                if not response.candidates or not response.candidates[0].content.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                    
                    # Special handling for MAX_TOKENS - this should trigger retry with smaller batch
                    if finish_reason == 2:  # MAX_TOKENS
                        raise Exception("MAX_TOKENS")
                    
                    error_msg = f"Gemini API nie zwróciło odpowiedzi. Powód: {finish_reason}"
                    if finish_reason == 3:  # SAFETY
                        error_msg = "Odpowiedź została zablokowana przez filtry bezpieczeństwa Gemini."
                    elif finish_reason == 4:  # RECITATION
                        error_msg = "Odpowiedź została zablokowana z powodu potencjalnego plagiatu."
                    
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                response_text = response.text
            
            else:
                raise Exception("Unknown AI provider type")
            
            # Parse response
            optimized_data = TitleOptimizerService._extract_json_from_response(response_text)
            
            if not optimized_data:
                # Check if response looks truncated (missing closing brackets)
                if response_text and not response_text.rstrip().endswith(('```', ']', '}')):
                    logger.error(f"AI response appears truncated. Last 200 chars: ...{response_text[-200:]}")
                    raise Exception("MAX_TOKENS")  # Treat as token limit error for retry
                else:
                    logger.error(f"Failed to parse AI response as JSON. Response: {response_text[:500]}")
                    raise Exception("AI zwróciło nieprawidłowy format odpowiedzi")
            
            # Map results back to input titles
            results = []
            successful = 0
            failed = 0
            
            ai_results_map = {item.get('offer_id'): item for item in optimized_data}
            
            for title in titles:
                ai_result = ai_results_map.get(title.offer_id)
                
                if ai_result and ai_result.get('optimized_title'):
                    optimized_title = ai_result['optimized_title'].strip()
                    analysis = ai_result.get('analysis', '').strip()
                    
                    # Validate optimized title
                    is_valid, warning = TitleOptimizerService._validate_title(optimized_title)
                    
                    if warning:
                        analysis = f"{analysis}\n\nUwaga: {warning}" if analysis else f"Uwaga: {warning}"
                    
                    results.append(schemas.OptimizedTitleResult(
                        offer_id=title.offer_id,
                        current_title=title.current_title,
                        optimized_title=optimized_title,
                        analysis=analysis or None,
                        character_count=len(optimized_title),
                        success=True,
                        error=None
                    ))
                    successful += 1
                else:
                    results.append(schemas.OptimizedTitleResult(
                        offer_id=title.offer_id,
                        current_title=title.current_title,
                        optimized_title=title.current_title,
                        analysis=None,
                        character_count=len(title.current_title),
                        success=False,
                        error="AI nie zwróciło wyniku dla tego tytułu"
                    ))
                    failed += 1
            
            return results, successful, failed
            
        except Exception as e:
            # If batch fails, return all as failed
            error_str = str(e)
            results = [
                schemas.OptimizedTitleResult(
                    offer_id=t.offer_id,
                    current_title=t.current_title,
                    optimized_title=t.current_title,
                    analysis=None,
                    character_count=len(t.current_title),
                    success=False,
                    error=f"Błąd podczas optymalizacji: {error_str}"
                )
                for t in titles
            ]
            return results, 0, len(titles)
    
    @staticmethod
    async def optimize_titles(
        titles: List[schemas.TitleToOptimize],
        user_id: Optional[int] = None,
        custom_prompt: Optional[str] = None,
        user_role = None,
        registration_source = None,
        include_offer_parameters: bool = False,
        access_token: Optional[str] = None,
        account_id: Optional[int] = None
    ) -> schemas.OptimizeTitlesAIResponse:
        """
        Optimize multiple titles using AI with automatic batching
        
        Args:
            titles: List of titles to optimize
            user_id: Optional user ID for AI configuration
            custom_prompt: Optional custom prompt (overrides default)
            user_role: User role for AI client fallback
            registration_source: User registration source for AI client fallback
            include_offer_parameters: Whether to fetch and include offer parameters in prompt
            access_token: Allegro API access token (DEPRECATED - use account_id instead)
            account_id: Account ID (required if include_offer_parameters=True)
            
        Returns:
            OptimizeTitlesAIResponse with optimization results
        """
        if not titles:
            return schemas.OptimizeTitlesAIResponse(
                results=[],
                total_processed=0,
                successful=0,
                failed=0
            )
        
        # Validate limits based on parameter inclusion
        max_titles = 20 if include_offer_parameters else 100
        if len(titles) > max_titles:
            limit_text = "20 tytułów (z parametrami)" if include_offer_parameters else "100 tytułów"
            error_message = f"Przekroczono limit {limit_text}. Otrzymano {len(titles)} tytułów."
            logger.error(error_message)
            return schemas.OptimizeTitlesAIResponse(
                results=[
                    schemas.OptimizedTitleResult(
                        offer_id=t.offer_id,
                        current_title=t.current_title,
                        optimized_title=t.current_title,
                        analysis=None,
                        character_count=len(t.current_title),
                        success=False,
                        error=error_message
                    )
                    for t in titles
                ],
                total_processed=len(titles),
                successful=0,
                failed=len(titles)
            )
        
        # Validate account_id if parameters are requested
        if include_offer_parameters and not account_id:
            error_message = "Account ID wymagany do pobierania parametrów ofert."
            logger.error(error_message)
            return schemas.OptimizeTitlesAIResponse(
                results=[
                    schemas.OptimizedTitleResult(
                        offer_id=t.offer_id,
                        current_title=t.current_title,
                        optimized_title=t.current_title,
                        analysis=None,
                        character_count=len(t.current_title),
                        success=False,
                        error=error_message
                    )
                    for t in titles
                ],
                total_processed=len(titles),
                successful=0,
                failed=len(titles)
            )
        
        # Get AI client
        ai_client, model_name = ai_provider_service.get_user_ai_client(
            user_config=None if user_id is None else await TitleOptimizerService._get_user_ai_config(user_id),
            fallback_to_default=True,
            user_role=user_role,
            registration_source=registration_source
        )
        
        if not ai_client:
            # Return all as failed if no AI available
            return schemas.OptimizeTitlesAIResponse(
                results=[
                    schemas.OptimizedTitleResult(
                        offer_id=t.offer_id,
                        current_title=t.current_title,
                        optimized_title=t.current_title,
                        analysis=None,
                        character_count=len(t.current_title),
                        success=False,
                        error="Brak dostępu do AI. Skonfiguruj swój klucz API lub skontaktuj się z administratorem."
                    )
                    for t in titles
                ],
                total_processed=len(titles),
                successful=0,
                failed=len(titles)
            )
        
        try:
            # Determine provider name based on client type
            provider_name = "anthropic" if hasattr(ai_client, 'messages') else "google"
            
            # Load configuration from database
            db = SessionLocal()
            try:
                # Get prompt from database (or use custom if provided)
                if custom_prompt:
                    user_prompt = custom_prompt
                else:
                    # Get Allegro-specific prompt for titles
                    user_prompt = ai_config_service.get_prompt_for_titles(db, provider_name, marketplace_type='allegro')
                
                # Get generation parameters from database
                gen_params = ai_config_service.get_generation_params(db, "titles", provider_name)
                
                logger.info(f"Using configured max_output_tokens: {gen_params.get('max_output_tokens', 'not set')}")
            finally:
                db.close()
            
            # Fetch offer parameters if requested
            offer_params = {}
            if include_offer_parameters and account_id:
                logger.info(f"Fetching parameters for {len(titles)} offers")
                offer_ids = [t.offer_id for t in titles]
                offer_params = TitleOptimizerService._fetch_offer_parameters(account_id, offer_ids, user_id)
                
            # Determine batch size - use adaptive batching to prevent MAX_TOKENS errors
            # Will automatically retry with smaller batches if MAX_TOKENS error occurs
            batch_size = 7 if include_offer_parameters else 12
            
            # If we have more titles than batch_size, use batching
            if len(titles) > batch_size:
                logger.info(f"Processing {len(titles)} titles in batches of {batch_size}")
                all_results = []
                total_successful = 0
                total_failed = 0
                
                # Process in batches
                for i in range(0, len(titles), batch_size):
                    batch = titles[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(titles) + batch_size - 1) // batch_size
                    
                    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} titles)")
            
                    # Try processing the batch
                    batch_results, batch_successful, batch_failed = await TitleOptimizerService._optimize_single_batch(
                        titles=batch,
                        ai_client=ai_client,
                        model_name=model_name,
                        user_prompt=user_prompt,
                        gen_params=gen_params,
                        include_offer_parameters=include_offer_parameters,
                        access_token=access_token,
                        user_id=user_id,
                        offer_params=offer_params
                    )
                    
                    # Check if batch failed due to MAX_TOKENS and retry with smaller batches
                    if batch_failed == len(batch) and any("MAX_TOKENS" in r.error for r in batch_results if r.error):
                        logger.warning(f"Batch {batch_num} hit MAX_TOKENS, splitting into smaller batches")
                        smaller_batch_size = max(2, len(batch) // 2)  # Split in half, minimum 2
                        
                        batch_results = []
                        batch_successful = 0
                        batch_failed = 0
                        
                        for j in range(0, len(batch), smaller_batch_size):
                            mini_batch = batch[j:j + smaller_batch_size]
                            logger.info(f"  Retrying mini-batch with {len(mini_batch)} titles")
                            
                            mini_results, mini_successful, mini_failed = await TitleOptimizerService._optimize_single_batch(
                                titles=mini_batch,
                                ai_client=ai_client,
                                model_name=model_name,
                                user_prompt=user_prompt,
                                gen_params=gen_params,
                                include_offer_parameters=include_offer_parameters,
                                access_token=access_token,
                                user_id=user_id,
                                offer_params=offer_params
                            )
                            
                            batch_results.extend(mini_results)
                            batch_successful += mini_successful
                            batch_failed += mini_failed
                    
                    all_results.extend(batch_results)
                    total_successful += batch_successful
                    total_failed += batch_failed
                
                logger.info(f"Completed all batches: {total_successful} successful, {total_failed} failed")
                
                return schemas.OptimizeTitlesAIResponse(
                    results=all_results,
                    total_processed=len(titles),
                    successful=total_successful,
                    failed=total_failed
                )
            
            # Single batch processing (original flow for small requests)
            logger.info(f"Processing {len(titles)} titles in single batch")
            batch_results, batch_successful, batch_failed = await TitleOptimizerService._optimize_single_batch(
                titles=titles,
                ai_client=ai_client,
                model_name=model_name,
                user_prompt=user_prompt,
                gen_params=gen_params,
                include_offer_parameters=include_offer_parameters,
                access_token=access_token,
                user_id=user_id,
                offer_params=offer_params
            )
            
            return schemas.OptimizeTitlesAIResponse(
                results=batch_results,
                total_processed=len(titles),
                successful=batch_successful,
                failed=batch_failed
            )
            
        except Exception as e:
            logger.error(f"Error during AI title optimization: {str(e)}", exc_info=True)
            
            # Return all as failed with error message
            return schemas.OptimizeTitlesAIResponse(
                results=[
                    schemas.OptimizedTitleResult(
                        offer_id=t.offer_id,
                        current_title=t.current_title,
                        optimized_title=t.current_title,
                        analysis=None,
                        character_count=len(t.current_title),
                        success=False,
                        error=f"Błąd podczas optymalizacji: {str(e)}"
                    )
                    for t in titles
                ],
                total_processed=len(titles),
                successful=0,
                failed=len(titles)
            )
    
    @staticmethod
    async def _get_user_ai_config(user_id: int):
        """Get user AI configuration from database"""
        from app.db.session import SessionLocal
        
        db = SessionLocal()
        try:
            return AIConfigRepository.get_user_config(db, user_id)
        finally:
            db.close()


# Global instance
title_optimizer_service = TitleOptimizerService()

