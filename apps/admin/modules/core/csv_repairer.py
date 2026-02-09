#!/usr/bin/env python3
"""
🔧 CSV Repair and Recovery Utility
===================================

Repairs failed CSV files by fixing encoding issues, column mismatches, 
and structural problems. Specifically designed to handle the issues 
identified by the enhanced CSV parser.

Issues Addressed:
- UTF-8 codec decode errors (invalid start bytes)
- Column count mismatches between rows
- Structural inconsistencies
- Character encoding problems

Author: IntelliCV AI System
Date: September 22, 2025
"""

import os
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import chardet
import pandas as pd
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RepairResult:
    """Result of CSV repair operation."""
    file_path: str
    original_encoding: str
    detected_encoding: str
    repair_actions: List[str]
    success: bool
    records_recovered: int
    records_lost: int

class CSVRepairer:
    """
    CSV repair utility for fixing encoding and structural issues
    """
    
    def __init__(self, base_path: str = None):
        """Initialize the CSV repairer"""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Output directories
        self.repaired_dir = self.base_path / "csv_repaired_files"
        self.backup_dir = self.base_path / "csv_original_backups"
        self.reports_dir = self.base_path / "csv_repair_reports"
        
        # Create directories
        for directory in [self.repaired_dir, self.backup_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Track repair results
        self.repair_results = []
        
        logger.info(f"🔧 CSV Repairer initialized")
        logger.info(f"📁 Repaired files: {self.repaired_dir}")
    
    def detect_file_encoding(self, file_path: Path) -> Tuple[str, float]:
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result['encoding'], result['confidence']
        except Exception as e:
            logger.warning(f"Could not detect encoding for {file_path.name}: {e}")
            return 'utf-8', 0.0
    
    def repair_encoding_issues(self, file_path: Path) -> RepairResult:
        """Repair encoding issues in CSV file"""
        repair_actions = []
        original_encoding = 'utf-8'  # Assumed original
        
        try:
            # Detect actual encoding
            detected_encoding, confidence = self.detect_file_encoding(file_path)
            logger.info(f"📊 {file_path.name}: Detected {detected_encoding} (confidence: {confidence:.2f})")
            
            if confidence < 0.7:
                # Try common encodings
                encodings_to_try = ['latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
                for encoding in encodings_to_try:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            f.read(1000)  # Test read
                        detected_encoding = encoding
                        confidence = 0.8  # Assume reasonable confidence
                        repair_actions.append(f"Used fallback encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
            
            # Create backup
            backup_path = self.backup_dir / f"{file_path.stem}_backup_{self.timestamp}{file_path.suffix}"
            backup_path.write_bytes(file_path.read_bytes())
            repair_actions.append(f"Created backup: {backup_path.name}")
            
            # Read with detected encoding
            try:
                with open(file_path, 'r', encoding=detected_encoding) as f:
                    content = f.read()
                repair_actions.append(f"Successfully read with {detected_encoding}")
            except UnicodeDecodeError as e:
                # Handle remaining decode errors by replacing problematic characters
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode(detected_encoding, errors='replace')
                repair_actions.append(f"Replaced problematic characters in {detected_encoding}")
            
            # Write as UTF-8
            repaired_path = self.repaired_dir / f"repaired_{file_path.name}"
            with open(repaired_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            
            repair_actions.append(f"Saved as UTF-8: {repaired_path.name}")
            
            # Count records
            records_recovered = content.count('\n')
            
            return RepairResult(
                file_path=str(file_path),
                original_encoding=original_encoding,
                detected_encoding=detected_encoding,
                repair_actions=repair_actions,
                success=True,
                records_recovered=records_recovered,
                records_lost=0
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to repair encoding for {file_path.name}: {e}")
            return RepairResult(
                file_path=str(file_path),
                original_encoding=original_encoding,
                detected_encoding='unknown',
                repair_actions=[f"Error: {str(e)}"],
                success=False,
                records_recovered=0,
                records_lost=0
            )
    
    def repair_column_mismatches(self, file_path: Path) -> RepairResult:
        """Repair column count mismatches in CSV file"""
        repair_actions = []
        records_recovered = 0
        records_lost = 0
        
        try:
            # First, ensure encoding is correct
            detected_encoding, _ = self.detect_file_encoding(file_path)
            
            # Read file and analyze structure
            lines = []
            with open(file_path, 'r', encoding=detected_encoding, errors='replace') as f:
                reader = csv.reader(f)
                lines = list(reader)
            
            if not lines:
                return RepairResult(
                    file_path=str(file_path),
                    original_encoding=detected_encoding,
                    detected_encoding=detected_encoding,
                    repair_actions=["File is empty"],
                    success=False,
                    records_recovered=0,
                    records_lost=0
                )
            
            # Determine expected column count from header
            header = lines[0]
            expected_cols = len(header)
            repair_actions.append(f"Expected columns: {expected_cols}")
            
            # Analyze column counts
            column_counts = {}
            for i, line in enumerate(lines):
                col_count = len(line)
                column_counts[col_count] = column_counts.get(col_count, 0) + 1
            
            # Find most common column count (excluding header)
            if len(column_counts) > 1:
                most_common_count = max(column_counts.items(), key=lambda x: x[1])[0]
                if most_common_count != expected_cols:
                    expected_cols = most_common_count
                    repair_actions.append(f"Adjusted expected columns to most common: {expected_cols}")
            
            # Repair rows
            repaired_lines = [header[:expected_cols]]  # Trim or pad header
            
            for i, line in enumerate(lines[1:], 1):  # Skip header
                if len(line) == expected_cols:
                    # Row is correct
                    repaired_lines.append(line)
                    records_recovered += 1
                elif len(line) > expected_cols:
                    # Row has too many columns - truncate
                    repaired_lines.append(line[:expected_cols])
                    records_recovered += 1
                    repair_actions.append(f"Truncated row {i}: {len(line)} -> {expected_cols} columns")
                elif len(line) < expected_cols:
                    # Row has too few columns - pad with empty strings
                    padded_line = line + [''] * (expected_cols - len(line))
                    repaired_lines.append(padded_line)
                    records_recovered += 1
                    repair_actions.append(f"Padded row {i}: {len(line)} -> {expected_cols} columns")
                else:
                    # Skip problematic rows that can't be fixed
                    records_lost += 1
                    repair_actions.append(f"Skipped problematic row {i}")
            
            # Create backup
            backup_path = self.backup_dir / f"{file_path.stem}_backup_{self.timestamp}{file_path.suffix}"
            backup_path.write_bytes(file_path.read_bytes())
            
            # Write repaired file
            repaired_path = self.repaired_dir / f"repaired_{file_path.name}"
            with open(repaired_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(repaired_lines)
            
            repair_actions.append(f"Saved repaired file: {repaired_path.name}")
            
            return RepairResult(
                file_path=str(file_path),
                original_encoding=detected_encoding,
                detected_encoding='utf-8',
                repair_actions=repair_actions,
                success=True,
                records_recovered=records_recovered,
                records_lost=records_lost
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to repair columns for {file_path.name}: {e}")
            return RepairResult(
                file_path=str(file_path),
                original_encoding='unknown',
                detected_encoding='unknown',
                repair_actions=[f"Error: {str(e)}"],
                success=False,
                records_recovered=0,
                records_lost=0
            )
    
    def repair_csv_file(self, file_path: Path, issues: List[str]) -> RepairResult:
        """Repair a CSV file based on identified issues"""
        logger.info(f"🔧 Repairing {file_path.name}")
        
        # Determine repair strategy based on issues
        has_encoding_issues = any('codec' in issue or 'decode' in issue for issue in issues)
        has_column_issues = any('columns' in issue for issue in issues)
        
        if has_encoding_issues:
            result = self.repair_encoding_issues(file_path)
            # If encoding was fixed, retry with column repair if needed
            if result.success and has_column_issues:
                repaired_file = self.repaired_dir / f"repaired_{file_path.name}"
                if repaired_file.exists():
                    column_result = self.repair_column_mismatches(repaired_file)
                    # Merge results
                    result.repair_actions.extend(column_result.repair_actions)
                    result.records_recovered = column_result.records_recovered
                    result.records_lost = column_result.records_lost
        elif has_column_issues:
            result = self.repair_column_mismatches(file_path)
        else:
            # Generic repair attempt
            result = self.repair_encoding_issues(file_path)
        
        self.repair_results.append(result)
        return result
    
    def repair_failed_files(self, failed_files_report: str) -> Dict[str, Any]:
        """Repair all failed files from the CSV parser report"""
        
        # Load failed files report
        try:
            with open(failed_files_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            logger.error(f"❌ Could not load failed files report: {e}")
            return {'success': False, 'message': 'Could not load report'}
        
        failed_files = report_data.get('failed_files', [])
        if not failed_files:
            logger.info("ℹ️ No failed files to repair")
            return {'success': True, 'message': 'No files to repair'}
        
        logger.info(f"🔧 Attempting to repair {len(failed_files)} files")
        
        repair_summary = {
            'files_attempted': 0,
            'files_repaired': 0,
            'files_failed': 0,
            'total_records_recovered': 0,
            'total_records_lost': 0
        }
        
        for file_info in failed_files:
            file_path = Path(file_info['file_path'])
            issues = file_info.get('errors', [])
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                continue
            
            repair_summary['files_attempted'] += 1
            
            try:
                result = self.repair_csv_file(file_path, issues)
                
                if result.success:
                    repair_summary['files_repaired'] += 1
                    repair_summary['total_records_recovered'] += result.records_recovered
                    repair_summary['total_records_lost'] += result.records_lost
                    logger.info(f"✅ Repaired {file_path.name}: {result.records_recovered} records recovered")
                else:
                    repair_summary['files_failed'] += 1
                    logger.warning(f"⚠️ Could not repair {file_path.name}")
                    
            except Exception as e:
                repair_summary['files_failed'] += 1
                logger.error(f"❌ Error repairing {file_path.name}: {e}")
        
        # Generate repair report
        self._generate_repair_report(repair_summary)
        
        return repair_summary
    
    def _generate_repair_report(self, summary: Dict[str, Any]):
        """Generate comprehensive repair report"""
        report = {
            'repair_session': {
                'timestamp': self.timestamp,
                'summary': summary
            },
            'detailed_results': [
                {
                    'file_path': r.file_path,
                    'success': r.success,
                    'original_encoding': r.original_encoding,
                    'detected_encoding': r.detected_encoding,
                    'records_recovered': r.records_recovered,
                    'records_lost': r.records_lost,
                    'repair_actions': r.repair_actions
                }
                for r in self.repair_results
            ]
        }
        
        # Save repair report
        report_file = self.reports_dir / f"csv_repair_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📋 Repair report saved to: {report_file}")


def main():
    """Main execution function"""
    try:
        # Initialize repairer
        repairer = CSVRepairer()
        
        # Find the latest failed files report
        base_path = Path.cwd()
        error_reports_dir = base_path / "csv_parsing_errors"
        
        if not error_reports_dir.exists():
            print("❌ No CSV parsing error reports found")
            return False
        
        # Find the latest error report
        error_reports = list(error_reports_dir.glob("failed_csv_files_*.json"))
        if not error_reports:
            print("❌ No failed CSV files reports found")
            return False
        
        latest_report = max(error_reports, key=lambda p: p.stat().st_mtime)
        print(f"📋 Using error report: {latest_report.name}")
        
        # Repair failed files
        results = repairer.repair_failed_files(latest_report)
        
        print("\n" + "="*80)
        print("🔧 CSV REPAIR COMPLETED!")
        print("="*80)
        print(f"📁 Files Attempted: {results['files_attempted']}")
        print(f"✅ Files Repaired: {results['files_repaired']}")
        print(f"❌ Files Still Failed: {results['files_failed']}")
        print(f"📊 Records Recovered: {results['total_records_recovered']}")
        print(f"📉 Records Lost: {results['total_records_lost']}")
        
        print(f"\n📁 Output Locations:")
        print(f"   • Repaired Files: {repairer.repaired_dir}")
        print(f"   • Backups: {repairer.backup_dir}")
        print(f"   • Reports: {repairer.reports_dir}")
        print("="*80)
        
        return results['files_repaired'] > 0
        
    except Exception as e:
        print(f"\n❌ CSV repair failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)