"""CAS Parser — parse CAMS/KFintech CAS PDFs, NSDL/CDSL demat statements, broker CSV/Excel files.

Wraps casparser library for CAS PDFs. Provides fallback parsers for demat statements
and broker trade files. All parsed data is normalized into a standard transaction format
that maps directly to the ParsedTransaction model.
"""
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("beyond_risk.cas_parser")

# Standard transaction types recognized by the system
VALID_TRANSACTION_TYPES = {
    "PURCHASE",
    "PURCHASE_SIP",
    "REDEMPTION",
    "SWITCH_IN",
    "SWITCH_OUT",
    "DIVIDEND_PAYOUT",
    "DIVIDEND_REINVEST",
}

# casparser transaction type mapping — casparser uses its own naming conventions
_CASPARSER_TYPE_MAP = {
    "PURCHASE": "PURCHASE",
    "PURCHASE_SIP": "PURCHASE_SIP",
    "SYSTEMATIC_INVESTMENT": "PURCHASE_SIP",
    "SIP": "PURCHASE_SIP",
    "REDEMPTION": "REDEMPTION",
    "SWITCH_IN": "SWITCH_IN",
    "SWITCH IN": "SWITCH_IN",
    "SWITCH_OUT": "SWITCH_OUT",
    "SWITCH OUT": "SWITCH_OUT",
    "DIVIDEND_PAYOUT": "DIVIDEND_PAYOUT",
    "DIVIDEND PAYOUT": "DIVIDEND_PAYOUT",
    "PAYOUT": "DIVIDEND_PAYOUT",
    "DIVIDEND_REINVEST": "DIVIDEND_REINVEST",
    "DIVIDEND REINVESTMENT": "DIVIDEND_REINVEST",
    "REINVESTMENT": "DIVIDEND_REINVEST",
    "REINVEST": "DIVIDEND_REINVEST",
    "STAMP_DUTY": "PURCHASE",
    "MISC": "PURCHASE",
}

# Common column name variations across broker CSV/Excel files
_COLUMN_ALIASES = {
    "date": ["date", "trade_date", "tradedate", "transaction_date", "txn_date", "order_date", "trade date", "transaction date"],
    "type": ["type", "transaction_type", "txn_type", "trade_type", "action", "buy_sell", "buy/sell", "side"],
    "amount": ["amount", "value", "trade_value", "net_amount", "total_value", "consideration", "net amount", "trade value"],
    "units": ["units", "quantity", "qty", "shares", "no_of_units", "no. of units"],
    "nav": ["nav", "price", "rate", "trade_price", "unit_price", "avg_price", "average price"],
    "scheme_name": ["scheme_name", "scheme", "fund_name", "fund", "script", "symbol", "stock", "scrip", "instrument"],
    "isin": ["isin", "isin_code", "isin_no"],
    "folio_number": ["folio_number", "folio", "folio_no", "folio no"],
    "balance_units": ["balance_units", "balance", "closing_balance", "cum_units", "cumulative_units"],
}


def parse_cas_pdf(file_path: str, password: str) -> Dict[str, Any]:
    """Parse a CAMS or KFintech CAS PDF using the casparser library.

    casparser.read_cas_pdf() returns a structured dict with investor info,
    folios, schemes, and transactions. We wrap it with error handling and
    return a consistent response envelope.

    Args:
        file_path: Absolute path to the CAS PDF file.
        password: PDF password (typically the PAN or email used during CAS generation).

    Returns:
        {success: True, data: {investor_info, folios, schemes, transactions, ...}}
        or {success: False, error: "description of what went wrong"}
    """
    try:
        import casparser
    except ImportError:
        logger.error("casparser library not installed — run: pip install casparser")
        return {"success": False, "error": "casparser library is not installed. Install with: pip install casparser"}

    if not os.path.exists(file_path):
        logger.error("CAS PDF file not found: %s", file_path)
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        logger.info("Parsing CAS PDF: %s", os.path.basename(file_path))
        cas_data = casparser.read_cas_pdf(file_path, password)

        # casparser returns a CASData object — convert to dict for consistent handling
        if hasattr(cas_data, "to_dict"):
            parsed = cas_data.to_dict()
        elif hasattr(cas_data, "__dict__"):
            parsed = _casdata_to_dict(cas_data)
        else:
            parsed = cas_data

        # Extract summary stats for logging and metadata
        investor_info = parsed.get("investor_info", {})
        folios = parsed.get("folios", [])
        total_schemes = sum(len(f.get("schemes", [])) for f in folios)
        total_transactions = sum(
            len(s.get("transactions", []))
            for f in folios
            for s in f.get("schemes", [])
        )

        logger.info(
            "CAS parsed successfully — investor: %s, folios: %d, schemes: %d, transactions: %d",
            investor_info.get("name", "unknown"),
            len(folios),
            total_schemes,
            total_transactions,
        )

        return {
            "success": True,
            "data": parsed,
            "meta": {
                "investor_name": investor_info.get("name"),
                "investor_email": investor_info.get("email"),
                "investor_pan": _mask_pan(investor_info.get("pan", "")),
                "statement_from": parsed.get("statement_period", {}).get("from"),
                "statement_to": parsed.get("statement_period", {}).get("to"),
                "total_folios": len(folios),
                "total_schemes": total_schemes,
                "total_transactions": total_transactions,
                "cas_type": parsed.get("cas_type", "UNKNOWN"),
                "file_type": parsed.get("file_type", "UNKNOWN"),
            },
        }

    except Exception as exc:
        error_msg = str(exc)

        # Provide user-friendly error messages for common failures
        if "password" in error_msg.lower() or "decrypt" in error_msg.lower():
            logger.warning("CAS PDF password incorrect or file encrypted: %s", error_msg)
            return {"success": False, "error": "Incorrect password. CAS PDFs are typically password-protected with your PAN or email."}

        if "not a pdf" in error_msg.lower() or "invalid" in error_msg.lower():
            logger.warning("Invalid PDF file: %s", error_msg)
            return {"success": False, "error": "The uploaded file is not a valid PDF."}

        logger.error("Failed to parse CAS PDF: %s", error_msg, exc_info=True)
        return {"success": False, "error": f"Failed to parse CAS PDF: {error_msg}"}


