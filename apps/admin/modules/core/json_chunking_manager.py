
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

#!/usr/bin/env python3
"""
JSON Chunking Strategy for Large Files
Handles massive JSON files that exceed practical limits by implementing smart chunking
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Iterator
import math

class JSONChunkingManager:
    def __init__(self, base_path: str = "C:\\IntelliCV\\admin_portal_final"):
        self.base_path = Path(base_path)
        self.chunk_size_mb = 50  # 50MB chunks
        self.chunk_size_bytes = self.chunk_size_mb * 1024 * 1024
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🔧 JSON Chunking Manager initialized")
        print(f"📦 Chunk size: {self.chunk_size_mb} MB")

    def chunk_large_json_file(self, file_path: Path) -> List[Path]:
        """Chunk a large JSON file into manageable pieces"""
        print(f"✂️  Chunking file: {file_path.name}")
        
        try:
            # Load the JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = []
            
            if isinstance(data, list):
                chunks = self._chunk_list_data(data, file_path)
            elif isinstance(data, dict):
                chunks = self._chunk_dict_data(data, file_path)
            else:
                print(f"⚠️  Cannot chunk data type: {type(data)}")
                return []
            
            print(f"✅ Created {len(chunks)} chunks for {file_path.name}")
            return chunks
            
        except Exception as e:
            print(f"❌ Error chunking {file_path}: {e}")
            return []

    def _chunk_list_data(self, data: List, original_path: Path) -> List[Path]:
        """Chunk list-based JSON data"""
        total_items = len(data)
        
        # Estimate items per chunk based on size
        sample_size = min(100, total_items)
        sample_json = json.dumps(data[:sample_size], ensure_ascii=False)
        avg_item_size = len(sample_json.encode('utf-8')) / sample_size
        items_per_chunk = max(1, int(self.chunk_size_bytes / avg_item_size))
        
        chunks = []
        chunk_dir = original_path.parent / f"{original_path.stem}_chunks"
        chunk_dir.mkdir(exist_ok=True)
        
        for i in range(0, total_items, items_per_chunk):
            chunk_data = data[i:i + items_per_chunk]
            chunk_num = i // items_per_chunk + 1
            chunk_path = chunk_dir / f"{original_path.stem}_chunk_{chunk_num:03d}.json"
            
            chunk_metadata = {
                'chunk_info': {
                    'original_file': str(original_path),
                    'chunk_number': chunk_num,
                    'total_chunks': math.ceil(total_items / items_per_chunk),
                    'items_in_chunk': len(chunk_data),
                    'start_index': i,
                    'end_index': min(i + items_per_chunk - 1, total_items - 1),
                    'timestamp': self.timestamp
                },
                'data': chunk_data
            }
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_metadata, f, indent=2, ensure_ascii=False)
            
            chunks.append(chunk_path)
            print(f"📦 Chunk {chunk_num}: {len(chunk_data):,} items -> {chunk_path.name}")
        
        # Create chunk manifest
        manifest_path = chunk_dir / f"{original_path.stem}_manifest.json"
        manifest = {
            'original_file': str(original_path),
            'chunking_timestamp': self.timestamp,
            'total_chunks': len(chunks),
            'total_items': total_items,
            'chunk_files': [str(chunk) for chunk in chunks],
            'reassembly_instructions': {
                'method': 'concatenate_data_arrays',
                'preserve_order': True
            }
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Manifest created: {manifest_path.name}")
        return chunks

    def _chunk_dict_data(self, data: Dict, original_path: Path) -> List[Path]:
        """Chunk dictionary-based JSON data"""
        chunks = []
        chunk_dir = original_path.parent / f"{original_path.stem}_chunks"
        chunk_dir.mkdir(exist_ok=True)
        
        # Group keys by estimated size
        key_groups = self._group_dict_keys_by_size(data)
        
        for group_num, key_group in enumerate(key_groups, 1):
            chunk_data = {key: data[key] for key in key_group}
            chunk_path = chunk_dir / f"{original_path.stem}_chunk_{group_num:03d}.json"
            
            chunk_metadata = {
                'chunk_info': {
                    'original_file': str(original_path),
                    'chunk_number': group_num,
                    'total_chunks': len(key_groups),
                    'keys_in_chunk': len(key_group),
                    'keys': list(key_group),
                    'timestamp': self.timestamp
                },
                'data': chunk_data
            }
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_metadata, f, indent=2, ensure_ascii=False)
            
            chunks.append(chunk_path)
            print(f"📦 Chunk {group_num}: {len(key_group)} keys -> {chunk_path.name}")
        
        # Create manifest
        manifest_path = chunk_dir / f"{original_path.stem}_manifest.json"
        manifest = {
            'original_file': str(original_path),
            'chunking_timestamp': self.timestamp,
            'total_chunks': len(chunks),
            'total_keys': len(data),
            'chunk_files': [str(chunk) for chunk in chunks],
            'reassembly_instructions': {
                'method': 'merge_data_dicts',
                'preserve_keys': True
            }
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        return chunks

    def _group_dict_keys_by_size(self, data: Dict) -> List[List[str]]:
        """Group dictionary keys into chunks based on size"""
        groups = []
        current_group = []
        current_size = 0
        
        for key, value in data.items():
            # Estimate size of this key-value pair
            item_json = json.dumps({key: value}, ensure_ascii=False)
            item_size = len(item_json.encode('utf-8'))
            
            if current_size + item_size > self.chunk_size_bytes and current_group:
                groups.append(current_group)
                current_group = [key]
                current_size = item_size
            else:
                current_group.append(key)
                current_size += item_size
        
        if current_group:
            groups.append(current_group)
        
        return groups

    def reassemble_chunks(self, manifest_path: Path) -> Path:
        """Reassemble chunks back into original format"""
        print(f"🔧 Reassembling chunks from: {manifest_path.name}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        reassembled_data = None
        method = manifest['reassembly_instructions']['method']
        
        if method == 'concatenate_data_arrays':
            reassembled_data = []
            for chunk_file in manifest['chunk_files']:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk = json.load(f)
                reassembled_data.extend(chunk['data'])
        
        elif method == 'merge_data_dicts':
            reassembled_data = {}
            for chunk_file in manifest['chunk_files']:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk = json.load(f)
                reassembled_data.update(chunk['data'])
        
        # Save reassembled file
        original_path = Path(manifest['original_file'])
        reassembled_path = original_path.parent / f"{original_path.stem}_reassembled.json"
        
        with open(reassembled_path, 'w', encoding='utf-8') as f:
            json.dump(reassembled_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reassembled: {reassembled_path.name}")
        return reassembled_path

    def process_large_files(self, size_threshold_mb: int = 100):
        """Process all large JSON files in the system"""
        print(f"🚀 Processing JSON files larger than {size_threshold_mb} MB")
        
        large_files = []
        processed_count = 0
        
        # Find large JSON files
        for json_file in self.base_path.rglob("*.json"):
            if any(skip in str(json_file) for skip in ['.git', '.vs', '__pycache__', 'chunks']):
                continue
            
            try:
                file_size_mb = json_file.stat().st_size / (1024 * 1024)
                if file_size_mb > size_threshold_mb:
                    large_files.append((json_file, file_size_mb))
            except Exception as e:
                print(f"⚠️  Error checking {json_file}: {e}")
        
        print(f"📊 Found {len(large_files)} large JSON files")
        
        # Process each large file
        for file_path, size_mb in large_files:
            print(f"\n🔧 Processing: {file_path.name} ({size_mb:.2f} MB)")
            
            # Skip if already chunked
            chunk_dir = file_path.parent / f"{file_path.stem}_chunks"
            if chunk_dir.exists():
                print(f"⏭️  Already chunked: {file_path.name}")
                continue
            
            chunks = self.chunk_large_json_file(file_path)
            if chunks:
                processed_count += 1
                
                # Optionally move original to backup
                backup_dir = file_path.parent / "large_json_backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / f"{file_path.name}.backup"
                
                try:
                    file_path.rename(backup_path)
                    print(f"📁 Backed up original: {backup_path.name}")
                except Exception as e:
                    print(f"⚠️  Could not backup {file_path.name}: {e}")
        
        print(f"\n✅ Processed {processed_count} large JSON files")
        return processed_count


def main():
    """Main execution function"""
    chunker = JSONChunkingManager()
    
    # Process all large files automatically
    processed = chunker.process_large_files(size_threshold_mb=100)
    
    print(f"\n🎯 CHUNKING COMPLETE")
    print(f"📦 {processed} files processed")
    print(f"💡 Large files are now chunked and manageable")
    print(f"🔧 Use manifest files to reassemble when needed")


if __name__ == "__main__":
    main()