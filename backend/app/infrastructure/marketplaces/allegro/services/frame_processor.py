import requests
from PIL import Image
from io import BytesIO
import logging
from typing import Optional, Dict, Any
from app.services.minio_service import minio_service
import uuid

logger = logging.getLogger(__name__)

class FrameProcessorService:
    """
    Service for applying frames to images based on the old app functionality.
    Supports both custom frames from uploaded images and frame scaling.
    """
    
    def apply_frame(self, image_url: str, frame_url: str, scale_factor: Optional[int] = None, save_to_storage: bool = True) -> str:
        """
        Apply frame to processed image with proper scaling.
        
        Args:
            image_url: URL of the image to frame
            frame_url: URL of the frame to apply
            scale_factor: Optional size in pixels for the content area.
                         If None, uses the default size of 2235px
                         Range: 1792px (70%) to 2560px (100%)
            save_to_storage: Deprecated parameter, kept for backwards compatibility. Images are always uploaded.
        
        Returns:
            str: URL of the processed image with frame applied, or original URL on error
        """
        try:
            logger.info(f"Applying frame to image: {image_url} with frame: {frame_url}")
            
            # Download the original image
            image = self._download_image(image_url)
            if not image:
                logger.error(f"Failed to download image: {image_url}")
                return image_url
            
            # Download the frame
            frame = self._download_image(frame_url)
            if not frame:
                logger.error(f"Failed to download frame: {frame_url}")
                return image_url
            
            # Apply the frame with scaling
            framed_image = self._apply_frame_to_image(image, frame, scale_factor)
            
            # Always upload framed images - they need to be accessible for Allegro offers
            processed_url = self._upload_processed_image(framed_image, save_to_storage=True)
            logger.info(f"Successfully applied frame. New URL: {processed_url}")
            
            return processed_url if processed_url else image_url
            
        except Exception as e:
            logger.error(f"Error applying frame to image {image_url}: {e}")
            return image_url  # Return original URL on error
    
    def apply_custom_frame(self, image_url: str, frame_number: int, account_name: str) -> str:
        """
        Apply custom frame to the image based on frame number.
        
        Args:
            image_url: URL of the image to frame
            frame_number: Number of the frame (1-6)
            account_name: Account name for getting custom frame
        
        Returns:
            str: URL of the processed image with custom frame applied
        """
        try:
            logger.info(f"Applying custom frame {frame_number} to image: {image_url}")
            
            # Download the original image
            image = self._download_image(image_url)
            if not image:
                logger.error(f"Failed to download image: {image_url}")
                return image_url
            
            # Get custom frame URL
            frame_url = f"https://upload.byst.re/{account_name}/Custom{frame_number}.png"
            
            # Download the custom frame
            try:
                frame_response = requests.get(frame_url)
                frame_response.raise_for_status()
                frame = Image.open(BytesIO(frame_response.content)).convert('RGBA')
            except Exception as e:
                logger.error(f"Failed to download custom frame {frame_number}: {e}")
                return image_url
            
            # Apply the custom frame
            framed_image = self._apply_custom_frame_to_image(image, frame)
            
            # Upload the processed image
            processed_url = self._upload_processed_image(framed_image)
            logger.info(f"Successfully applied custom frame {frame_number}. New URL: {processed_url}")
            
            return processed_url
            
        except Exception as e:
            logger.error(f"Error applying custom frame {frame_number} to image {image_url}: {e}")
            return image_url  # Return original URL on error
    
    def _download_image(self, image_url: str) -> Optional[Image.Image]:
        """Download and convert image to RGBA format."""
        try:
            # Replace public MinIO URL with internal URL for inter-container communication
            from app.core.config import settings
            internal_image_url = image_url.replace(settings.MINIO_PUBLIC_URL, settings.MINIO_INTERNAL_URL)
            
            response = requests.get(internal_image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert('RGBA')
            return image
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            # Fallback: try with the original public URL if internal URL fails
            logger.info(f"Attempting fallback with public URL: {image_url}")
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert('RGBA')
                logger.info(f"Successfully downloaded using public URL: {image_url}")
                return image
            except Exception as fallback_error:
                logger.error(f"Fallback download also failed for {image_url}: {fallback_error}")
                return None
    
    def _apply_frame_to_image(self, image: Image.Image, frame: Image.Image, scale_factor: Optional[int] = None) -> Image.Image:
        """
        Apply frame to processed image with proper scaling.
        Based on the old app's apply_frame function.
        """
        # Get frame dimensions
        bg_width, bg_height = frame.size
        
        # Use provided scale factor (in pixels) or default
        if scale_factor is not None:
            # Use the provided pixel value directly
            final_width = int(scale_factor)
            final_height = int(scale_factor)
        else:
            # Use default scale factor
            final_width = 2235  # Default size in pixels
            final_height = 2235
        
        # Ensure values are within valid range
        max_size = min(bg_width, bg_height)
        final_width = min(final_width, max_size)
        final_height = min(final_height, max_size)

        # Calculate dimensions maintaining aspect ratio
        width, height = image.size
        aspect_ratio = width / height
        if aspect_ratio > 1:
            new_width = final_width
            new_height = int(new_width / aspect_ratio)
            if new_height > final_height:
                new_height = final_height
                new_width = int(new_height * aspect_ratio)
        else:
            new_height = final_height
            new_width = int(new_height * aspect_ratio)
            if new_width > final_width:
                new_width = final_width
                new_height = int(new_width / aspect_ratio)

        # Resize and compose the image with frame
        resized_img = image.resize((new_width, new_height), Image.LANCZOS)
        result = Image.new('RGBA', (bg_width, bg_height), (0, 0, 0, 0))
        paste_x = (bg_width - new_width) // 2
        paste_y = (bg_height - new_height) // 2
        result.paste(resized_img, (paste_x, paste_y), resized_img)
        result.paste(frame, (0, 0), frame)
        
        return result
    
    def _apply_custom_frame_to_image(self, image: Image.Image, frame: Image.Image) -> Image.Image:
        """
        Apply custom frame to the image based on the old app's apply_custom_frame function.
        """
        # Ensure frame and image are the same size
        if frame.size != image.size:
            frame = frame.resize(image.size, Image.LANCZOS)
        
        # Create new image for the result
        result = Image.new('RGBA', image.size, (0, 0, 0, 0))
        
        # Paste the original image
        result.paste(image, (0, 0), image if image.mode == 'RGBA' else None)
        
        # Overlay the frame
        result.paste(frame, (0, 0), frame)
        
        return result
    
    def _upload_processed_image(self, image: Image.Image, save_to_storage: bool = True) -> str:
        """
        Upload processed image to MinIO and return public URL.
        
        Args:
            image: PIL Image object to upload
            save_to_storage: Deprecated parameter, kept for backwards compatibility
        
        Returns:
            str: Public URL of uploaded image
        """
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        unique_filename = f"{uuid.uuid4()}_framed.png"
        
        public_url = minio_service.upload_file(
            bucket_name="allegro-images",
            file_name=unique_filename,
            file_data=buffer.getvalue(),
            content_type="image/png"
        )
        return public_url

# Create a singleton instance
frame_processor_service = FrameProcessorService()
