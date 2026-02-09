/**
 * Services Index
 * 
 * Central export for all services
 */

export { apiService, APIError } from './api';
export { chatService } from './chatService';
export { authService } from './authService';
export { forumService } from './forumService';
export { knowledgeBaseService } from './knowledgeBaseService';
export { API_CONFIG, AI_CONFIG } from './config';

export type { ChatMessage, ChatRequest, ChatResponse } from './chatService';
export type { User, SessionState } from './authService';
export type { ForumPost, ForumReply } from './forumService';
export type { KnowledgeArticle, KnowledgeCategory } from './knowledgeBaseService';