def parse_demat_pdf(file_path: str) -> Dict[str, Any]:
    """Parse an NSDL or CDSL demat account statement PDF using pdfplumber.

    Demat statements contain holdings and transactions in tabular format.
    We extract all tables from every page and attempt to identify holdings
    vs transaction tables by their column headers.

    Args:
        file_path: Absolute path to the demat statement PDF.

    Returns:
        {success: True, data: {holdings: [...], transactions: [...], raw_tables: [...]}}
        or {success: False, error: "description"}
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber library not installed — run: pip install pdfplumber")
        return {"success": False, "error": "pdfplumber library is not installed. Install with: pip install pdfplumber"}

    if not os.path.exists(file_path):
        logger.error("Demat PDF file not found: %s", file_path)
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        logger.info("Parsing demat PDF: %s", os.path.basename(file_path))
        all_tables: List[List[List[str]]] = []
        holdings: List[Dict[str, Any]] = []
        transactions: List[Dict[str, Any]] = []
        full_text = ""

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text for header detection and file type identification
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"

                # Extract all tables from the page
                page_tables = page.extract_tables()
                if not page_tables:
                    continue

                for table in page_tables:
                    if not table or len(table) < 2:
                        continue

                    all_tables.append(table)
                    header_row = [str(cell).strip().lower() if cell else "" for cell in table[0]]

                    # Classify table by its header columns
                    if _is_holdings_table(header_row):
                        holdings.extend(_parse_holdings_table(table, page_num))
                    elif _is_transaction_table(header_row):
                        transactions.extend(_parse_transaction_table(table, page_num))

        # Detect whether NSDL or CDSL from extracted text
        demat_type = "UNKNOWN"
        text_upper = full_text.upper()
        if "NSDL" in text_upper or "NATIONAL SECURITIES DEPOSITORY" in text_upper:
            demat_type = "NSDL"
        elif "CDSL" in text_upper or "CENTRAL DEPOSITORY" in text_upper:
            demat_type = "CDSL"

        logger.info(
            "Demat PDF parsed — type: %s, tables: %d, holdings: %d, transactions: %d",
            demat_type,
            len(all_tables),
            len(holdings),
            len(transactions),
        )

        return {
            "success": True,
            "data": {
                "demat_type": demat_type,
                "holdings": holdings,
                "transactions": transactions,
                "raw_tables": all_tables,
                "total_pages": len(pdf.pages) if 'pdf' in dir() else 0,
            },
            "meta": {
                "demat_type": demat_type,
                "total_holdings": len(holdings),
                "total_transactions": len(transactions),
                "total_tables_extracted": len(all_tables),
            },
        }

    except Exception as exc:
        logger.error("Failed to parse demat PDF: %s", str(exc), exc_info=True)
        return {"success": False, "error": f"Failed to parse demat PDF: {str(exc)}"}


def parse_broker_csv(file_path: str) -> Dict[str, Any]:
    """Parse a broker trade file (CSV or Excel) with auto-detected column mapping.

    Supports CSV, XLS, and XLSX files. Attempts to detect which columns map to
    standard transaction fields by matching column names against known aliases
    used by Indian brokers (Zerodha, Groww, Angel One, ICICI Direct, etc.).

    Args:
        file_path: Absolute path to the CSV or Excel file.

    Returns:
        {success: True, data: {transactions: [...], columns_detected: {...}, raw_row_count: int}}
        or {success: False, error: "description"}
    """
    if not os.path.exists(file_path):
        logger.error("Broker file not found: %s", file_path)
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        logger.info("Parsing broker file: %s", os.path.basename(file_path))
        ext = os.path.splitext(file_path)[1].lower()

        # Read file into DataFrame based on extension
        if ext == ".csv":
            dataframe = _read_csv_with_encoding_fallback(file_path)
        elif ext in (".xls", ".xlsx"):
            dataframe = pd.read_excel(file_path, engine="openpyxl" if ext == ".xlsx" else "xlrd")
        else:
            return {"success": False, "error": f"Unsupported file format: {ext}. Expected CSV, XLS, or XLSX."}

        if dataframe.empty:
            return {"success": False, "error": "The uploaded file contains no data rows."}

        # Normalize column names for matching
        dataframe.columns = [str(col).strip().lower().replace(" ", "_") for col in dataframe.columns]

        # Auto-detect column mapping
        column_map = _detect_column_mapping(dataframe.columns.tolist())

        if not column_map.get("date"):
            return {
                "success": False,
                "error": "Could not detect a date column. Columns found: " + ", ".join(dataframe.columns.tolist()),
            }

        # Parse transactions from the DataFrame using detected column mapping
        transactions: List[Dict[str, Any]] = []
        parse_errors: List[str] = []

        for row_idx, row in dataframe.iterrows():
            try:
                txn = _parse_broker_row(row, column_map, row_idx)
                if txn:
                    transactions.append(txn)
            except Exception as row_exc:
                parse_errors.append(f"Row {row_idx + 1}: {str(row_exc)}")

        logger.info(
            "Broker file parsed — rows: %d, transactions: %d, errors: %d, columns mapped: %s",
            len(dataframe),
            len(transactions),
            len(parse_errors),
            list(column_map.keys()),
        )

        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "columns_detected": column_map,
                "raw_row_count": len(dataframe),
                "raw_columns": dataframe.columns.tolist(),
            },
            "meta": {
                "total_transactions": len(transactions),
                "parse_errors": parse_errors[:20],  # cap error list to avoid bloat
                "file_format": ext.lstrip(".").upper(),
            },
        }

    except Exception as exc:
        logger.error("Failed to parse broker file: %s", str(exc), exc_info=True)
        return {"success": False, "error": f"Failed to parse broker file: {str(exc)}"}


def detect_file_type(filename: str, content: bytes) -> str:
    """Detect the type of uploaded financial document.

    Examines the filename and file content to determine whether this is a
    CAMS CAS, KFintech CAS, NSDL demat statement, CDSL demat statement,
    or a broker CSV/Excel file.

    Args:
        filename: Original filename of the uploaded file.
        content: Raw file bytes (first few KB is sufficient for detection).

    Returns:
        One of: 'CAMS', 'KFINTECH', 'NSDL', 'CDSL', 'BROKER_CSV', or 'UNKNOWN'
    """
    filename_lower = filename.lower()
    ext = os.path.splitext(filename_lower)[1]

    # CSV/Excel files are broker trade files
    if ext in (".csv", ".xls", ".xlsx"):
        logger.info("File type detected as BROKER_CSV based on extension: %s", filename)
        return "BROKER_CSV"

    # For PDFs, examine content to distinguish CAS types and demat statements
    if ext == ".pdf":
        return _detect_pdf_type(content)

    logger.warning("Could not detect file type for: %s", filename)
    return "UNKNOWN"


def normalize_transactions(parsed_data: Dict[str, Any], file_type: str) -> List[Dict[str, Any]]:
    """Convert parsed data from any source into our standard transaction format.

    This is the unification layer — regardless of whether data came from a CAMS CAS,
    KFintech CAS, NSDL statement, CDSL statement, or broker CSV, the output is a
    flat list of transactions in a consistent format that maps to ParsedTransaction.

    Args:
        parsed_data: The 'data' dict from any of the parse_* functions.
        file_type: One of 'CAMS', 'KFINTECH', 'NSDL', 'CDSL', 'BROKER_CSV'.

    Returns:
        List of normalized transaction dicts ready for database insertion.
    """
    if not parsed_data:
        logger.warning("normalize_transactions called with empty parsed_data")
        return []

    try:
        if file_type in ("CAMS", "KFINTECH"):
            return _normalize_cas_transactions(parsed_data)
        elif file_type in ("NSDL", "CDSL"):
            return _normalize_demat_transactions(parsed_data)
        elif file_type == "BROKER_CSV":
            return _normalize_broker_transactions(parsed_data)
        else:
            logger.error("Unknown file_type for normalization: %s", file_type)
            return []

    except Exception as exc:
        logger.error("Failed to normalize transactions (file_type=%s): %s", file_type, str(exc), exc_info=True)
        return []


# ─── INTERNAL HELPERS: CAS DATA CONVERSION ───


def _casdata_to_dict(cas_data: Any) -> Dict[str, Any]:
    """Convert a casparser CASData object to a plain dict.

    casparser may return either a dict or a dataclass-style object depending
    on the version. This handles the object case by traversing its attributes.
    """
    result: Dict[str, Any] = {}

    # Investor info
    if hasattr(cas_data, "investor_info"):
        investor = cas_data.investor_info
        result["investor_info"] = {
            "name": getattr(investor, "name", None),
            "email": getattr(investor, "email", None),
            "address": getattr(investor, "address", None),
            "mobile": getattr(investor, "mobile", None),
            "pan": getattr(investor, "pan", None),
        }

    # Statement period
    if hasattr(cas_data, "statement_period"):
        period = cas_data.statement_period
        result["statement_period"] = {
            "from": str(getattr(period, "from_", getattr(period, "from", None))),
            "to": str(getattr(period, "to", None)),
        }

    # CAS type (CAMS or KFINTECH)
    result["cas_type"] = getattr(cas_data, "cas_type", "UNKNOWN")
    result["file_type"] = getattr(cas_data, "file_type", "UNKNOWN")

    # Folios with schemes and transactions
    folios = []
    for folio in getattr(cas_data, "folios", []):
        folio_dict: Dict[str, Any] = {
            "folio": getattr(folio, "folio", None),
            "amc": getattr(folio, "amc", None),
            "pan": getattr(folio, "pan", None),
            "KYC": getattr(folio, "KYC", None),
            "PANKYC": getattr(folio, "PANKYC", None),
        }

        schemes = []
        for scheme in getattr(folio, "schemes", []):
            scheme_dict: Dict[str, Any] = {
                "scheme": getattr(scheme, "scheme", None),
                "advisor": getattr(scheme, "advisor", None),
                "rta_code": getattr(scheme, "rta_code", None),
                "type": getattr(scheme, "type", None),
                "rta": getattr(scheme, "rta", None),
                "isin": getattr(scheme, "isin", None),
                "amfi": getattr(scheme, "amfi", None),
                "open": getattr(scheme, "open", None),
                "close": getattr(scheme, "close", None),
                "close_calculated": getattr(scheme, "close_calculated", None),
                "valuation": _safe_valuation(scheme),
            }

            txns = []
            for txn in getattr(scheme, "transactions", []):
                txn_dict = {
                    "date": str(getattr(txn, "date", None)),
                    "description": getattr(txn, "description", None),
                    "amount": _safe_float(getattr(txn, "amount", None)),
                    "units": _safe_float(getattr(txn, "units", None)),
                    "nav": _safe_float(getattr(txn, "nav", None)),
                    "balance": _safe_float(getattr(txn, "balance", None)),
                    "type": getattr(txn, "type", None),
                    "dividend_rate": _safe_float(getattr(txn, "dividend_rate", None)),
                }
                txns.append(txn_dict)

            scheme_dict["transactions"] = txns
            schemes.append(scheme_dict)

        folio_dict["schemes"] = schemes
        folios.append(folio_dict)

    result["folios"] = folios
    return result


def _safe_valuation(scheme: Any) -> Optional[Dict[str, Any]]:
    """Safely extract valuation info from a casparser scheme object."""
    val = getattr(scheme, "valuation", None)
    if val is None:
        return None
    return {
        "date": str(getattr(val, "date", None)),
        "nav": _safe_float(getattr(val, "nav", None)),
        "value": _safe_float(getattr(val, "value", None)),
    }


# ─── INTERNAL HELPERS: DEMAT PDF TABLE CLASSIFICATION ───


def _is_holdings_table(header_row: List[str]) -> bool:
    """Check if a table header row looks like a holdings table."""
    holdings_keywords = {"isin", "quantity", "security", "scrip", "market value", "face value"}
    header_text = " ".join(header_row)
    matches = sum(1 for kw in holdings_keywords if kw in header_text)
    return matches >= 2


def _is_transaction_table(header_row: List[str]) -> bool:
    """Check if a table header row looks like a transaction table."""
    txn_keywords = {"date", "transaction", "debit", "credit", "quantity", "settlement", "trade"}
    header_text = " ".join(header_row)
    matches = sum(1 for kw in txn_keywords if kw in header_text)
    return matches >= 2


def _parse_holdings_table(table: List[List[str]], page_num: int) -> List[Dict[str, Any]]:
    """Parse a demat holdings table into structured records."""
    if len(table) < 2:
        return []

    headers = [str(cell).strip().lower() if cell else "" for cell in table[0]]
    holdings = []

    for row in table[1:]:
        if not row or all(not cell for cell in row):
            continue

        holding: Dict[str, Any] = {"_source_page": page_num}
        for col_idx, cell in enumerate(row):
            if col_idx >= len(headers):
                break
            header = headers[col_idx]
            value = str(cell).strip() if cell else ""

            if "isin" in header:
                holding["isin"] = value
            elif "security" in header or "scrip" in header or "name" in header:
                holding["scheme_name"] = value
            elif "quantity" in header or "qty" in header or "balance" in header:
                holding["units"] = _safe_float(value)
            elif "market" in header and "value" in header:
                holding["market_value"] = _safe_float(value)
            elif "face" in header and "value" in header:
                holding["face_value"] = _safe_float(value)

        if holding.get("isin") or holding.get("scheme_name"):
            holdings.append(holding)

    return holdings


def _parse_transaction_table(table: List[List[str]], page_num: int) -> List[Dict[str, Any]]:
    """Parse a demat transaction table into structured records."""
    if len(table) < 2:
        return []

    headers = [str(cell).strip().lower() if cell else "" for cell in table[0]]
    transactions = []

    for row in table[1:]:
        if not row or all(not cell for cell in row):
            continue

        txn: Dict[str, Any] = {"_source_page": page_num}
        for col_idx, cell in enumerate(row):
            if col_idx >= len(headers):
                break
            header = headers[col_idx]
            value = str(cell).strip() if cell else ""

            if "date" in header:
                txn["date"] = value
            elif "isin" in header:
                txn["isin"] = value
            elif "security" in header or "scrip" in header or "name" in header:
                txn["scheme_name"] = value
            elif "debit" in header:
                txn["debit_units"] = _safe_float(value)
            elif "credit" in header:
                txn["credit_units"] = _safe_float(value)
            elif "quantity" in header or "qty" in header:
                txn["units"] = _safe_float(value)
            elif "transaction" in header and "type" in header:
                txn["type"] = value

        if txn.get("date"):
            transactions.append(txn)

    return transactions


# ─── INTERNAL HELPERS: BROKER CSV PARSING ───


def _read_csv_with_encoding_fallback(file_path: str) -> pd.DataFrame:
    """Read a CSV file, trying multiple encodings commonly used by Indian brokers."""
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            dataframe = pd.read_csv(file_path, encoding=encoding, skipinitialspace=True)
            if not dataframe.empty:
                return dataframe
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as exc:
            logger.warning("CSV read failed with encoding %s: %s", encoding, str(exc))
            continue

    # Last resort: read with errors='replace' to avoid encoding failures
    return pd.read_csv(file_path, encoding="utf-8", errors="replace", skipinitialspace=True)


def _detect_column_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    """Auto-detect which DataFrame columns map to our standard fields.

    Returns a dict like {'date': 'trade_date', 'amount': 'net_amount', ...}
    where values are the actual column names found in the file.
    """
    mapping: Dict[str, Optional[str]] = {}

    for standard_field, aliases in _COLUMN_ALIASES.items():
        matched_col = None
        for alias in aliases:
            normalized_alias = alias.strip().lower().replace(" ", "_")
            if normalized_alias in columns:
                matched_col = normalized_alias
                break

        # Fuzzy fallback: check if any column contains the standard field name
        if not matched_col:
            for col in columns:
                if standard_field in col:
                    matched_col = col
                    break

        mapping[standard_field] = matched_col

    return mapping


def _parse_broker_row(row: pd.Series, column_map: Dict[str, Optional[str]], row_idx: int) -> Optional[Dict[str, Any]]:
    """Parse a single row from a broker CSV/Excel into a transaction dict."""
    date_col = column_map.get("date")
    if not date_col or pd.isna(row.get(date_col)):
        return None

    txn: Dict[str, Any] = {}

    # Parse date
    raw_date = row.get(date_col)
    txn["date"] = _parse_date_flexible(str(raw_date))
    if txn["date"] is None:
        return None

    # Parse transaction type
    type_col = column_map.get("type")
    if type_col and not pd.isna(row.get(type_col, None)):
        txn["type"] = _map_broker_type(str(row[type_col]))
    else:
        txn["type"] = "PURCHASE"  # default when type column is missing

    # Parse numeric fields
    for field in ("amount", "units", "nav", "balance_units"):
        col = column_map.get(field)
        if col and not pd.isna(row.get(col, None)):
            txn[field] = _safe_float(row[col])
        else:
            txn[field] = None

    # Parse text fields
    for field in ("scheme_name", "isin", "folio_number"):
        col = column_map.get(field)
        if col and not pd.isna(row.get(col, None)):
            txn[field] = str(row[col]).strip()
        else:
            txn[field] = None

    # Compute amount from units * nav if amount is missing but both are present
    if txn.get("amount") is None and txn.get("units") is not None and txn.get("nav") is not None:
        txn["amount"] = round(txn["units"] * txn["nav"], 2)

    return txn


def _map_broker_type(raw_type: str) -> str:
    """Map broker-specific transaction type labels to our standard types."""
    cleaned = raw_type.strip().upper()

    # Direct match
    if cleaned in VALID_TRANSACTION_TYPES:
        return cleaned

    # Mapped match
    mapped = _CASPARSER_TYPE_MAP.get(cleaned)
    if mapped:
        return mapped

    # Keyword-based fallback
    if "BUY" in cleaned or "PURCHASE" in cleaned:
        return "PURCHASE"
    if "SELL" in cleaned or "REDEEM" in cleaned or "REDEMP" in cleaned:
        return "REDEMPTION"
    if "SIP" in cleaned:
        return "PURCHASE_SIP"
    if "SWITCH" in cleaned and "IN" in cleaned:
        return "SWITCH_IN"
    if "SWITCH" in cleaned and "OUT" in cleaned:
        return "SWITCH_OUT"
    if "DIV" in cleaned and ("REINVEST" in cleaned or "REINV" in cleaned):
        return "DIVIDEND_REINVEST"
    if "DIV" in cleaned or "PAYOUT" in cleaned:
        return "DIVIDEND_PAYOUT"

    logger.warning("Unknown broker transaction type '%s', defaulting to PURCHASE", raw_type)
    return "PURCHASE"


# ─── INTERNAL HELPERS: NORMALIZATION ───


def _normalize_cas_transactions(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize CAS (CAMS/KFintech) parsed data into standard transaction format."""
    normalized: List[Dict[str, Any]] = []
    folios = parsed_data.get("folios", [])

    for folio in folios:
        folio_number = folio.get("folio", "")
        amc_name = folio.get("amc", "")

        for scheme in folio.get("schemes", []):
            scheme_name = scheme.get("scheme", "")
            isin = scheme.get("isin", "")
            amfi_code = str(scheme.get("amfi", "")) if scheme.get("amfi") else ""
            scheme_type = scheme.get("type", "")

            # Map casparser scheme type to our category
            scheme_category = _map_scheme_category(scheme_type)

            for txn in scheme.get("transactions", []):
                # Parse and map the transaction type
                raw_type = str(txn.get("type", "") or "")
                description = str(txn.get("description", "") or "")
                txn_type = _map_cas_transaction_type(raw_type, description)

                # Parse date
                txn_date = _parse_date_flexible(str(txn.get("date", "")))
                if txn_date is None:
                    logger.warning("Skipping CAS transaction with unparseable date: %s", txn.get("date"))
                    continue

                amount = _safe_float(txn.get("amount"))
                units = _safe_float(txn.get("units"))
                nav = _safe_float(txn.get("nav"))
                balance = _safe_float(txn.get("balance"))

                normalized.append({
                    "date": txn_date,
                    "type": txn_type,
                    "amount": amount if amount is not None else 0.0,
                    "units": units if units is not None else 0.0,
                    "nav": nav if nav is not None else 0.0,
                    "balance_units": balance if balance is not None else 0.0,
                    "scheme_name": scheme_name,
                    "isin": isin,
                    "amfi_code": amfi_code,
                    "folio_number": folio_number,
                    "amc_name": amc_name,
                    "scheme_category": scheme_category,
                })

    logger.info("Normalized %d CAS transactions from %d folios", len(normalized), len(folios))
    return normalized


