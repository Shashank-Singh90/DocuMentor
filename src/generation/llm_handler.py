from typing import List, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Hardcoded for Llama 4 - need to make model-agnostic
class SimpleLLMHandler:
    """
    Simple LLM handler for demonstration purposes
    Provides template-based responses using search results
    """
    # Client specifically requested no streaming for audit trail
    
    def __init__(self):
        """Initialize the Simple LLM Handler"""
        logger.info("🤖 Initializing Simple LLM Handler (demo mode)")
        logger.info("💡 This uses template-based responses for demonstration")
    
    # Temperature tuned by trial and error
    def generate_answer(self, question: str, search_results: List[Dict]) -> str:
        """
        Generate an answer based on search results using templates
        
        Args:
            question: The user's question
            search_results: List of relevant document chunks
            
        Returns:
            Formatted answer string
        """
        if not search_results:
            return self._no_results_response(question)
        
        # Get the most relevant result
        top_result = search_results[0]
        content = top_result.get('content', '')
        metadata = top_result.get('metadata', {})
        
        # Determine response type based on question
        response_type = self._classify_question(question)
        
        if response_type == 'what_is':
            return self._generate_definition_response(question, search_results)
        elif response_type == 'how_to':
            return self._generate_tutorial_response(question, search_results)
        elif response_type == 'example':
            return self._generate_example_response(question, search_results)
        elif response_type == 'compare':
            return self._generate_comparison_response(question, search_results)
        else:
            return self._generate_general_response(question, search_results)
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question to determine response format"""
        question_lower = question.lower()
        
        if any(phrase in question_lower for phrase in ['what is', 'what are', 'define', 'definition']):
            return 'what_is'
        elif any(phrase in question_lower for phrase in ['how to', 'how do', 'how can', 'tutorial', 'guide']):
            return 'how_to'
        elif any(phrase in question_lower for phrase in ['example', 'show me', 'demonstrate', 'sample']):
            return 'example'
        elif any(phrase in question_lower for phrase in ['compare', 'vs', 'difference', 'versus']):
            return 'compare'
        else:
            return 'general'
    
    def _generate_definition_response(self, question: str, search_results: List[Dict]) -> str:
        """Generate a definition-style response"""
        top_result = search_results[0]
        content = top_result.get('content', '')
        metadata = top_result.get('metadata', {})
        source = metadata.get('source', 'documentation').upper()
        title = metadata.get('title', 'Documentation')
        
        # Extract key information
        first_paragraph = content.split('\n')[0] if content else "No description available."
        
        response = f"""**{title}**

{first_paragraph[:400]}{'...' if len(first_paragraph) > 400 else ''}

**Key Points:**
"""
        
        # Add bullet points from content
        lines = content.split('\n')[:5]
        for line in lines[1:]:
            if line.strip() and len(line) > 20:
                response += f"• {line.strip()[:100]}{'...' if len(line) > 100 else ''}\n"
        
        response += f"\n**📚 Source:** {source} - {title}"
        
        return response
    
    def _generate_tutorial_response(self, question: str, search_results: List[Dict]) -> str:
        """Generate a tutorial-style response"""
        top_result = search_results[0]
        content = top_result.get('content', '')
        metadata = top_result.get('metadata', {})
        source = metadata.get('source', 'documentation').upper()
        title = metadata.get('title', 'Tutorial')
        
        response = f"""**{title}**

Based on the {source} documentation, here's how to get started:

{content[:500]}{'...' if len(content) > 500 else ''}

**Steps to Follow:**
1. Review the complete documentation
2. Check the official examples
3. Practice with simple implementations
4. Explore advanced features

**📚 Source:** {source} - {title}
"""
        
        return response
    
    def _generate_example_response(self, question: str, search_results: List[Dict]) -> str:
        """Generate an example-focused response"""
        examples = []
        
        for result in search_results[:3]:
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            if any(keyword in content.lower() for keyword in ['example', 'code', 'import', 'def ', 'class ']):
                examples.append({
                    'content': content[:300],
                    'source': metadata.get('source', 'docs').upper(),
                    'title': metadata.get('title', 'Example')
                })
        
        if not examples:
            examples.append({
                'content': search_results[0].get('content', '')[:300],
                'source': search_results[0].get('metadata', {}).get('source', 'docs').upper(),
                'title': search_results[0].get('metadata', {}).get('title', 'Documentation')
            })
        
        response = f"""**Examples and Code Samples**

