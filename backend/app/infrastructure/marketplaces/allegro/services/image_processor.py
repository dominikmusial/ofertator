import requests
from PIL import Image, ImageFilter
from io import BytesIO
import rembg
import uuid
import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)

class ImageProcessorService:
    def _download_image(self, image_url: str) -> Image.Image:
        """Download image from URL and convert to PIL Image."""
        try:
            # Replace public MinIO URL with internal URL for inter-container communication
            from app.core.config import settings
            internal_image_url = image_url.replace(settings.MINIO_PUBLIC_URL, settings.MINIO_INTERNAL_URL)
            response = requests.get(internal_image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            return image
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {e}")
            return None

    def _upload_processed_image(self, image: Image.Image, save_to_storage: bool = True) -> str:
        """
        Upload processed image to MinIO storage.
        
        Args:
            image: PIL Image object to upload
            save_to_storage: Deprecated parameter, kept for backwards compatibility
        
        Returns:
            str: Public URL of uploaded image
        """
        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            
            unique_filename = f"{uuid.uuid4()}_processed.png"
            
            public_url = minio_service.upload_file(
                bucket_name="allegro-images",
                file_name=unique_filename,
                file_data=buffer.getvalue(),
                content_type="image/png"
            )
            return public_url
        except Exception as e:
            logger.error(f"Error uploading processed image: {e}")
            return None

    def detect_main_object(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the main object in the image using various CV techniques.
        
        Returns:
            tuple: (center_x, center_y, width, height) of the main object or None if detection fails
        """
        try:
            # Convert PIL image to CV2 format
            cv_image = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply GaussianBlur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find the largest contour by area
            main_contour = max(contours, key=cv2.contourArea)
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(main_contour)
            
            # Calculate center of the bounding box
            center_x = x + w//2
            center_y = y + h//2
            
            return (center_x, center_y, w, h)
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return None

    def is_white_background(self, image: Image.Image, threshold: float = 0.15, white_threshold: int = 240, border_size: int = 10) -> bool:
        """
        Check if image has a white background.
        
        Args:
            image: PIL Image object
            threshold: Minimum percentage of white pixels to consider as white background (default 0.15 or 15%)
            white_threshold: RGB value threshold for considering a pixel as white (default 240)
            border_size: Size of border to check in pixels (default 10)
        
        Returns:
            bool: True if image has white background, False otherwise
        """
        try:
            # Convert image to RGB if it's not
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for faster processing
            img_array = np.array(image)
            
            # Get dimensions
            height, width = img_array.shape[:2]
            
            # Check border pixels
            top_border = img_array[:border_size, :, :]
            bottom_border = img_array[-border_size:, :, :]
            left_border = img_array[:, :border_size, :]
            right_border = img_array[:, -border_size:, :]
            
            # Combine all border pixels
            border_pixels = np.concatenate([
                top_border.reshape(-1, 3),
                bottom_border.reshape(-1, 3),
                left_border.reshape(-1, 3),
                right_border.reshape(-1, 3)
            ])
            
            # Check if border is white
            border_white_pixels = np.all(border_pixels >= white_threshold, axis=1)
            border_white_percentage = np.mean(border_white_pixels)
            
            # Check entire image
            white_pixels = np.all(img_array >= white_threshold, axis=2)
            total_white_percentage = np.mean(white_pixels)
            
            logger.debug(f"Border white percentage: {border_white_percentage * 100:.2f}%")
            logger.debug(f"Total white pixel percentage: {total_white_percentage * 100:.2f}%")
            
            # Image is considered to have white background if:
            # 1. Total white pixels are above threshold AND
            # 2. Border is at least 95% white
            return total_white_percentage >= threshold and border_white_percentage >= 0.95
        except Exception as e:
            logger.error(f"Error checking white background: {e}")
            return False

    def is_square(self, image: Image.Image, tolerance: float = 0.05) -> bool:
        """
        Check if image is approximately square.
        
        Args:
            image: PIL Image object
            tolerance: Allowed difference between width and height as a percentage (default 0.05 or 5%)
        
        Returns:
            bool: True if image is square within tolerance, False otherwise
        """
        try:
            width, height = image.size
            max_dim = max(width, height)
            ratio = abs(width - height) / max_dim
            
            return ratio <= tolerance
        except Exception as e:
            logger.error(f"Error checking if image is square: {e}")
            return False

    def add_blur_effect(self, image: Image.Image) -> Image.Image:
        """
        Add background effect by:
        1. Creating a square background from the original image
        2. Applying 60% blur to the background
        3. Darkening the background by 30% (preserving alpha channel)
        4. Placing the original image centered on the blurred, darkened background
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Image with blurred background effect
        """
        try:
            # Convert to RGBA if not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Calculate target square size based on the larger dimension
            target_size = max(image.width, image.height)
            
            # Calculate position to paste the original image
            paste_x = (target_size - image.width) // 2
            paste_y = (target_size - image.height) // 2
            
            # Create the final square image with the original image as background
            # but blurred and darkened
            background = image.resize((target_size, target_size), Image.LANCZOS)
            
            # Apply strong blur (60%)
            blur_radius = int(target_size * 0.05)  # 5% of image size for blur radius
            background = background.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            # Darken the background by 30%
            background_data = background.getdata()
            darkened_data = []
            
            for item in background_data:
                # Reduce RGB values by 30% but keep alpha channel
                if len(item) == 4:  # RGBA
                    darkened_data.append((
                        int(item[0] * 0.7),
                        int(item[1] * 0.7),
                        int(item[2] * 0.7),
                        item[3]
                    ))
                else:  # RGB
                    darkened_data.append((
                        int(item[0] * 0.7),
                        int(item[1] * 0.7),
                        int(item[2] * 0.7)
                    ))
            
            background.putdata(darkened_data)
            
            # Create a new image with the blurred background
            result = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
            result.paste(background, (0, 0))
            
            # Paste the original image on top
            result.paste(image, (paste_x, paste_y), image)
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding blur effect: {e}")
            return image  # Return original image if processing fails

    def remove_background_advanced(self, image: Image.Image) -> Image.Image:
        """
        Advanced background removal using rembg with enhanced quality settings.
        Always attempts to remove background regardless of background color.
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Image with background removed
        """
        try:
            # Convert to RGBA if not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Always attempt background removal with rembg
            session = rembg.new_session(
                "u2net",  # Use u2net model for better quality
                providers=['CPUExecutionProvider']  # Use CPU for compatibility
            )
            
            # Convert to bytes for rembg
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Remove background
            output_bytes = rembg.remove(img_byte_arr, session=session)
            image_no_bg = Image.open(BytesIO(output_bytes)).convert('RGBA')
            
            # Create a transparent background centered in a square
            width, height = image_no_bg.size
            size = max(width, height)
            result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Calculate position to paste the no-background image
            paste_x = (size - width) // 2
            paste_y = (size - height) // 2
            
            # Paste the no-background image
            result.paste(image_no_bg, (paste_x, paste_y), image_no_bg)
            
            return result
        except Exception as e:
            logger.error(f"Error in background removal: {e}")
            return image  # Return original image if processing fails

    def crop_to_square_advanced(self, image: Image.Image) -> Image.Image:
        """
        Crop image to square using simple center crop.
        Always crops from the center of the image without any smart detection.
        
        Args:
            image: PIL Image object
        
        Returns:
            PIL Image: Square cropped image centered
        """
        try:
            # Check if image is already square
            if self.is_square(image):
                logger.debug("Image is already square - skipping crop")
                return image
                
            # Check if image has white background
            if self.is_white_background(image):
                logger.debug("White background detected - skipping crop")
                return image
                
            logger.debug("Cropping image to square using center crop")
            
            # Get image dimensions
            width, height = image.size
            new_size = min(width, height)
            
            # Always use simple center crop - no smart detection
            left = (width - new_size) // 2
            top = (height - new_size) // 2
            right = left + new_size
            bottom = top + new_size
            
            logger.debug(f"Center crop coordinates: left={left}, top={top}, right={right}, bottom={bottom}")
            return image.crop((left, top, right, bottom))
            
        except Exception as e:
            logger.error(f"Error cropping to square: {e}")
            return image

    def process_image_by_mode(self, image: Image.Image, mode: str) -> Image.Image:
        """
        Process image according to selected mode.
        
        Args:
            image: PIL Image object
            mode: String indicating processing mode
            
        Returns:
            PIL Image: Processed image
        """
        try:
            logger.info(f"Processing image with mode: {mode}")
            
            # Map Polish mode names to English for backwards compatibility
            mode_mapping = {
                "Oryginalny": "Original",
                "Przytnij do kwadratu": "Crop to square",
                "Efekt rozmycia": "Blurred effect",
                "Usunięcie tła + Efekt rozmycia": "Background removal + Blurred effect",
                "Usunięcie tła + Przytnij do kwadratu": "Background removal + Crop to square"
            }
            
            # Convert Polish mode name to English if necessary
            english_mode = mode_mapping.get(mode, mode)
            
            if english_mode == "Original":
                return image
                
            elif english_mode == "Crop to square":
                # Check if image is already square
                if self.is_square(image):
                    logger.debug("Image is already square - skipping crop")
                    return image
                    
                return self.crop_to_square_advanced(image)
                
            elif english_mode == "Blurred effect":
                # Apply blur effect only if image is NOT square AND does NOT have white background
                has_white_bg = self.is_white_background(image)
                is_img_square = self.is_square(image)
                
                logger.info(f"Blur effect check: white_bg={has_white_bg}, square={is_img_square}, size={image.size}")
                
                if has_white_bg:
                    logger.info("White background detected - skipping blur effect")
                    return image
                    
                if is_img_square:
                    logger.info("Image is already square - skipping blur effect")
                    return image
                    
                logger.info("Applying blur effect")
                return self.add_blur_effect(image)
                
            elif english_mode == "Background removal + Blurred effect":
                # First remove background, then add blur effect
                logger.info("Applying background removal + blur effect")
                no_bg = self.remove_background_advanced(image)
                logger.info(f"Background removed, now applying blur to result with size: {no_bg.size}")
                return self.add_blur_effect(no_bg)
                
            elif english_mode == "Background removal + Crop to square":
                # First remove background, then crop to square
                logger.info("Applying background removal + crop to square")
                no_bg = self.remove_background_advanced(image)
                logger.info(f"Background removed, now cropping to square result with size: {no_bg.size}")
                return self.crop_to_square_advanced(no_bg)
                
            elif english_mode == "Background removal":
                return self.remove_background_advanced(image)
                
            else:
                logger.warning(f"Unknown mode: {mode} (English: {english_mode})")
                return image
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return image  # Return original image if processing fails

    # Legacy API methods for backward compatibility
    def remove_background(self, image_url: str) -> str:
        """
        Removes the background from an image.
        """
        try:
            image = self._download_image(image_url)
            if not image:
                return image_url
            
            processed_image = self.remove_background_advanced(image)
            return self._upload_processed_image(processed_image)
        except Exception as e:
            logger.error(f"Error in remove_background: {e}")
            return image_url

    def crop_to_square(self, image_url: str) -> str:
        """
        Crop image to square with object detection.
        """
        try:
            image = self._download_image(image_url)
            if not image:
                return image_url
            
            processed_image = self.crop_to_square_advanced(image)
            return self._upload_processed_image(processed_image)
        except Exception as e:
            logger.error(f"Error in crop_to_square: {e}")
            return image_url

    def add_blur_effect_url(self, image_url: str) -> str:
        """
        Add blur effect to image from URL.
        """
        try:
            image = self._download_image(image_url)
            if not image:
                return image_url
            
            processed_image = self.add_blur_effect(image)
            return self._upload_processed_image(processed_image)
        except Exception as e:
            logger.error(f"Error in add_blur_effect: {e}")
            return image_url

    def process_image_by_mode_url(self, image_url: str, mode: str, save_to_storage: bool = True) -> str:
        """
        Process image from URL according to selected mode.
        
        Args:
            image_url: URL of the image to process
            mode: Processing mode (Oryginalny, Przytnij do kwadratu, etc.)
            save_to_storage: Deprecated parameter, kept for backwards compatibility. Images are always uploaded.
        
        Returns:
            str: URL of processed image, or original URL on error
        """
        try:
            image = self._download_image(image_url)
            if not image:
                return image_url
            
            processed_image = self.process_image_by_mode(image, mode)
            
            # Always upload processed images - they need to be accessible for Allegro offers
            processed_url = self._upload_processed_image(processed_image, save_to_storage=True)
            return processed_url if processed_url else image_url
        except Exception as e:
            logger.error(f"Error in process_image_by_mode_url: {e}")
            return image_url

image_processor_service = ImageProcessorService()
