#!/usr/bin/env python3
"""
🔄 Enhanced CSV Parser and AI Integrator
=========================================

Comprehensive CSV parsing system that handles all CSV files and integrates them 
with AI sections. Processes email CSVs, creates new CSV outputs, and links data
to appropriate AI intelligence engines.

Features:
- Universal CSV parsing and validation
- Email CSV processing and enhancement
- AI section integration and correlation
- Error tracking and recovery
- Comprehensive reporting

Author: IntelliCV AI System
Date: September 22, 2025
"""

import os
import csv
import json
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import re
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CSVParsingResult:
    """Result of CSV parsing operation."""
    file_path: str
    records_processed: int
    errors: List[str]
    ai_correlations: List[str]
    success: bool
    processing_time: float

@dataclass
class AICorrelation:
    """AI section correlation data."""
    csv_record_id: str
    ai_section: str
    correlation_type: str
    confidence_score: float
    enrichment_data: Dict[str, Any]

class EnhancedCSVParser:
    """
    Enhanced CSV parser with AI integration capabilities
    """
    
    def __init__(self, base_path: str = None):
        """Initialize the enhanced CSV parser"""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Output directories
        self.csv_output_dir = self.base_path / "csv_parsed_output"
        self.ai_integration_dir = self.base_path / "ai_csv_integration"
        self.error_reports_dir = self.base_path / "csv_parsing_errors"
        
        # Create directories
        for directory in [self.csv_output_dir, self.ai_integration_dir, self.error_reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # AI sections mapping
        self.ai_sections = {
            'dashboard_intelligence': {'keywords': ['dashboard', 'metrics', 'kpi'], 'priority': 'high'},
            'user_management_intelligence': {'keywords': ['user', 'profile', 'account'], 'priority': 'critical'},
            'data_parser_intelligence': {'keywords': ['parse', 'extract', 'document'], 'priority': 'critical'},
            'email_intelligence': {'keywords': ['email', 'contact', 'communication'], 'priority': 'high'},
            'market_intelligence': {'keywords': ['company', 'industry', 'market'], 'priority': 'high'},
            'skills_intelligence': {'keywords': ['skill', 'competency', 'expertise'], 'priority': 'high'},
            'analytics_intelligence': {'keywords': ['analytics', 'report', 'analysis'], 'priority': 'high'},
            'compliance_intelligence': {'keywords': ['compliance', 'gdpr', 'regulation'], 'priority': 'medium'}
        }
        
        # Initialize results tracking
        self.parsing_results = []
        self.ai_correlations = []
        self.failed_files = []
        
        logger.info(f"🔄 Enhanced CSV Parser initialized")
        logger.info(f"📁 CSV Output: {self.csv_output_dir}")
        logger.info(f"🧠 AI Integration: {self.ai_integration_dir}")
    
    def discover_csv_files(self, search_paths: List[str] = None) -> List[Path]:
        """Discover all CSV files in the workspace"""
        if search_paths is None:
            search_paths = [
                str(self.base_path),
                str(self.base_path / "working_copy"),
                str(self.base_path / "data"),
                str(self.base_path / "ai_enriched_output"),
                str(self.base_path / "admin_portal"),
                str(self.base_path / "admin_portal_final")
            ]
        
        csv_files = []
        for search_path in search_paths:
            path_obj = Path(search_path)
            if path_obj.exists():
                # Find all CSV files recursively
                csv_files.extend(path_obj.rglob("*.csv"))
        
        logger.info(f"🔍 Found {len(csv_files)} CSV files to process")
        return csv_files
    
    def validate_csv_structure(self, file_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate CSV file structure and return metadata"""
        errors = []
        metadata = {
            'file_size': 0,
            'row_count': 0,
            'column_count': 0,
            'columns': [],
            'encoding': 'utf-8',
            'delimiter': ',',
            'has_header': True
        }
        
        try:
            # Check file exists and get size
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
                return False, errors, metadata
            
            metadata['file_size'] = file_path.stat().st_size
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read(1024)  # Read first 1KB
                    metadata['encoding'] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                errors.append("Could not decode file with any supported encoding")
                return False, errors, metadata
            
            # Detect delimiter
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(content)
                metadata['delimiter'] = dialect.delimiter
            except csv.Error:
                metadata['delimiter'] = ','  # Default
            
            # Read and validate structure
            with open(file_path, 'r', encoding=metadata['encoding']) as f:
                reader = csv.reader(f, delimiter=metadata['delimiter'])
                
                # Check header
                try:
                    first_row = next(reader)
                    metadata['columns'] = first_row
                    metadata['column_count'] = len(first_row)
                    metadata['has_header'] = self._detect_header(first_row)
                except StopIteration:
                    errors.append("File is empty")
                    return False, errors, metadata
                
                # Count rows
                row_count = 1  # Header row
                for row in reader:
                    row_count += 1
                    if len(row) != metadata['column_count']:
                        errors.append(f"Row {row_count} has {len(row)} columns, expected {metadata['column_count']}")
                
                metadata['row_count'] = row_count
            
            return len(errors) == 0, errors, metadata
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors, metadata
    
    def _detect_header(self, first_row: List[str]) -> bool:
        """Detect if first row is a header"""
        # Simple heuristic: if all values are strings and don't look like data
        if not first_row:
            return False
        
        # Check for common header patterns
        header_indicators = ['id', 'name', 'email', 'date', 'type', 'status', 'count']
        numeric_count = 0
        
        for value in first_row:
            if value.lower() in header_indicators:
                return True
            try:
                float(value)
                numeric_count += 1
            except ValueError:
                pass
        
        # If most values are numeric, probably not a header
        return numeric_count < len(first_row) * 0.7
    
    def parse_csv_file(self, file_path: Path) -> CSVParsingResult:
        """Parse a single CSV file and create enhanced version"""
        start_time = datetime.now()
        errors = []
        ai_correlations = []
        records_processed = 0
        
        try:
            logger.info(f"📄 Processing CSV: {file_path.name}")
            
            # Validate structure
            is_valid, validation_errors, metadata = self.validate_csv_structure(file_path)
            if not is_valid:
                errors.extend(validation_errors)
                return CSVParsingResult(
                    file_path=str(file_path),
                    records_processed=0,
                    errors=errors,
                    ai_correlations=[],
                    success=False,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Read CSV data
            df = pd.read_csv(
                file_path, 
                encoding=metadata['encoding'],
                delimiter=metadata['delimiter']
            )
            
            records_processed = len(df)
            
            # Enhance data with AI correlations
            enhanced_df = self._enhance_csv_data(df, file_path)
            
            # Find AI correlations
            ai_correlations = self._find_ai_correlations(enhanced_df, file_path)
            
            # Save enhanced CSV
            output_file = self.csv_output_dir / f"enhanced_{file_path.stem}_{self.timestamp}.csv"
            enhanced_df.to_csv(output_file, index=False, encoding='utf-8')
            
            # Create AI integration files
            self._create_ai_integration_files(enhanced_df, ai_correlations, file_path)
            
            logger.info(f"✅ Successfully processed {records_processed} records from {file_path.name}")
            
            return CSVParsingResult(
                file_path=str(file_path),
                records_processed=records_processed,
                errors=errors,
                ai_correlations=[corr.ai_section for corr in ai_correlations],
                success=True,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return CSVParsingResult(
                file_path=str(file_path),
                records_processed=records_processed,
                errors=errors,
                ai_correlations=[],
                success=False,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _enhance_csv_data(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """Enhance CSV data with additional AI-ready columns"""
        enhanced_df = df.copy()
        
        # Add metadata columns
        enhanced_df['_source_file'] = file_path.name
        enhanced_df['_processing_timestamp'] = datetime.now().isoformat()
        enhanced_df['_record_hash'] = enhanced_df.apply(
            lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest()[:16], 
            axis=1
        )
        
        # Email-specific enhancements
        if 'email' in df.columns:
            enhanced_df['_email_domain'] = enhanced_df['email'].apply(self._extract_domain)
            enhanced_df['_email_valid'] = enhanced_df['email'].apply(self._validate_email)
            enhanced_df['_email_type'] = enhanced_df['email'].apply(self._classify_email_type)
        
        # Add AI readiness score
        enhanced_df['_ai_readiness_score'] = enhanced_df.apply(self._calculate_ai_readiness, axis=1)
        
        return enhanced_df
    
    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        if pd.isna(email) or not isinstance(email, str):
            return ''
        
        match = re.search(r'@([^@\s]+)', email)
        return match.group(1) if match else ''
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        if pd.isna(email) or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _classify_email_type(self, email: str) -> str:
        """Classify email type (business, personal, etc.)"""
        if pd.isna(email) or not isinstance(email, str):
            return 'unknown'
        
        domain = self._extract_domain(email).lower()
        
        # Business domains
        business_indicators = ['.com', '.co.uk', '.org', '.net']
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        
        if domain in personal_domains:
            return 'personal'
        elif any(indicator in domain for indicator in business_indicators):
            return 'business'
        else:
            return 'unknown'
    
    def _calculate_ai_readiness(self, row: pd.Series) -> float:
        """Calculate AI readiness score for a record"""
        score = 0.0
        total_fields = len(row)
        
        # Score based on data completeness
        non_null_fields = row.notna().sum()
        completeness_score = non_null_fields / total_fields if total_fields > 0 else 0
        
        # Score based on data quality
        quality_score = 0.8  # Base quality score
        
        # Email validation bonus
        if 'email' in row.index and row.get('_email_valid', False):
            quality_score += 0.1
        
        # Calculate final score
        score = (completeness_score * 0.6) + (quality_score * 0.4)
        return min(1.0, score)
    
    def _find_ai_correlations(self, df: pd.DataFrame, file_path: Path) -> List[AICorrelation]:
        """Find correlations between CSV data and AI sections"""
        correlations = []
        
        for _, row in df.iterrows():
            record_id = row.get('_record_hash', '')
            row_text = ' '.join([str(val) for val in row.values if pd.notna(val)]).lower()
            
            for ai_section, config in self.ai_sections.items():
                correlation_score = 0.0
                matched_keywords = []
                
                # Check keyword matches
                for keyword in config['keywords']:
                    if keyword in row_text:
                        correlation_score += 1.0
                        matched_keywords.append(keyword)
                
                # Normalize score
                if config['keywords']:
                    correlation_score = correlation_score / len(config['keywords'])
                
                # Apply priority multiplier
                priority_multipliers = {'critical': 1.5, 'high': 1.2, 'medium': 1.0, 'low': 0.8}
                correlation_score *= priority_multipliers.get(config['priority'], 1.0)
                
                # Only keep significant correlations
                if correlation_score > 0.3:
                    correlations.append(AICorrelation(
                        csv_record_id=record_id,
                        ai_section=ai_section,
                        correlation_type='keyword_match',
                        confidence_score=min(1.0, correlation_score),
                        enrichment_data={
                            'matched_keywords': matched_keywords,
                            'source_file': file_path.name,
                            'priority': config['priority']
                        }
                    ))
        
        return correlations
    
    def _create_ai_integration_files(self, df: pd.DataFrame, correlations: List[AICorrelation], file_path: Path):
        """Create AI integration files for each correlated section"""
        
        # Group correlations by AI section
        section_correlations = {}
        for corr in correlations:
            if corr.ai_section not in section_correlations:
                section_correlations[corr.ai_section] = []
            section_correlations[corr.ai_section].append(corr)
        
        # Create integration files for each section
        for ai_section, section_corrs in section_correlations.items():
            integration_data = {
                'source_csv': file_path.name,
                'ai_section': ai_section,
                'correlation_count': len(section_corrs),
                'processing_timestamp': datetime.now().isoformat(),
                'correlations': []
            }
            
            for corr in section_corrs:
                # Get the actual record data
                record_data = df[df['_record_hash'] == corr.csv_record_id].iloc[0].to_dict()
                
                integration_data['correlations'].append({
                    'record_id': corr.csv_record_id,
                    'confidence_score': corr.confidence_score,
                    'correlation_type': corr.correlation_type,
                    'enrichment_data': corr.enrichment_data,
                    'record_data': record_data
                })
            
            # Save integration file
            output_file = self.ai_integration_dir / f"{ai_section}_{file_path.stem}_{self.timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(integration_data, f, indent=2, default=str)
    
    def process_all_csv_files(self) -> Dict[str, Any]:
        """Process all discovered CSV files"""
        start_time = datetime.now()
        
        logger.info("🚀 Starting comprehensive CSV processing...")
        
        # Discover CSV files
        csv_files = self.discover_csv_files()
        
        if not csv_files:
            logger.warning("⚠️ No CSV files found to process")
            return {
                'success': False,
                'message': 'No CSV files found',
                'processing_time': 0
            }
        
        # Process each file
        for csv_file in csv_files:
            try:
                result = self.parse_csv_file(csv_file)
                self.parsing_results.append(result)
                
                if not result.success:
                    self.failed_files.append(csv_file)
                    logger.warning(f"⚠️ Failed to process: {csv_file.name}")
                
            except Exception as e:
                logger.error(f"❌ Critical error processing {csv_file.name}: {str(e)}")
                self.failed_files.append(csv_file)
        
        # Generate comprehensive report
        self._generate_comprehensive_report()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        results_summary = {
            'success': True,
            'files_discovered': len(csv_files),
            'files_processed': len([r for r in self.parsing_results if r.success]),
            'files_failed': len(self.failed_files),
            'total_records_processed': sum(r.records_processed for r in self.parsing_results),
            'ai_correlations_found': len(self.ai_correlations),
            'processing_time': processing_time
        }
        
        logger.info(f"🎉 CSV processing completed!")
        logger.info(f"📊 Files processed: {results_summary['files_processed']}/{results_summary['files_discovered']}")
        logger.info(f"📈 Records processed: {results_summary['total_records_processed']}")
        logger.info(f"🧠 AI correlations: {results_summary['ai_correlations_found']}")
        
        return results_summary
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive processing report"""
        report = {
            'processing_session': {
                'timestamp': self.timestamp,
                'start_time': datetime.now().isoformat(),
                'base_path': str(self.base_path)
            },
            'summary': {
                'files_discovered': len(self.parsing_results),
                'successful_parses': len([r for r in self.parsing_results if r.success]),
                'failed_parses': len(self.failed_files),
                'total_records': sum(r.records_processed for r in self.parsing_results)
            },
            'detailed_results': [
                {
                    'file_path': r.file_path,
                    'success': r.success,
                    'records_processed': r.records_processed,
                    'processing_time': r.processing_time,
                    'ai_correlations': r.ai_correlations,
                    'errors': r.errors
                }
                for r in self.parsing_results
            ],
            'failed_files': [str(f) for f in self.failed_files],
            'ai_section_correlations': self._get_ai_section_summary()
        }
        
        # Save comprehensive report
        report_file = self.csv_output_dir / f"comprehensive_csv_processing_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save failed files report
        if self.failed_files:
            failed_report = {
                'failed_files_count': len(self.failed_files),
                'failed_files': [
                    {
                        'file_path': str(f),
                        'file_size': f.stat().st_size if f.exists() else 0,
                        'errors': next((r.errors for r in self.parsing_results if r.file_path == str(f)), [])
                    }
                    for f in self.failed_files
                ]
            }
            
            failed_report_file = self.error_reports_dir / f"failed_csv_files_{self.timestamp}.json"
            with open(failed_report_file, 'w', encoding='utf-8') as f:
                json.dump(failed_report, f, indent=2, default=str)
        
        logger.info(f"📋 Comprehensive report saved to: {report_file}")
    
    def _get_ai_section_summary(self) -> Dict[str, int]:
        """Get summary of AI section correlations"""
        section_counts = {}
        for result in self.parsing_results:
            for ai_section in result.ai_correlations:
                section_counts[ai_section] = section_counts.get(ai_section, 0) + 1
        return section_counts
    
    def get_failed_files_report(self) -> Dict[str, Any]:
        """Get detailed report of failed files"""
        if not self.failed_files:
            return {'message': 'No failed files to report'}
        
        failed_report = {
            'failed_count': len(self.failed_files),
            'files': []
        }
        
        for failed_file in self.failed_files:
            file_info = {
                'path': str(failed_file),
                'exists': failed_file.exists(),
                'size': failed_file.stat().st_size if failed_file.exists() else 0,
                'errors': []
            }
            
            # Find errors from parsing results
            for result in self.parsing_results:
                if result.file_path == str(failed_file):
                    file_info['errors'] = result.errors
                    break
            
            failed_report['files'].append(file_info)
        
        return failed_report


def main():
    """Main execution function"""
    try:
        # Initialize parser
        parser = EnhancedCSVParser()
        
        # Process all CSV files
        results = parser.process_all_csv_files()
        
        print("\n" + "="*80)
        print("🔄 CSV PARSING AND AI INTEGRATION COMPLETED!")
        print("="*80)
        print(f"📁 Files Discovered: {results['files_discovered']}")
        print(f"✅ Files Processed: {results['files_processed']}")
        print(f"❌ Files Failed: {results['files_failed']}")
        print(f"📊 Total Records: {results['total_records_processed']}")
        print(f"🧠 AI Correlations: {results['ai_correlations_found']}")
        print(f"⏱️  Processing Time: {results['processing_time']:.2f} seconds")
        
        # Report failed files if any
        if results['files_failed'] > 0:
            print("\n⚠️ FAILED FILES REPORT:")
            failed_report = parser.get_failed_files_report()
            for failed_file in failed_report['files']:
                print(f"   ❌ {failed_file['path']}")
                if failed_file['errors']:
                    for error in failed_file['errors'][:3]:  # Show first 3 errors
                        print(f"      • {error}")
        
        print("\n📁 Output Locations:")
        print(f"   • Enhanced CSVs: {parser.csv_output_dir}")
        print(f"   • AI Integrations: {parser.ai_integration_dir}")
        print(f"   • Error Reports: {parser.error_reports_dir}")
        print("="*80)
        
        return results['files_failed'] == 0
        
    except Exception as e:
        print(f"\n❌ CSV processing failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)