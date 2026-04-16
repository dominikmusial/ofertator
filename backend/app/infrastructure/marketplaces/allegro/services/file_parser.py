"""
Service for parsing Excel and CSV files for price schedule import
"""
import pandas as pd
from typing import List, Dict, Any, Tuple
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class FileParserError(Exception):
    """Custom exception for file parsing errors"""
    pass


def parse_schedule_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Parse Excel or CSV file and extract schedule data.

    Expected format:
    | ID Oferty | SKU | Nazwa Oferty | Cena Promocyjna | 1 | 2 | 3 | ... | 31 |

    Where columns 1-31 represent days of the month, and 'x' marks active days.
    SKU column is optional.

    Args:
        file_content: Raw file bytes
        filename: Original filename to determine format

    Returns:
        List of dicts with keys: offer_id, sku, offer_name, scheduled_price, days

    Raises:
        FileParserError: If file format is invalid
    """
    try:
        # Determine file type and read accordingly
        if filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        elif filename.endswith('.csv'):
            # Try multiple encodings to handle different CSV formats
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1250']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(BytesIO(file_content), encoding=encoding)
                    logger.info(f"Successfully read CSV with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise FileParserError("Nie udało się odczytać pliku CSV. Sprawdź kodowanie pliku.")
        else:
            raise FileParserError(f"Nieobsługiwany format pliku: {filename}. Użyj .xlsx lub .csv")

        # Log actual columns found in file
        logger.info(f"Columns found in file: {list(df.columns)}")

        # Validate required columns
        required_base_columns = ['ID Oferty', 'Nazwa Oferty', 'Cena Promocyjna']
        day_columns = [str(i) for i in range(1, 32)]  # "1", "2", ..., "31"

        missing_columns = []
        for col in required_base_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}. Found columns: {list(df.columns)}")
            raise FileParserError(f"Brakujące kolumny: {', '.join(missing_columns)}")

        # Check if day columns exist
        missing_day_columns = [day for day in day_columns if day not in df.columns]
        if missing_day_columns:
            raise FileParserError(
                f"Brakujące kolumny dni: {', '.join(missing_day_columns)}. "
                f"Plik musi zawierać kolumny od '1' do '31'"
            )

        # Parse rows
        parsed_rows = []
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['ID Oferty']) or row['ID Oferty'] == '':
                    continue

                offer_id = str(row['ID Oferty']).strip()

                # SKU is optional - extract if column exists
                sku = None
                if 'SKU' in df.columns and pd.notna(row['SKU']) and row['SKU'] != '':
                    sku = str(row['SKU']).strip()

                offer_name = str(row['Nazwa Oferty']).strip() if pd.notna(row['Nazwa Oferty']) else ''
                scheduled_price = str(row['Cena Promocyjna']).strip()

                # Extract active days (where value is 'x', 'X', '1', 'true', or True)
                active_days = []
                for day in range(1, 32):
                    day_col = str(day)
                    cell_value = row[day_col]

                    # Check if day is marked as active
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip().lower()
                        if cell_str in ['x', '1', 'true', 'tak', 'yes']:
                            active_days.append(day)

                parsed_rows.append({
                    'offer_id': offer_id,
                    'sku': sku,
                    'offer_name': offer_name,
                    'scheduled_price': scheduled_price,
                    'days': active_days,
                    'row_number': index + 2  # +2 because: 0-indexed + 1 for header row
                })

            except Exception as e:
                logger.error(f"Error parsing row {index + 2}: {e}")
                raise FileParserError(f"Błąd w wierszu {index + 2}: {str(e)}")

        if not parsed_rows:
            raise FileParserError("Plik nie zawiera żadnych prawidłowych wierszy z danymi")

        logger.info(f"Successfully parsed {len(parsed_rows)} rows from {filename}")
        return parsed_rows

    except FileParserError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing file: {e}")
        raise FileParserError(f"Błąd podczas odczytu pliku: {str(e)}")


def generate_template_excel() -> bytes:
    """
    Generate an Excel template file for price schedules.

    Returns:
        Excel file content as bytes
    """
    # Create column headers with SKU after ID Oferty
    columns = ['ID Oferty', 'SKU', 'Nazwa Oferty', 'Cena Promocyjna']
    columns.extend([str(i) for i in range(1, 32)])  # Days 1-31

    # Create empty DataFrame with just headers
    df = pd.DataFrame(columns=columns)

    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Harmonogram Cen')

        # Get workbook and worksheet for styling
        workbook = writer.book
        worksheet = writer.sheets['Harmonogram Cen']

        # Auto-size columns (approximate)
        worksheet.column_dimensions['A'].width = 15  # ID Oferty
        worksheet.column_dimensions['B'].width = 15  # SKU
        worksheet.column_dimensions['C'].width = 30  # Nazwa Oferty
        worksheet.column_dimensions['D'].width = 18  # Cena Promocyjna

        # Day columns (1-31) - smaller width
        for i in range(5, 36):  # Columns E-AI (days 1-31)
            col_letter = worksheet.cell(row=1, column=i).column_letter
            worksheet.column_dimensions[col_letter].width = 4

    output.seek(0)
    return output.read()


def generate_template_csv() -> str:
    """
    Generate a CSV template file for price schedules.

    Returns:
        CSV file content as string with UTF-8 BOM for Excel compatibility
    """
    # Create column headers with SKU after ID Oferty
    columns = ['ID Oferty', 'SKU', 'Nazwa Oferty', 'Cena Promocyjna']
    columns.extend([str(i) for i in range(1, 32)])  # Days 1-31

    # Create empty DataFrame with just headers
    df = pd.DataFrame(columns=columns)

    # Write to CSV with UTF-8 BOM (Excel compatibility for Polish characters)
    # BOM (Byte Order Mark) helps Excel recognize UTF-8 encoding
    csv_content = df.to_csv(index=False, encoding='utf-8-sig')
    return csv_content


def validate_file_size(file_content: bytes, max_size_mb: int = 5) -> None:
    """
    Validate file size.

    Args:
        file_content: Raw file bytes
        max_size_mb: Maximum allowed size in megabytes

    Raises:
        FileParserError: If file is too large
    """
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise FileParserError(
            f"Plik jest za duży ({size_mb:.2f}MB). Maksymalny rozmiar to {max_size_mb}MB"
        )
