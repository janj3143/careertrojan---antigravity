/**
 * API Configuration
 * 
 * Configure your backend endpoints and API keys here.
 * In production, use environment variables.
 */

export const API_CONFIG = {
  // Backend API base URL
  BASE_URL: import.meta.env.VITE_API_BASE_URL || '/api',
  
  // AI Chat endpoint
  CHAT_ENDPOINT: '/chat',
  
  // Forum endpoint
  FORUM_ENDPOINT: '/forum',
  
  // Knowledge base endpoint
  KNOWLEDGE_BASE_ENDPOINT: '/knowledge',
  
  // Authentication endpoint
  AUTH_ENDPOINT: '/auth',
  
  // Request timeout (ms)
  TIMEOUT: 30000,
};

export const AI_CONFIG = {
  // OpenAI API key (alternative to backend proxy)
  OPENAI_API_KEY: import.meta.env.VITE_OPENAI_API_KEY || '',
  
  // Anthropic API key (alternative to backend proxy)
  ANTHROPIC_API_KEY: import.meta.env.VITE_ANTHROPIC_API_KEY || '',
  
  // Model selection
  MODEL: import.meta.env.VITE_AI_MODEL || 'gpt-4',
  
  // Max tokens
  MAX_TOKENS: 2000,
  
  // Temperature
  TEMPERATURE: 0.7,
};