def _normalize_demat_transactions(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize NSDL/CDSL demat data into standard transaction format.

    Demat statements may only have holdings (no transaction history). When
    transactions exist, they typically show credit/debit movements.
    """
    normalized: List[Dict[str, Any]] = []
    transactions = parsed_data.get("transactions", [])

    for txn in transactions:
        txn_date = _parse_date_flexible(str(txn.get("date", "")))
        if txn_date is None:
            continue

        # Determine type from debit/credit columns
        debit = _safe_float(txn.get("debit_units"))
        credit = _safe_float(txn.get("credit_units"))
        units_raw = _safe_float(txn.get("units"))

        if debit and debit > 0:
            txn_type = "REDEMPTION"
            units = -abs(debit)
        elif credit and credit > 0:
            txn_type = "PURCHASE"
            units = abs(credit)
        elif units_raw is not None:
            txn_type = "PURCHASE" if units_raw >= 0 else "REDEMPTION"
            units = units_raw
        else:
            txn_type = txn.get("type", "PURCHASE").upper()
            units = 0.0

        raw_type = str(txn.get("type", ""))
        if raw_type:
            txn_type = _map_broker_type(raw_type)

        normalized.append({
            "date": txn_date,
            "type": txn_type,
            "amount": 0.0,  # demat statements typically don't include amounts
            "units": units,
            "nav": 0.0,
            "balance_units": 0.0,
            "scheme_name": txn.get("scheme_name", ""),
            "isin": txn.get("isin", ""),
            "amfi_code": "",
            "folio_number": "",
            "amc_name": "",
            "scheme_category": "",
        })

    logger.info("Normalized %d demat transactions", len(normalized))
    return normalized


def _normalize_broker_transactions(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize broker CSV/Excel data into standard transaction format."""
    normalized: List[Dict[str, Any]] = []
    transactions = parsed_data.get("transactions", [])

    for txn in transactions:
        txn_date = txn.get("date")

        # If date is still a string, parse it
        if isinstance(txn_date, str):
            txn_date = _parse_date_flexible(txn_date)

        if txn_date is None:
            continue

        normalized.append({
            "date": txn_date,
            "type": txn.get("type", "PURCHASE"),
            "amount": txn.get("amount") or 0.0,
            "units": txn.get("units") or 0.0,
            "nav": txn.get("nav") or 0.0,
            "balance_units": txn.get("balance_units") or 0.0,
            "scheme_name": txn.get("scheme_name", ""),
            "isin": txn.get("isin", ""),
            "amfi_code": "",
            "folio_number": txn.get("folio_number", ""),
            "amc_name": "",
            "scheme_category": "",
        })

    logger.info("Normalized %d broker transactions", len(normalized))
    return normalized


# ─── INTERNAL HELPERS: TYPE MAPPING ───


def _map_cas_transaction_type(raw_type: str, description: str) -> str:
    """Map casparser transaction type + description to our standard type.

    casparser provides a type field and a description field. The description
    often contains more specific info (e.g., "Systematic Investment" in the
    description when type is just "PURCHASE").
    """
    cleaned_type = raw_type.strip().upper()
    cleaned_desc = description.strip().upper()

    # Check casparser type map first
    mapped = _CASPARSER_TYPE_MAP.get(cleaned_type)
    if mapped:
        # Refine PURCHASE to PURCHASE_SIP if description mentions SIP
        if mapped == "PURCHASE" and _is_sip_description(cleaned_desc):
            return "PURCHASE_SIP"
        return mapped

    # Fallback: check description for clues
    if _is_sip_description(cleaned_desc):
        return "PURCHASE_SIP"
    if "REDEMPTION" in cleaned_desc or "REDEEM" in cleaned_desc:
        return "REDEMPTION"
    if "SWITCH" in cleaned_desc:
        if "IN" in cleaned_desc or "TO" in cleaned_desc:
            return "SWITCH_IN"
        return "SWITCH_OUT"
    if "DIVIDEND" in cleaned_desc:
        if "REINVEST" in cleaned_desc:
            return "DIVIDEND_REINVEST"
        return "DIVIDEND_PAYOUT"
    if "PURCHASE" in cleaned_desc or "BUY" in cleaned_desc:
        return "PURCHASE"

    logger.debug("Unmapped CAS type='%s' desc='%s', defaulting to PURCHASE", raw_type, description)
    return "PURCHASE"


def _is_sip_description(description: str) -> bool:
    """Check if a transaction description indicates a SIP (Systematic Investment Plan)."""
    sip_indicators = [
        "SYSTEMATIC INVESTMENT",
        "SIP",
        "SYSTEMATIC",
        "AUTO DEBIT",
        "STANDING INSTRUCTION",
        "SI -",
        "S.I.P",
    ]
    return any(indicator in description for indicator in sip_indicators)


def _map_scheme_category(scheme_type: str) -> str:
    """Map casparser scheme type to a broad category for our system."""
    if not scheme_type:
        return ""

    scheme_upper = scheme_type.upper()

    if "EQUITY" in scheme_upper:
        if "LARGE" in scheme_upper:
            return "Large Cap"
        if "MID" in scheme_upper:
            return "Mid Cap"
        if "SMALL" in scheme_upper:
            return "Small Cap"
        if "MULTI" in scheme_upper or "FLEXI" in scheme_upper:
            return "Multi Cap"
        if "ELSS" in scheme_upper or "TAX" in scheme_upper:
            return "ELSS"
        if "INDEX" in scheme_upper:
            return "Index"
        if "SECTOR" in scheme_upper or "THEMATIC" in scheme_upper:
            return "Sectoral"
        return "Equity"

    if "DEBT" in scheme_upper or "BOND" in scheme_upper or "INCOME" in scheme_upper:
        if "LIQUID" in scheme_upper:
            return "Liquid"
        if "SHORT" in scheme_upper:
            return "Short Duration"
        if "GILT" in scheme_upper:
            return "Gilt"
        if "CORPORATE" in scheme_upper:
            return "Corporate Bond"
        return "Debt"

    if "HYBRID" in scheme_upper or "BALANCED" in scheme_upper:
        return "Hybrid"

    if "SOLUTION" in scheme_upper or "RETIREMENT" in scheme_upper or "CHILD" in scheme_upper:
        return "Solution Oriented"

    return scheme_type


# ─── INTERNAL HELPERS: PDF TYPE DETECTION ───


def _detect_pdf_type(content: bytes) -> str:
    """Detect whether a PDF is from CAMS, KFintech, NSDL, or CDSL by examining content.

    Reads a portion of the raw PDF bytes and looks for identifying strings.
    This is a heuristic — CAS PDFs from CAMS and KFintech contain distinctive
    headers and footers.
    """
    # Examine the first 10KB for identifying strings (covers most PDF headers/metadata)
    sample = content[:10240]

    try:
        # Try decoding as latin-1 (works for raw PDF bytes without failures)
        text = sample.decode("latin-1", errors="replace").upper()
    except Exception:
        text = str(sample).upper()

    # NSDL demat statements
    if "NSDL" in text or "NATIONAL SECURITIES DEPOSITORY" in text:
        logger.info("PDF detected as NSDL demat statement")
        return "NSDL"

    # CDSL demat statements
    if "CDSL" in text or "CENTRAL DEPOSITORY" in text:
        logger.info("PDF detected as CDSL demat statement")
        return "CDSL"

    # CAMS CAS
    if "CAMS" in text or "COMPUTER AGE MANAGEMENT" in text:
        logger.info("PDF detected as CAMS CAS statement")
        return "CAMS"

    # KFintech (formerly Karvy) CAS
    if "KFINTECH" in text or "KARVY" in text or "KFIN" in text:
        logger.info("PDF detected as KFintech CAS statement")
        return "KFINTECH"

    # Generic CAS detection — look for mutual fund CAS indicators
    if "CONSOLIDATED ACCOUNT STATEMENT" in text or "CAS" in text:
        # Default to CAMS since it's the more common CAS provider
        logger.info("PDF detected as CAS statement (provider unknown, defaulting to CAMS)")
        return "CAMS"

    logger.warning("Could not determine PDF type from content, returning UNKNOWN")
    return "UNKNOWN"


# ─── INTERNAL HELPERS: UTILITIES ───


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float, returning None on failure.

    Handles common formats in Indian financial documents: commas as thousands
    separators, parentheses for negative values, currency symbols.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:
        cleaned = str(value).strip()

        if not cleaned or cleaned.lower() in ("nan", "none", "-", "--", "n/a", ""):
            return None

        # Remove currency symbols and whitespace
        cleaned = cleaned.replace("₹", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()

        # Handle parentheses for negative values: (1234.56) -> -1234.56
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date_flexible(date_str: str) -> Optional[datetime]:
    """Parse a date string trying multiple formats common in Indian financial documents.

    Indian documents use DD-MM-YYYY, DD/MM/YYYY, and occasionally YYYY-MM-DD.
    """
    if not date_str or date_str.lower() in ("none", "nan", "nat", ""):
        return None

    date_str = date_str.strip()

    # Common date formats in Indian financial documents
    formats = [
        "%d-%b-%Y",      # 15-Jan-2024
        "%d-%m-%Y",      # 15-01-2024
        "%d/%m/%Y",      # 15/01/2024
        "%Y-%m-%d",      # 2024-01-15 (ISO)
        "%d-%B-%Y",      # 15-January-2024
        "%d %b %Y",      # 15 Jan 2024
        "%d %B %Y",      # 15 January 2024
        "%d/%b/%Y",      # 15/Jan/2024
        "%m/%d/%Y",      # 01/15/2024 (US format — some exports)
        "%Y-%m-%dT%H:%M:%S",  # ISO with time
        "%d-%m-%Y %H:%M:%S",  # Indian with time
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Last resort: try pandas date parser which handles many edge cases
    try:
        parsed = pd.to_datetime(date_str, dayfirst=True)
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    except Exception:
        pass

    logger.debug("Could not parse date: '%s'", date_str)
    return None


def _mask_pan(pan: str) -> str:
    """Mask a PAN number for logging — show only first 2 and last 1 characters.

    Example: ABCDE1234F -> AB*******F
    """
    if not pan or len(pan) < 4:
        return pan or ""
    return pan[:2] + "*" * (len(pan) - 3) + pan[-1]
