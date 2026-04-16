"""
Allegro-specific HTML content sanitization.

Allegro API has strict HTML validation rules:
- Allowed tags: h1, h2, p, ul, ol, li, b (lowercase only)
- No nested formatting in headers
- <b> and <li> tags MUST be inside container tags
- No orphaned tags outside containers
"""
import re
import logging

logger = logging.getLogger(__name__)


def sanitize_html_content(content: str) -> str:
    """
    Sanitize HTML content for Allegro API based on actual API validation.
    Allowed HTML tags: h1, h2, p, ul, ol, li, b
    Important restrictions:
    - h1 and h2 tags cannot contain nested formatting
    - Content must be wrapped in HTML tags (lowercase only)
    - <b> and <li> tags MUST be inside container tags (h1, h2, p, ul, ol)
    - No orphaned <b> or <li> tags outside containers
    """
    if not content:
        return "<p>Opis produktu</p>"
    
    # Clean up extra whitespace first
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    # Fix nested tags in h1 and h2 tags - Allegro specifically doesn't allow this
    # Remove any formatting inside headers
    content = re.sub(r'<(h[12])>\s*<b\b[^>]*>(.*?)</b>\s*</\1>', r'<\1>\2</\1>', content)
    content = re.sub(r'<(h[12])>\s*<strong\b[^>]*>(.*?)</strong>\s*</\1>', r'<\1>\2</\1>', content)
    content = re.sub(r'<(h[12])>\s*<em\b[^>]*>(.*?)</em>\s*</\1>', r'<\1>\2</\1>', content)
    content = re.sub(r'<(h[12])>\s*<i\b[^>]*>(.*?)</i>\s*</\1>', r'<\1>\2</\1>', content)
    
    # Remove any other nested formatting tags from h1/h2
    def fix_complex_nested_headers(match):
        tag = match.group(1)
        inner_content = match.group(2)
        # Remove HTML tags from headers but keep the content
        clean_content = re.sub(r'<[^>]*>', '', inner_content)
        return f'<{tag}>{clean_content}</{tag}>'
    
    # Apply to headers that still contain nested tags
    content = re.sub(r'<(h[12])>([^<]*<[^>]+>[^<]*)</\1>', fix_complex_nested_headers, content)
    
    # Fix <br> tags - not allowed by Allegro API, replace with proper spacing
    content = re.sub(r'<br\s*/?>', ' ', content)
    
    # Remove disallowed HTML tags while preserving allowed ones
    # Allowed: h1, h2, p, ul, ol, li, b (but b and li must be inside containers)
    # Remove: strong, em, i, u, s, span, div, section, article, etc.
    content = re.sub(r'</?(?:strong|em|i|u|s|span|div|section|article)\b[^>]*>', '', content)
    
    # Escape special characters that could break the API
    content = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);)', '&amp;', content)
    
    # Fix malformed HTML structures that might cause validation errors
    # Ensure proper nesting and no orphaned tags
    content = re.sub(r'<([^>]+)>\s*</\1>', '', content)  # Remove empty tags
    
    # Fix content that has plain text mixed with HTML tags (common issue from logs)
    # This handles cases like "<h1>Title</h1> plain text with <b>bold</b>" which causes validation errors
    
    # First, fix text that appears after closing tags but before opening tags
    def fix_text_between_tags(content):
        # Pattern: "</tag> text with possible <b> tags <tag>"
        # This catches text between HTML tags that should be wrapped in <p>
        pattern = r'(</(h[12]|p|ul|ol|li)>)\s*([^<]+(?:<b>[^<]*</b>[^<]*)*)\s*(<(?:h[12]|p|ul|ol|li)\b)'
        
        def replace_between_tags(match):
            closing_tag = match.group(1)
            text_content = match.group(3).strip()
            opening_tag = match.group(4)
            
            if text_content:
                return f"{closing_tag}<p>{text_content}</p>{opening_tag}"
            return f"{closing_tag}{opening_tag}"
        
        return re.sub(pattern, replace_between_tags, content)
    
    content = fix_text_between_tags(content)
    
    # Fix content that starts with plain text before HTML tags
    def fix_leading_text(match):
        leading_text = match.group(1).strip()
        rest_of_content = match.group(2)
        if leading_text:
            return f"<p>{leading_text}</p>{rest_of_content}"
        return rest_of_content
    
    # Pattern to catch plain text before the first HTML tag
    content = re.sub(r'^([^<]+)(<.+)$', fix_leading_text, content, flags=re.DOTALL)
    
    # Fix content that ends with plain text after HTML tags
    def fix_trailing_text(match):
        html_content = match.group(1)
        trailing_text = match.group(2).strip()
        if trailing_text:
            return f"{html_content}<p>{trailing_text}</p>"
        return html_content
    
    # Pattern to catch plain text after the last HTML tag
    content = re.sub(r'(.*>)\s*([^<]+)$', fix_trailing_text, content, flags=re.DOTALL)
    
    # Fix orphaned <b> tags that are not inside container tags
    # This catches patterns like: "</p> <b>text</b>" or " <b>text</b> <h1>"
    def wrap_orphaned_b_tags(content):
        # Pattern to find <b> tags that are not inside h1, h2, p, ul, ol
        # Look for <b> tags that appear after closing tags or at start without opening container
        pattern = r'(\s*)(<b>[^<]*</b>)(\s*)(?=<(?:h[12]|p|ul|ol)\b|$)'
        
        def replace_orphaned_b(match):
            whitespace_before = match.group(1)
            b_content = match.group(2)
            whitespace_after = match.group(3)
            return f"{whitespace_before}<p>{b_content}</p>{whitespace_after}"
        
        return re.sub(pattern, replace_orphaned_b, content)
    
    content = wrap_orphaned_b_tags(content)
    
    # If content doesn't contain any HTML tags, wrap it in <p> tags
    if not re.search(r'<[^>]+>', content):
        content = f"<p>{content}</p>"
    
    # If content is still empty after processing, provide basic content
    if not content or content.isspace():
        content = "<p>Opis produktu</p>"
    
    logger.debug(f"Sanitized content: {content[:100]}...")
    return content
