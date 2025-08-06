// api/documenter.js - API service for DocuMentor

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class DocuMentorAPI {
  // Main chat function
  async askQuestion(question, sourceFilter = null, k = 5) {
    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          source_filter: sourceFilter,
          k,
          temperature: 0.1,
          max_tokens: 1024
        }),
      });

      if (!response.ok) {
        throw new Error('API request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Error asking question:', error);
      throw error;
    }
  }

  // Stream responses for better UX
  async askQuestionStream(question, sourceFilter = null, onChunk) {
    const response = await fetch(`${API_BASE_URL}/stream-ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        source_filter: sourceFilter,
        k: 5,
        temperature: 0.1,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onChunk(data);
          } catch (e) {
            console.error('Error parsing SSE:', e);
          }
        }
      }
    }
  }

  // Search documentation
  async searchDocs(query, k = 10, sourceFilter = null) {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        k,
        source_filter: sourceFilter,
      }),
    });

    return await response.json();
  }

  // Upload document
  async uploadDocument(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      // Track upload progress
      onUploadProgress: onProgress,
    });

    return await response.json();
  }

  // Get available sources
  async getSources() {
    const response = await fetch(`${API_BASE_URL}/sources`);
    return await response.json();
  }

  // Get statistics
  async getStats() {
    const response = await fetch(`${API_BASE_URL}/stats`);
    return await response.json();
  }

  // Submit feedback
  async submitFeedback(messageId, feedback) {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message_id: messageId,
        feedback,
      }),
    });

    return await response.json();
  }
}

export default new DocuMentorAPI();

// Usage in React component:
/*
import DocuMentorAPI from './api/documenter';

// In your component
const handleSendMessage = async (message) => {
  setLoading(true);
  try {
    // For streaming responses
    await DocuMentorAPI.askQuestionStream(
      message,
      selectedSource,
      (chunk) => {
        if (chunk.type === 'sources') {
          setSources(chunk.data);
        } else if (chunk.type === 'answer') {
          setResponse(prev => prev + chunk.data);
        }
      }
    );
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setLoading(false);
  }
};
*/