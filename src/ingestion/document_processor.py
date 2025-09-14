#!/usr/bin/env python3
"""
Document Processor for DocuMentor
Handles processing of uploaded documents (MD, TXT, CSV) into chunks
"""
import re
import csv
import io
from typing import List, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentProcessor:
    """
    Process uploaded documents into chunks suitable for vector storage
    """
    
    def __init__(self):
        self.chunk_size = 1000  # Target chunk size in characters
        # Magic number - tested with our current docs
        self.chunk_overlap = 100  # Overlap between chunks
        
    def process_uploaded_file(self, file_content: bytes, filename: str, file_extension: str) -> List[Dict[str, Any]]:
        """
        Process uploaded file into chunks
        
        Args:
            file_content: Raw file content as bytes
            filename: Name of the uploaded file
            file_extension: File extension (md, txt, csv)
            
        Returns:
            List of chunks with content and metadata
        """
        logger.info(f"📄 Processing uploaded file: {filename} ({file_extension})")
        
        try:
            # Decode content to text
            if isinstance(file_content, bytes):
                text_content = file_content.decode('utf-8', errors='ignore')
            else:
                text_content = str(file_content)
            
            # Process based on file type
            if file_extension.lower() in ['md', 'markdown']:
                chunks = self._process_markdown(text_content, filename)
            elif file_extension.lower() == 'csv':
                chunks = self._process_csv(text_content, filename)
            elif file_extension.lower() in ['txt', 'text']:
                chunks = self._process_text(text_content, filename)
            else:
                # Fallback to text processing
                chunks = self._process_text(text_content, filename)
            
            logger.info(f"✅ Processed {filename}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
            raise Exception(f"Failed to process {filename}: {str(e)}")
    
    def _process_markdown(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Process Markdown files by sections and headers"""
        chunks = []
        
        # Split by headers (# ## ###)
        sections = re.split(r'\n(?=#{1,6}\s)', content)
        
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
                
            # Extract header and content
            lines = section.split('\n')
            header = lines[0] if lines[0].startswith('#') else f"Section {i+1}"
            section_content = '\n'.join(lines[1:]) if len(lines) > 1 else lines[0]
            
            # Create chunks from this section
            section_chunks = self._create_chunks_from_text(
                section_content, 
                filename, 
                title=header.strip('#').strip(),
                section_type="markdown_section"
            )
            
            chunks.extend(section_chunks)
        
        # If no headers found, process as plain text
        if not chunks:
            chunks = self._create_chunks_from_text(content, filename, title="Document Content")
        
        return chunks
    
    def _process_csv(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Process CSV files by creating overview and column analysis"""
        chunks = []
        
        try:
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            if not rows:
                return chunks
            
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            # Create overview chunk
            overview_content = f"""CSV File: {filename}
            
## Overview
- Total rows: {len(data_rows)}
- Total columns: {len(headers)}
- Headers: {', '.join(headers)}

## Data Structure
This CSV contains {len(data_rows)} rows of data with the following columns:
{chr(10).join([f"- {header}" for header in headers])}
"""
            
            chunks.append({
                'content': overview_content,
                'metadata': {
                    'source': 'Upload',
                    'title': f"{filename} - Overview",
                    'doc_type': 'csv_overview',
                    'filename': filename,
                    'chunk_type': 'overview',
                    'rows_count': len(data_rows),
                    'columns_count': len(headers),
                    'uploaded_at': datetime.now().isoformat()
                }
            })
            
            # Create column analysis chunks
            for col_idx, header in enumerate(headers):
                if len(data_rows) > 0:
                    # Sample values from this column
                    column_values = [row[col_idx] if col_idx < len(row) else '' for row in data_rows]
                    non_empty_values = [v for v in column_values if v.strip()]
                    
                    # Create sample
                    sample_values = non_empty_values[:5] if len(non_empty_values) >= 5 else non_empty_values
                    
                    column_content = f"""Column Analysis: {header}

## Column: {header}
- Position: Column {col_idx + 1}
- Non-empty values: {len(non_empty_values)} out of {len(data_rows)}
- Sample values: {', '.join(sample_values)}

## Data Quality
- Fill rate: {len(non_empty_values)/len(data_rows)*100:.1f}%
"""
                    
                    chunks.append({
                        'content': column_content,
                        'metadata': {
                            'source': 'Upload',
                            'title': f"{filename} - Column: {header}",
                            'doc_type': 'csv_column',
                            'filename': filename,
                            'chunk_type': 'column_analysis',
                            'column_name': header,
                            'column_index': col_idx,
                            'uploaded_at': datetime.now().isoformat()
                        }
                    })
            
            # Create data sample chunk if we have data
            if len(data_rows) > 0:
                sample_rows = data_rows[:3]  # First 3 rows as sample
                sample_content = f"""Data Sample from {filename}

## Sample Data (First 3 rows)
Headers: {', '.join(headers)}

"""
                for i, row in enumerate(sample_rows):
                    sample_content += f"Row {i+1}: {', '.join(row)}\n"
                
                chunks.append({
                    'content': sample_content,
                    'metadata': {
                        'source': 'Upload',
                        'title': f"{filename} - Data Sample",
                        'doc_type': 'csv_sample',
                        'filename': filename,
                        'chunk_type': 'data_sample',
                        'uploaded_at': datetime.now().isoformat()
                    }
                })
        
        except Exception as e:
            logger.error(f"Error processing CSV {filename}: {e}")
            # Fallback to text processing
            return self._process_text(content, filename)
        
        return chunks
    
    def _process_text(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Process plain text files"""
        return self._create_chunks_from_text(content, filename, title="Text Document")
    
    def _create_chunks_from_text(self, text: str, filename: str, title: str = None, section_type: str = "text") -> List[Dict[str, Any]]:
        """Create chunks from text content using intelligent splitting"""
        chunks = []
        
        if not text.strip():
            return chunks
        
        # Split text into sentences for better chunking
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_content = current_chunk.strip()
                if chunk_content:
                    chunks.append(self._create_chunk_dict(
                        chunk_content, 
                        filename, 
                        title or "Document Chunk", 
                        chunk_index,
                        section_type
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                if len(current_chunk) > self.chunk_overlap:
                    # Take last part of current chunk as overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    # Find word boundary for clean overlap
                    word_boundary = overlap_text.find(' ')
                    if word_boundary > 0:
                        current_chunk = overlap_text[word_boundary:].strip() + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk_dict(
                current_chunk.strip(), 
                filename, 
                title or "Document Chunk", 
                chunk_index,
                section_type
            ))
        
        return chunks
    
    def _create_chunk_dict(self, content: str, filename: str, title: str, index: int, section_type: str = "text") -> Dict[str, Any]:
        """Create a standardized chunk dictionary"""
        
        # Create a unique ID for this chunk
        chunk_id = hashlib.md5(f"{filename}_{index}_{content[:50]}".encode()).hexdigest()[:8]
        
        return {
            'content': content,
            'metadata': {
                'source': 'Upload',
                'title': f"{title} (Part {index + 1})" if index > 0 else title,
                'doc_type': 'uploaded_document',
                'filename': filename,
                'chunk_type': section_type,
                'chunk_index': index,
                'chunk_id': chunk_id,
                'content_length': len(content),
                'uploaded_at': datetime.now().isoformat()
            }
        }

# Test function
def test_document_processor():
    """Test the document processor with sample content"""
    processor = DocumentProcessor()
    
    # Test markdown
    md_content = """# Introduction
This is a test document.

## Features
- Feature 1: Something important
- Feature 2: Another feature

## Usage
Here's how to use this:
1. Step one
2. Step two
"""
    
    chunks = processor.process_uploaded_file(md_content.encode(), "test.md", "md")
    print(f"Markdown test: {len(chunks)} chunks created")
    
    # Test CSV
    csv_content = """Name,Age,City
John,25,New York
Jane,30,Los Angeles
Bob,35,Chicago"""
    
    chunks = processor.process_uploaded_file(csv_content.encode(), "test.csv", "csv")
    print(f"CSV test: {len(chunks)} chunks created")

if __name__ == "__main__":
    test_document_processor()
