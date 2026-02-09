"""
IntelliCV Parsers Integration Layer
==================================

Unified interface to all document parsers for dashboard and admin portal use.
"""

# Import all relevant parser modules here
# (Add more as needed for new formats)

from ...utils.doc_parser import parse_docx, parse_pdf, parse_txt
from ...utils.email_tools.email_parser import parse_email_attachments
from ...utils.parse_table_utils import parse_tables
from ...utils.job_title_parser import parse_job_titles
from ...utils.nlp.parse_resume_nlp import parse_resume_nlp

# Example unified API

def parse_document(file_path, file_type=None):
    """Auto-detect and parse a document by type."""
    if not file_type:
        if file_path.lower().endswith('.pdf'):
            return parse_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return parse_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            return parse_txt(file_path)
        # ... add more types as needed
    else:
        if file_type == 'pdf':
            return parse_pdf(file_path)
        elif file_type == 'docx':
            return parse_docx(file_path)
        elif file_type == 'txt':
            return parse_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type or file_path}")


def parse_email(file_path):
    """Parse email file and extract attachments."""
    return parse_email_attachments(file_path)


def parse_tables_from_doc(file_path):
    """Extract tables from a document."""
    return parse_tables(file_path)


def parse_job_titles_from_text(text):
    """Extract job titles from text."""
    return parse_job_titles(text)


def parse_resume_with_nlp(file_path):
    """Parse resume using NLP pipeline."""
    return parse_resume_nlp(file_path)
