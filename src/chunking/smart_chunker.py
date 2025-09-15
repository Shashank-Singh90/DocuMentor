import re
from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SmartDocumentChunker:
    """
    Intelligent document chunking for better RAG performance
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
    async def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict]:
        """
        Chunk a document intelligently
        
        Args:
            content: The document content to chunk
            metadata: Metadata for the document
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        try:
            # Clean the content
            cleaned_content = self._clean_content(content)
            
            if len(cleaned_content) < self.min_chunk_size:
                logger.warning(f"Document too short: {len(cleaned_content)} chars")
                return []
            
            # Split into chunks
            chunks = self._split_text(cleaned_content)
            
            # Create chunk objects
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) >= self.min_chunk_size:
                    chunk_metadata = metadata.copy()
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['total_chunks'] = len(chunks)
                    
                    chunk_objects.append({
                        'content': chunk_text.strip(),
                        'metadata': chunk_metadata
                    })
            
            logger.debug(f"Created {len(chunk_objects)} chunks from document: {metadata.get('title', 'Unknown')}")
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Error chunking document {metadata.get('title', 'Unknown')}: {e}")
            return []
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Remove very short lines (likely navigation or footer elements)
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Keep meaningful lines
            if (len(line) > 10 or 
                line.startswith('#') or  # Headers
                line.endswith(':') or   # Definitions
                any(keyword in line.lower() for keyword in ['example', 'note', 'important', 'warning'])):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with smart boundaries"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + paragraph
                else:
                    # Single paragraph is too long, split by sentences
                    if len(paragraph) > self.chunk_size:
                        sentence_chunks = self._split_by_sentences(paragraph)
                        chunks.extend(sentence_chunks[:-1])
                        current_chunk = sentence_chunks[-1] if sentence_chunks else ""
                    else:
                        current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split long text by sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + sentence
                else:
                    # Single sentence is too long, just add it
                    chunks.append(sentence)
            else:
                if current_chunk:
                    current_chunk += ' ' + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text + '\n\n'
        
        # Try to find a good breaking point for overlap
        overlap_text = text[-self.chunk_overlap:]
        
        # Find the start of a sentence in the overlap
        sentence_start = re.search(r'[.!?]\s+', overlap_text)
        if sentence_start:
            overlap_text = overlap_text[sentence_start.end():]
        
        return overlap_text + '\n\n' if overlap_text else ''

# Test function
def test_chunker():
    """Test the document chunker"""
    chunker = SmartDocumentChunker(chunk_size=500, chunk_overlap=100)
    
    sample_text = """
    FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
    
    The key features are:
    
    Fast: Very high performance, on par with NodeJS and Go (thanks to Starlette and Pydantic). One of the fastest Python frameworks available.
    
    Fast to code: Increase the speed to develop features by about 200% to 300%.
    
    Fewer bugs: Reduce about 40% of human (developer) induced errors.
    
    Intuitive: Great editor support. Completion everywhere. Less time debugging.
    
    Easy: Designed to be easy to use and learn. Less time reading docs.
    
    Short: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.
    
    Robust: Get production-ready code. With automatic interactive documentation.
    
    Standards-based: Based on (and fully compatible with) the open standards for APIs: OpenAPI (previously known as Swagger) and JSON Schema.
    """
    
    import asyncio
    
    async def run_test():
        chunks = await chunker.chunk_document(
            content=sample_text,
            metadata={'title': 'FastAPI Introduction', 'source': 'fastapi', 'url': 'test'}
        )
        
        logger.info(f"Generated {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1}: {len(chunk['content'])} chars")
            logger.info(f"Content preview: {chunk['content'][:100]}...")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_chunker()




