/**
 * Chat Service - Real AI Integration
 * 
 * Handles communication with AI chatbot backend.
 * Supports both backend proxy and direct API calls.
 */

import { apiService, APIError } from './api';
import { API_CONFIG, AI_CONFIG } from './config';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  reply?: string;
  message?: string;
  content?: string;
  text?: string;
  answer?: string;
  data?: {
    reply?: string;
    message?: string;
    content?: string;
    text?: string;
    answer?: string;
  };
}

class ChatService {
  private backendAvailable: boolean = true;

  /**
   * Send chat request to backend
   */
  async sendChat(payload: ChatRequest, userId: string): Promise<string> {
    // Try backend first
    if (this.backendAvailable) {
      try {
        const response = await this.sendToBackend(payload, userId);
        return this.extractReply(response);
      } catch (error) {
        console.warn('Backend unavailable, falling back to direct API:', error);
        this.backendAvailable = false;
        
        // If backend is not available, try direct API
        return await this.sendToDirectAPI(payload);
      }
    } else {
      // Backend already known to be unavailable
      return await this.sendToDirectAPI(payload);
    }
  }

  /**
   * Send request through backend proxy
   */
  private async sendToBackend(
    payload: ChatRequest,
    userId: string
  ): Promise<ChatResponse> {
    try {
      const response = await apiService.post<ChatResponse>(
        API_CONFIG.CHAT_ENDPOINT,
        {
          ...payload,
          user_id: userId,
        },
        {
          'X-User-ID': userId,
        }
      );
      return response;
    } catch (error) {
      if (error instanceof APIError) {
        throw new Error(`Backend chat service error: ${error.message}`);
      }
      throw new Error('Backend chat bridge not available');
    }
  }

  /**
   * Send request directly to AI API (OpenAI)
   * This is a fallback when backend is unavailable
   */
  private async sendToDirectAPI(payload: ChatRequest): Promise<string> {
    const apiKey = AI_CONFIG.OPENAI_API_KEY;
    
    if (!apiKey) {
      throw new Error(
        'Backend chat bridge not available and no direct API key configured. ' +
        'Please set VITE_OPENAI_API_KEY in your environment or configure the backend.'
      );
    }

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: payload.model || AI_CONFIG.MODEL,
          messages: payload.messages,
          temperature: payload.temperature || AI_CONFIG.TEMPERATURE,
          max_tokens: payload.max_tokens || AI_CONFIG.MAX_TOKENS,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error?.message || `OpenAI API error: ${response.status}`);
      }

      const data = await response.json();
      return data.choices[0]?.message?.content || '';
    } catch (error) {
      throw new Error(
        `Direct API call failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Extract reply from various response formats
   * Following the same logic as the Python code
   */
  private extractReply(response: ChatResponse): string {
    // Check top-level keys
    for (const key of ['reply', 'message', 'content', 'text', 'answer']) {
      const value = (response as any)[key];
      if (typeof value === 'string' && value.trim()) {
        return value;
      }
    }

    // Check data object
    if (response.data && typeof response.data === 'object') {
      for (const key of ['reply', 'message', 'content', 'text', 'answer']) {
        const value = response.data[key];
        if (typeof value === 'string' && value.trim()) {
          return value;
        }
      }
    }

    throw new Error('Chat backend returned an unexpected response shape.');
  }

  /**
   * Test backend availability
   */
  async testConnection(): Promise<boolean> {
    try {
      await apiService.get('/health');
      this.backendAvailable = true;
      return true;
    } catch {
      this.backendAvailable = false;
      return false;
    }
  }

  /**
   * Check if backend is available
   */
  isBackendAvailable(): boolean {
    return this.backendAvailable;
  }
}

// Singleton instance
export const chatService = new ChatService();
