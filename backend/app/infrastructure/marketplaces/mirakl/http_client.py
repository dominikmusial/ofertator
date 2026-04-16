"""HTTP client abstraction - Dependency Inversion Principle"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests
import time
import logging
from .types import HttpMethod
from .error_handler import MiraklErrorHandler, MiraklRateLimitError

logger = logging.getLogger(__name__)


@dataclass
class HttpResponse:
    """HTTP response wrapper"""
    status_code: int
    data: Any
    headers: Dict[str, str]


class IHttpClient(ABC):
    """Abstract HTTP client interface"""
    
    @abstractmethod
    def request(
        self,
        method: HttpMethod,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> HttpResponse:
        """Execute HTTP request"""
        pass


class RequestsHttpClient(IHttpClient):
    """HTTP client implementation using requests library"""
    
    def __init__(
        self,
        error_handler: MiraklErrorHandler,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self._error_handler = error_handler
        self._max_retries = max_retries
        self._retry_delay = retry_delay
    
    def request(
        self,
        method: HttpMethod,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> HttpResponse:
        """Execute HTTP request with retry logic"""
        
        for attempt in range(self._max_retries):
            try:
                response = self._execute_request(
                    method, url, headers, params, json_data, timeout
                )
                
                # Check for errors
                self._error_handler.handle_response(response)
                
                # Parse response
                return HttpResponse(
                    status_code=response.status_code,
                    data=response.json() if response.content else None,
                    headers=dict(response.headers)
                )
                
            except MiraklRateLimitError as e:
                if attempt < self._max_retries - 1:
                    wait_time = int(e.retry_after) if hasattr(e, 'retry_after') else 60
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                raise
                
            except requests.exceptions.Timeout:
                if attempt < self._max_retries - 1:
                    logger.warning(f"Timeout on attempt {attempt + 1}/{self._max_retries}")
                    time.sleep(self._retry_delay)
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise
        
        raise Exception("Max retries exceeded")
    
    def _execute_request(
        self,
        method: HttpMethod,
        url: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        timeout: int
    ) -> requests.Response:
        """Execute single HTTP request"""
        
        request_kwargs = {
            "url": url,
            "headers": headers,
            "params": params,
            "timeout": timeout
        }
        
        if method == HttpMethod.GET:
            return requests.get(**request_kwargs)
        elif method == HttpMethod.POST:
            return requests.post(**request_kwargs, json=json_data)
        elif method == HttpMethod.PUT:
            return requests.put(**request_kwargs, json=json_data)
        elif method == HttpMethod.DELETE:
            return requests.delete(**request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
