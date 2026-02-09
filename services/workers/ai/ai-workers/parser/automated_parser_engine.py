"""
Automated Parser Engine - Production Ready Data Extraction
===========================================================

Converts raw files (PDF, DOCX, CSV, etc.) to structured JSON
Handles 2000+ files in automated_parser/ directory
Output: JSON files in automated_parser/completed/

Usage:
    python automated_parser_engine.py

    # or

    from automated_parser_engine import AutomatedParserEngine
    parser = AutomatedParserEngine()
    results = parser.run()
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomatedParserEngine:
    """
    Production-ready parser for multiple file formats
    Supports: PDF, DOCX, DOC, CSV, XLSX, MSG, TXT, JSON
    """

    def __init__(self, parser_root='automated_parser', output_root='ai_data_final'):
        """Initialize parser with folder paths"""
        self.parser_root = Path(parser_root)
        self.incoming = self.parser_root / 'incoming'
        self.completed = self.parser_root / 'completed'
        self.output_root = Path(output_root)

        # Create output folders if needed
        self.completed.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)

        self.results = {
            'total_files': 0,
            'processed': 0,
            'skipped': 0,
            'errors': [],
            'file_types': {},
            'created_at': datetime.now().isoformat()
        }

        logger.info(f"Parser initialized: {self.parser_root}")
        logger.info(f"Output folder (legacy): {self.completed}")
        logger.info(f"Output folder (primary): {self.output_root}")

    def discover_source_files(self) -> Dict[str, List[Path]]:
        """
        Discover all parseable files in parser root RECURSIVELY
        Returns: dict mapping file type to list of paths
        """
        extensions = {
            '.pdf': 'PDF',
            '.docx': 'DOCX',
            '.doc': 'DOC',
            '.csv': 'CSV',
            '.xlsx': 'XLSX',
            '.xls': 'XLS',      # NEW: Legacy Excel
            '.msg': 'MSG',
            '.eml': 'EML',      # NEW: Email files
            '.mbox': 'MBOX',    # NEW: Mailbox archives
            '.txt': 'TEXT',
            '.json': 'JSON',
            '.rtf': 'TEXT',
            '.odt': 'ODT',      # NEW: OpenDocument Text
            '.ods': 'ODS',      # NEW: OpenDocument Spreadsheet
            '.xml': 'XML',      # NEW: XML files
            '.yaml': 'YAML',    # NEW: YAML files
            '.yml': 'YAML',     # NEW: YAML files
            '.html': 'HTML',    # NEW: HTML files
            '.htm': 'HTML',     # NEW: HTML files
            '.md': 'MARKDOWN'   # NEW: Markdown files
        }

        source_files = {}
        ignored_folders = {'incoming', 'completed', '__pycache__', '.git', '.venv', 'node_modules'}
        skip_files = {'data_ingestion_tracker.py', 'README.md', '.gitignore', 'desktop.ini', 'Thumbs.db'}

        logger.info("Scanning ALL subdirectories recursively...")

        # Recursively scan all subdirectories using rglob
        for file_path in self.parser_root.rglob('*'):
            # Skip if it's a directory
            if file_path.is_dir():
                continue

            # Skip if in ignored folders
            if any(ignored in file_path.parts for ignored in ignored_folders):
                continue

            # Skip certain files
            if file_path.name in skip_files:
                continue

            # Check extension
            ext = file_path.suffix.lower()
            if ext in extensions:
                file_type = extensions[ext]
                if file_type not in source_files:
                    source_files[file_type] = []
                source_files[file_type].append(file_path)
                self.results['total_files'] += 1

                # Track file type stats
                self.results['file_types'][file_type] = self.results['file_types'].get(file_type, 0) + 1

        logger.info(f"Found {self.results['total_files']} files to process")
        for ft, count in self.results['file_types'].items():
            logger.info(f"  {ft}: {count} files")

        return source_files

    # FILE PARSING METHODS

    def parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF"""
        try:
            # Try pdfplumber first (better accuracy)
            try:
                import pdfplumber
                text = ""
                metadata = {}

                with pdfplumber.open(file_path) as pdf:
                    metadata = pdf.metadata or {}
                    for page in pdf.pages:
                        text += page.extract_text() or ""

                return {
                    'file_name': file_path.name,
                    'file_type': 'PDF',
                    'text': text.strip(),
                    'metadata': metadata,
                    'page_count': len(pdf.pages) if hasattr(pdf, 'pages') else None,
                    'extraction_method': 'pdfplumber'
                }
            except ImportError:
                # Fallback to PyPDF2
                try:
                    from PyPDF2 import PdfReader
                    text = ""

                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        for page in reader.pages:
                            text += page.extract_text() or ""

                    return {
                        'file_name': file_path.name,
                        'file_type': 'PDF',
                        'text': text.strip(),
                        'page_count': len(reader.pages),
                        'extraction_method': 'PyPDF2'
                    }
                except ImportError:
                    logger.warning("PDF parsing libraries not installed. Install: pdfplumber or PyPDF2")
                    return {
                        'file_name': file_path.name,
                        'file_type': 'PDF',
                        'error': 'PDF libraries not installed',
                        'status': 'skipped'
                    }
        except Exception as e:
            logger.error(f"PDF parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'PDF',
                'error': str(e),
                'status': 'error'
            }

    def parse_docx(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from DOCX"""
        try:
            from docx import Document

            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])

            # Extract tables
            tables_data = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                tables_data.append(table_data)

            return {
                'file_name': file_path.name,
                'file_type': 'DOCX',
                'text': text.strip(),
                'tables': tables_data if tables_data else None,
                'paragraph_count': len(doc.paragraphs),
                'extraction_method': 'python-docx'
            }
        except ImportError:
            logger.warning("python-docx not installed. Install: pip install python-docx")
            return {
                'file_name': file_path.name,
                'file_type': 'DOCX',
                'error': 'python-docx not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"DOCX parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'DOCX',
                'error': str(e),
                'status': 'error'
            }

    def parse_doc(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from DOC (try to convert or use fallback)"""
        try:
            # Try to use python-docx if it's actually a DOCX
            return self.parse_docx(file_path)
        except Exception:
            # Fallback: try to read as text
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    # Try to extract readable text
                    text = ''.join(chr(b) for b in content if 32 <= b < 127)

                    return {
                        'file_name': file_path.name,
                        'file_type': 'DOC',
                        'text': text.strip(),
                        'extraction_method': 'binary_fallback',
                        'note': 'Limited text extraction from binary format'
                    }
            except Exception as e:
                logger.error(f"DOC parsing error {file_path.name}: {str(e)}")
                return {
                    'file_name': file_path.name,
                    'file_type': 'DOC',
                    'error': str(e),
                    'status': 'error'
                }

    def parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV data"""
        try:
            import csv

            rows = []
            headers = []

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                for row in reader:
                    rows.append(row)

            return {
                'file_name': file_path.name,
                'file_type': 'CSV',
                'headers': headers,
                'rows': rows,
                'row_count': len(rows),
                'column_count': len(headers),
                'extraction_method': 'csv'
            }
        except Exception as e:
            logger.error(f"CSV parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'CSV',
                'error': str(e),
                'status': 'error'
            }

    def parse_xlsx(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from Excel"""
        try:
            from openpyxl import load_workbook

            wb = load_workbook(file_path)
            sheets_data = {}

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = []

                for row in ws.iter_rows(values_only=True):
                    rows.append(list(row))

                sheets_data[sheet_name] = {
                    'rows': rows,
                    'row_count': ws.max_row,
                    'column_count': ws.max_column
                }

            return {
                'file_name': file_path.name,
                'file_type': 'XLSX',
                'sheets': sheets_data,
                'sheet_count': len(wb.sheetnames),
                'extraction_method': 'openpyxl'
            }
        except ImportError:
            logger.warning("openpyxl not installed. Install: pip install openpyxl")
            return {
                'file_name': file_path.name,
                'file_type': 'XLSX',
                'error': 'openpyxl not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"XLSX parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'XLSX',
                'error': str(e),
                'status': 'error'
            }

    def parse_msg(self, file_path: Path) -> Dict[str, Any]:
        """Extract email data from MSG"""
        try:
            from extract_msg import Message

            msg = Message(file_path)

            return {
                'file_name': file_path.name,
                'file_type': 'MSG',
                'subject': msg.subject,
                'sender': msg.sender,
                'to': msg.to,
                'cc': msg.cc or [],
                'bcc': msg.bcc or [],
                'body': msg.body,
                'date': str(msg.date) if hasattr(msg, 'date') else None,
                'attachments': [att.filename for att in msg.attachments] if hasattr(msg, 'attachments') else [],
                'extraction_method': 'extract_msg'
            }
        except ImportError:
            logger.warning("extract_msg not installed. Install: pip install extract_msg")
            return {
                'file_name': file_path.name,
                'file_type': 'MSG',
                'error': 'extract_msg not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"MSG parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'MSG',
                'error': str(e),
                'status': 'error'
            }

    def parse_text(self, file_path: Path) -> Dict[str, Any]:
        """Read plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

            return {
                'file_name': file_path.name,
                'file_type': 'TEXT',
                'text': text.strip(),
                'character_count': len(text),
                'line_count': len(text.split('\n')),
                'extraction_method': 'text'
            }
        except Exception as e:
            logger.error(f"Text parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'TEXT',
                'error': str(e),
                'status': 'error'
            }

    def parse_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                'file_name': file_path.name,
                'file_type': 'JSON',
                'data': data,
                'extraction_method': 'json'
            }
        except Exception as e:
            logger.error(f"JSON parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'JSON',
                'error': str(e),
                'status': 'error'
            }
    def parse_xls(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from Legacy Excel (.xls)"""
        try:
            import xlrd

            workbook = xlrd.open_workbook(file_path)
            sheets_data = {}

            for sheet_name in workbook.sheet_names():
                sheet = workbook.sheet_by_name(sheet_name)
                rows = []

                for row_idx in range(sheet.nrows):
                    row_data = [sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)]
                    rows.append(row_data)

                sheets_data[sheet_name] = {
                    'rows': rows,
                    'row_count': sheet.nrows,
                    'column_count': sheet.ncols
                }

            return {
                'file_name': file_path.name,
                'file_type': 'XLS',
                'sheets': sheets_data,
                'sheet_count': len(workbook.sheet_names()),
                'extraction_method': 'xlrd'
            }
        except ImportError:
            logger.warning("xlrd not installed. Install: pip install xlrd")
            return {
                'file_name': file_path.name,
                'file_type': 'XLS',
                'error': 'xlrd not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"XLS parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'XLS',
                'error': str(e),
                'status': 'error'
            }

    def parse_odt(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from OpenDocument Text (.odt)"""
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            # ODT files are zip archives containing content.xml
            with zipfile.ZipFile(file_path, 'r') as odt_zip:
                # Read content.xml
                content_xml = odt_zip.read('content.xml')

                # Parse XML and extract text
                root = ET.fromstring(content_xml)

                # ODT uses namespaces
                namespaces = {
                    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
                    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
                }

                # Extract all text elements
                text_elements = []
                for elem in root.iter():
                    if elem.text:
                        text_elements.append(elem.text.strip())
                    if elem.tail:
                        text_elements.append(elem.tail.strip())

                text = '\n'.join([t for t in text_elements if t])

                return {
                    'file_name': file_path.name,
                    'file_type': 'ODT',
                    'text': text.strip(),
                    'extraction_method': 'zipfile_xml',
                    'note': 'OpenDocument format parsed as XML from ZIP'
                }
        except Exception as e:
            logger.error(f"ODT parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'ODT',
                'error': str(e),
                'status': 'error'
            }

    def parse_ods(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from OpenDocument Spreadsheet (.ods)"""
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(file_path, 'r') as ods_zip:
                content_xml = ods_zip.read('content.xml')
                root = ET.fromstring(content_xml)

                # Extract table data
                tables_data = {}
                for table in root.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table'):
                    table_name = table.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name', 'Sheet')
                    rows = []

                    for row in table.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-row'):
                        row_data = []
                        for cell in row.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell'):
                            cell_text = ''.join(cell.itertext()).strip()
                            row_data.append(cell_text)
                        if row_data:
                            rows.append(row_data)

                    tables_data[table_name] = {
                        'rows': rows,
                        'row_count': len(rows)
                    }

                return {
                    'file_name': file_path.name,
                    'file_type': 'ODS',
                    'sheets': tables_data,
                    'sheet_count': len(tables_data),
                    'extraction_method': 'zipfile_xml'
                }
        except Exception as e:
            logger.error(f"ODS parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'ODS',
                'error': str(e),
                'status': 'error'
            }

    def parse_eml(self, file_path: Path) -> Dict[str, Any]:
        """Extract email data from EML files"""
        try:
            import email
            from email import policy

            with open(file_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        body += part.get_content()
            else:
                body = msg.get_content()

            # Extract attachments
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        attachments.append(part.get_filename())

            return {
                'file_name': file_path.name,
                'file_type': 'EML',
                'subject': msg.get('Subject', ''),
                'sender': msg.get('From', ''),
                'to': msg.get('To', ''),
                'cc': msg.get('Cc', ''),
                'date': msg.get('Date', ''),
                'body': body.strip() if body else '',
                'attachments': attachments,
                'extraction_method': 'email.parser'
            }
        except Exception as e:
            logger.error(f"EML parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'EML',
                'error': str(e),
                'status': 'error'
            }

    def parse_mbox(self, file_path: Path) -> Dict[str, Any]:
        """Extract emails from MBOX mailbox archive"""
        try:
            import mailbox

            mbox = mailbox.mbox(file_path)
            messages = []

            for message in mbox:
                messages.append({
                    'subject': message.get('Subject', ''),
                    'sender': message.get('From', ''),
                    'to': message.get('To', ''),
                    'date': message.get('Date', ''),
                    'body': message.get_payload()[:500] if message.get_payload() else ''  # Limit body length
                })

            return {
                'file_name': file_path.name,
                'file_type': 'MBOX',
                'message_count': len(messages),
                'messages': messages[:100],  # Limit to first 100 messages
                'extraction_method': 'mailbox'
            }
        except Exception as e:
            logger.error(f"MBOX parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'MBOX',
                'error': str(e),
                'status': 'error'
            }

    def parse_xml(self, file_path: Path) -> Dict[str, Any]:
        """Parse XML files"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract text from all elements
            text_elements = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_elements.append(elem.text.strip())

            # Also capture XML as string for structure
            xml_string = ET.tostring(root, encoding='unicode')[:5000]  # Limit length

            return {
                'file_name': file_path.name,
                'file_type': 'XML',
                'text': '\n'.join(text_elements),
                'root_tag': root.tag,
                'xml_preview': xml_string,
                'extraction_method': 'xml.etree'
            }
        except Exception as e:
            logger.error(f"XML parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'XML',
                'error': str(e),
                'status': 'error'
            }

    def parse_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Parse YAML files"""
        try:
            import yaml

            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            return {
                'file_name': file_path.name,
                'file_type': 'YAML',
                'data': data,
                'extraction_method': 'pyyaml'
            }
        except ImportError:
            logger.warning("PyYAML not installed. Install: pip install PyYAML")
            return {
                'file_name': file_path.name,
                'file_type': 'YAML',
                'error': 'PyYAML not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"YAML parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'YAML',
                'error': str(e),
                'status': 'error'
            }

    def parse_html(self, file_path: Path) -> Dict[str, Any]:
        """Parse HTML files and extract text"""
        try:
            from bs4 import BeautifulSoup

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Extract metadata
            title = soup.title.string if soup.title else ''
            meta_description = ''
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '')

            return {
                'file_name': file_path.name,
                'file_type': 'HTML',
                'text': text,
                'title': title,
                'meta_description': meta_description,
                'extraction_method': 'beautifulsoup4'
            }
        except ImportError:
            logger.warning("beautifulsoup4 not installed. Install: pip install beautifulsoup4 lxml")
            return {
                'file_name': file_path.name,
                'file_type': 'HTML',
                'error': 'beautifulsoup4 not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"HTML parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'HTML',
                'error': str(e),
                'status': 'error'
            }

    def parse_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Parse Markdown files and convert to text"""
        try:
            import markdown
            from bs4 import BeautifulSoup

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                md_content = f.read()

            # Convert markdown to HTML
            html = markdown.markdown(md_content)

            # Extract plain text from HTML
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            return {
                'file_name': file_path.name,
                'file_type': 'MARKDOWN',
                'text': text,
                'raw_markdown': md_content[:5000],  # Keep first 5000 chars of original
                'extraction_method': 'markdown+beautifulsoup4'
            }
        except ImportError:
            logger.warning("markdown not installed. Install: pip install markdown beautifulsoup4")
            return {
                'file_name': file_path.name,
                'file_type': 'MARKDOWN',
                'error': 'markdown not installed',
                'status': 'skipped'
            }
        except Exception as e:
            logger.error(f"Markdown parsing error {file_path.name}: {str(e)}")
            return {
                'file_name': file_path.name,
                'file_type': 'MARKDOWN',
                'error': str(e),
                'status': 'error'
            }
    # HELPER METHODS

    def compute_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file for deduplication"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def save_as_json(self, file_path: Path, extracted_data: Dict[str, Any]) -> Path:
        """
        Save extracted data as JSON to ai_data_final/
        Filename: {original_name}_{timestamp}.json
        """
        timestamp = int(datetime.now().timestamp() * 1000)
        output_name = f"{file_path.stem}_{timestamp}.json"
        output_file = self.output_root / output_name

        json_data = {
            'source_file': file_path.name,
            'source_path': str(file_path.relative_to(self.parser_root)),
            'file_type': extracted_data.get('file_type'),
            'file_hash': self.compute_hash(file_path),
            'extracted_data': extracted_data,
            'processed_at': datetime.now().isoformat()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return output_file

    # MAIN EXECUTION

    def run(self, max_files: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute complete parsing pipeline

        Args:
            max_files: Limit number of files to process (for testing)
        """
        logger.info("=" * 60)
        logger.info("PARSER ENGINE STARTING")
        logger.info("=" * 60)

        # Step 1: Discover files
        source_files = self.discover_source_files()

        if self.results['total_files'] == 0:
            logger.warning("No parseable files found!")
            return self.results

        # Step 2: Process each file
        file_count = 0
        for file_type, files in source_files.items():
            parser_method_name = f"parse_{file_type.lower()}"
            parser_method = getattr(self, parser_method_name, None)

            if not parser_method:
                logger.warning(f"No parser for {file_type}")
                self.results['skipped'] += len(files)
                continue

            for file_path in files:
                file_count += 1

                if max_files and file_count > max_files:
                    logger.info(f"Reached max_files limit: {max_files}")
                    break

                try:
                    logger.info(f"[{file_count}/{self.results['total_files']}] Processing: {file_path.name}")

                    # Parse file
                    extracted = parser_method(file_path)

                    # Check for errors
                    if extracted.get('status') == 'skipped':
                        logger.warning(f"  SKIPPED: {extracted.get('error', 'Unknown reason')}")
                        self.results['skipped'] += 1
                        continue

                    if extracted.get('status') == 'error':
                        logger.error(f"  ERROR: {extracted.get('error')}")
                        self.results['errors'].append({
                            'file': file_path.name,
                            'error': extracted.get('error')
                        })
                        continue

                    # Save as JSON
                    output_file = self.save_as_json(file_path, extracted)
                    self.results['processed'] += 1
                    logger.info(f"  âœ“ Saved to {output_file.name}")

                except Exception as e:
                    logger.error(f"  FATAL: {str(e)}")
                    self.results['errors'].append({
                        'file': file_path.name,
                        'error': str(e)
                    })

        # Step 3: Generate report
        self.generate_report()

        return self.results

    def generate_report(self) -> Path:
        """Create parsing summary report"""
        success_count = self.results['processed']
        total = self.results['total_files']
        success_rate = (success_count / max(total, 1)) * 100

        report = {
            'summary': {
                'total_files': total,
                'successfully_parsed': success_count,
                'skipped': self.results['skipped'],
                'failed': len(self.results['errors']),
                'success_rate': f"{success_rate:.1f}%"
            },
            'file_types': self.results['file_types'],
            'errors': self.results['errors'][:100],  # Limit to first 100 errors
            'timestamp': self.results['created_at']
        }

        report_file = self.output_root / 'parsing_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Print summary
        logger.info("=" * 60)
        logger.info("PARSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total files: {total}")
        logger.info(f"Successfully parsed: {success_count}")
        logger.info(f"Skipped: {self.results['skipped']}")
        logger.info(f"Failed: {len(self.results['errors'])}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Report saved: {report_file}")
        logger.info("=" * 60)

        return report_file


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Automated Parser Engine')
    parser.add_argument('--max-files', type=int, help='Limit files to process (for testing)')
    parser.add_argument('--root', default='automated_parser', help='Parser root directory')

    args = parser.parse_args()

    # Run parser
    engine = AutomatedParserEngine(args.root)
    results = engine.run(max_files=args.max_files)

    # Exit with appropriate code
    exit_code = 0 if len(results['errors']) == 0 else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

