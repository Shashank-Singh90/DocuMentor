import pandas as pd
import io
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentProcessor:
    """Process uploaded documents (Markdown, CSV, TXT) for DocuMentor"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def process_uploaded_file(self, file_content: bytes, filename: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Process uploaded file and return chunks ready for vector store
        
        Args:
            file_content: Raw file bytes
            filename: Name of the uploaded file
            file_type: Type of file (markdown, csv, txt)
            
        Returns:
            List of document chunks with metadata
        """
        try:
            logger.info(f"📄 Processing uploaded file: {filename} (type: {file_type})")
            
            if file_type.lower() in ['md', 'markdown']:
                return self._process_markdown(file_content, filename)
            elif file_type.lower() == 'csv':
                return self._process_csv(file_content, filename)
            elif file_type.lower() in ['txt', 'text']:
                return self._process_text(file_content, filename)
            else:
                logger.warning(f"⚠️ Unsupported file type: {file_type}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error processing file {filename}: {e}")
            return []
    
    def _process_markdown(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Process Markdown files"""
        try:
            # Decode content
            content = file_content.decode('utf-8')
            
            # Parse markdown structure
            sections = self._parse_markdown_sections(content)
            
            chunks = []
            for i, section in enumerate(sections):
                # Create chunks for each section
                section_chunks = self._chunk_text(section['content'])
                
                for j, chunk_text in enumerate(section_chunks):
                    if len(chunk_text.strip()) > 50:  # Skip very short chunks
                        chunks.append({
                            'content': chunk_text.strip(),
                            'metadata': {
                                'title': section['title'] or f"{filename} - Section {i+1}",
                                'source': 'uploaded_markdown',
                                'filename': filename,
                                'doc_type': 'user_upload',
                                'section': section['title'],
                                'chunk_index': j,
                                'file_type': 'markdown'
                            }
                        })
            
            logger.info(f"✅ Created {len(chunks)} chunks from markdown: {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing markdown {filename}: {e}")
            return []
    
    def _process_csv(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Process CSV files"""
        try:
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content))
            
            logger.info(f"📊 CSV has {len(df)} rows and {len(df.columns)} columns")
            
            chunks = []
            
            # Method 1: Create overview chunk
            overview = self._create_csv_overview(df, filename)
            chunks.append({
                'content': overview,
                'metadata': {
                    'title': f"{filename} - Data Overview",
                    'source': 'uploaded_csv',
                    'filename': filename,
                    'doc_type': 'user_upload',
                    'section': 'overview',
                    'chunk_index': 0,
                    'file_type': 'csv'
                }
            })
            
            # Method 2: Create chunks from column descriptions
            for i, column in enumerate(df.columns):
                column_info = self._analyze_column(df, column)
                if column_info:
                    chunks.append({
                        'content': column_info,
                        'metadata': {
                            'title': f"{filename} - Column: {column}",
                            'source': 'uploaded_csv',
                            'filename': filename,
                            'doc_type': 'user_upload',
                            'section': f'column_{column}',
                            'chunk_index': i + 1,
                            'file_type': 'csv'
                        }
                    })
            
            # Method 3: Create chunks from row samples (if reasonable size)
            if len(df) <= 1000:  # Only for smaller datasets
                sample_chunks = self._create_row_samples(df, filename)
                chunks.extend(sample_chunks)
            
            logger.info(f"✅ Created {len(chunks)} chunks from CSV: {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing CSV {filename}: {e}")
            return []
    
    def _process_text(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Process plain text files"""
        try:
            # Decode content
            content = file_content.decode('utf-8')
            
            # Clean content
            content = self._clean_text(content)
            
            # Create chunks
            text_chunks = self._chunk_text(content)
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                if len(chunk_text.strip()) > 50:
                    chunks.append({
                        'content': chunk_text.strip(),
                        'metadata': {
                            'title': f"{filename} - Part {i+1}",
                            'source': 'uploaded_text',
                            'filename': filename,
                            'doc_type': 'user_upload',
                            'section': f'part_{i+1}',
                            'chunk_index': i,
                            'file_type': 'text'
                        }
                    })
            
            logger.info(f"✅ Created {len(chunks)} chunks from text: {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing text {filename}: {e}")
            return []
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, str]]:
        """Parse markdown into sections based on headers"""
        sections = []
        lines = content.split('\n')
        
        current_section = {'title': None, 'content': ''}
        
        for line in lines:
            # Check if it's a header
            if line.strip().startswith('#'):
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                header_level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()
                current_section = {'title': title, 'content': line + '\n'}
            else:
                current_section['content'] += line + '\n'
        
        # Add the last section
        if current_section['content'].strip():
            sections.append(current_section)
        
        # If no headers found, treat entire content as one section
        if not sections:
            sections.append({'title': 'Main Content', 'content': content})
        
        return sections
    
    def _create_csv_overview(self, df: pd.DataFrame, filename: str) -> str:
        """Create an overview description of the CSV data"""
        overview = f"Dataset: {filename}\n\n"
        overview += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
        
        overview += "Columns:\n"
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            overview += f"- {col}: {dtype} ({non_null} non-null values)\n"
        
        overview += "\nData Summary:\n"
        try:
            # Get basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                overview += "Numeric columns statistics:\n"
                stats = df[numeric_cols].describe()
                overview += stats.to_string() + "\n\n"
            
            # Get value counts for categorical columns (top 5)
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols[:3]:  # Limit to first 3 categorical columns
                overview += f"\nTop values in {col}:\n"
                top_values = df[col].value_counts().head()
                overview += top_values.to_string() + "\n"
                
        except Exception as e:
            overview += f"Could not generate detailed statistics: {e}\n"
        
        return overview
    
    def _analyze_column(self, df: pd.DataFrame, column: str) -> str:
        """Analyze a specific column and create description"""
        try:
            col_data = df[column]
            analysis = f"Column Analysis: {column}\n\n"
            
            analysis += f"Data Type: {col_data.dtype}\n"
            analysis += f"Non-null Count: {col_data.count()} / {len(col_data)}\n"
            analysis += f"Null Values: {col_data.isnull().sum()}\n\n"
            
            if col_data.dtype in ['int64', 'float64']:
                # Numeric column
                analysis += f"Statistics:\n"
                analysis += f"Min: {col_data.min()}\n"
                analysis += f"Max: {col_data.max()}\n"
                analysis += f"Mean: {col_data.mean():.2f}\n"
                analysis += f"Median: {col_data.median()}\n"
            else:
                # Categorical column
                unique_count = col_data.nunique()
                analysis += f"Unique Values: {unique_count}\n"
                
                if unique_count <= 20:  # Show all unique values if not too many
                    analysis += f"Unique Values: {list(col_data.unique())}\n"
                else:
                    analysis += f"Sample Values: {list(col_data.unique()[:10])}\n"
                
                # Top values
                analysis += f"\nTop 5 Values:\n"
                analysis += col_data.value_counts().head().to_string()
            
            return analysis
            
        except Exception as e:
            return f"Could not analyze column {column}: {e}"
    
    def _create_row_samples(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        """Create sample chunks from CSV rows"""
        chunks = []
        
        # Sample different parts of the dataset
        samples = [
            ("First 10 rows", df.head(10)),
            ("Last 10 rows", df.tail(10)),
        ]
        
        # Add random sample if dataset is large enough
        if len(df) > 50:
            samples.append(("Random 10 rows", df.sample(min(10, len(df)))))
        
        for i, (sample_name, sample_df) in enumerate(samples):
            sample_text = f"{sample_name} from {filename}:\n\n"
            sample_text += sample_df.to_string(index=False)
            
            chunks.append({
                'content': sample_text,
                'metadata': {
                    'title': f"{filename} - {sample_name}",
                    'source': 'uploaded_csv',
                    'filename': filename,
                    'doc_type': 'user_upload',
                    'section': f'sample_{i}',
                    'chunk_index': 1000 + i,  # High index to separate from other chunks
                    'file_type': 'csv'
                }
            })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end in the last 100 chars
                last_part = text[max(0, end-100):end]
                sentence_end = last_part.rfind('. ')
                if sentence_end > 0:
                    end = end - 100 + sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks

# Test function
def test_processor():
    """Test the document processor"""
    processor = DocumentProcessor()
    
    # Test markdown content
    markdown_content = """
# My Documentation

This is a test document.

## Section 1

Content for section 1 with some important information.

## Section 2

More content here with examples and code.
    """.encode('utf-8')
    
    chunks = processor.process_uploaded_file(markdown_content, "test.md", "markdown")
    
    logger.info(f"Generated {len(chunks)} chunks from test markdown")
    for chunk in chunks:
        logger.info(f"Chunk: {chunk['metadata']['title']}")

if __name__ == "__main__":
    test_processor()