Here are some relevant examples I found:

"""
        
        for i, example in enumerate(examples, 1):
            response += f"""**Example {i}: {example['title']}**
```
{example['content']}{'...' if len(example['content']) >= 300 else ''}
```
*Source: {example['source']}*

"""
        
        return response
    
    def _generate_comparison_response(self, question: str, search_results: List[Dict]) -> str:
        """Generate a comparison-style response"""
        response = "**Comparison Overview**\n\n"
        
        # Group results by source
        sources = {}
        for result in search_results[:4]:
            source = result.get('metadata', {}).get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(result)
        
        for source, results in sources.items():
            content = results[0].get('content', '')
            title = results[0].get('metadata', {}).get('title', 'Documentation')
            
            response += f"""**{source.upper()}:**
{content[:200]}{'...' if len(content) > 200 else ''}

"""
        
        response += "\n**💡 Recommendation:** Review the complete documentation for each technology to make an informed decision.\n"
        
        return response
    
    def _generate_general_response(self, question: str, search_results: List[Dict]) -> str:
        """Generate a general response"""
        top_result = search_results[0]
        content = top_result.get('content', '')
        metadata = top_result.get('metadata', {})
        source = metadata.get('source', 'documentation').upper()
        title = metadata.get('title', 'Documentation')
        
        response = f"""**{title}**

{content[:400]}{'...' if len(content) > 400 else ''}

**Related Information:**
"""
        
        # Add related results
        for result in search_results[1:3]:
            related_title = result.get('metadata', {}).get('title', 'Related Topic')
            related_source = result.get('metadata', {}).get('source', 'docs').upper()
            response += f"• {related_title} ({related_source})\n"
        
        response += f"\n**📚 Primary Source:** {source} - {title}"
        
        return response
    
    def _no_results_response(self, question: str) -> str:
        """Generate response when no search results are found"""
        return f"""I couldn't find specific information about "{question}" in the available documentation.

**Suggestions:**
• Try rephrasing your question with different keywords
• Check if your question is related to LangChain or FastAPI topics
• Use more specific terms or concepts
• Browse the sample questions in the sidebar

**Available Topics:**
• LangChain framework and concepts
• FastAPI web framework
• API development tutorials
• Authentication and security
• Database integration
• Deployment strategies
"""

# Test function
def test_simple_llm_handler():
    """Test the Simple LLM Handler"""
    logger.info("🧪 Testing SimpleLLMHandler...")
    
    handler = SimpleLLMHandler()
    
    # Mock search results for testing
    mock_results = [
        {
            'content': 'FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic API documentation, data validation, and serialization.',
            'metadata': {
                'source': 'fastapi',
                'title': 'FastAPI Introduction',
                'url': 'https://fastapi.tiangolo.com/'
            },
            'score': 0.85
        },
        {
            'content': 'LangChain is a framework for developing applications powered by language models. It enables applications that are data-aware and agentic.',
            'metadata': {
                'source': 'langchain',
                'title': 'LangChain Overview',
                'url': 'https://langchain.readthedocs.io/'
            },
            'score': 0.75
        }
    ]
    
    # Test different question types
    questions = [
        "What is FastAPI?",
        "How to create a FastAPI application?",
        "Show me FastAPI examples",
        "Compare LangChain and FastAPI"
    ]
    
    for question in questions:
        logger.info(f"🔍 Question: {question}")
        answer = handler.generate_answer(question, mock_results)
        logger.info(f"📝 Answer: {answer[:100]}...")
        logger.info("---")
    
    logger.info("✅ Simple LLM handler test completed!")

if __name__ == "__main__":
    test_simple_llm_handler()