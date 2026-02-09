/**
 * Knowledge Base Service
 * 
 * Handles knowledge base retrieval and search
 */

import { apiService } from './api';
import { API_CONFIG } from './config';

export interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: {
    id: string;
    name: string;
  };
  views: number;
  helpful_count: number;
}

export interface KnowledgeCategory {
  id: string;
  name: string;
  description: string;
  article_count: number;
}

class KnowledgeBaseService {
  /**
   * Get all categories
   */
  async getCategories(): Promise<KnowledgeCategory[]> {
    return await apiService.get<KnowledgeCategory[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/categories`
    );
  }

  /**
   * Get articles by category
   */
  async getArticlesByCategory(categoryId: string): Promise<KnowledgeArticle[]> {
    return await apiService.get<KnowledgeArticle[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/categories/${categoryId}/articles`
    );
  }

  /**
   * Get single article
   */
  async getArticle(articleId: string): Promise<KnowledgeArticle> {
    return await apiService.get<KnowledgeArticle>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/articles/${articleId}`
    );
  }

  /**
   * Search articles
   */
  async searchArticles(query: string): Promise<KnowledgeArticle[]> {
    return await apiService.get<KnowledgeArticle[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/search?q=${encodeURIComponent(query)}`
    );
  }

  /**
   * Get popular articles
   */
  async getPopularArticles(limit: number = 10): Promise<KnowledgeArticle[]> {
    return await apiService.get<KnowledgeArticle[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/popular?limit=${limit}`
    );
  }

  /**
   * Get recent articles
   */
  async getRecentArticles(limit: number = 10): Promise<KnowledgeArticle[]> {
    return await apiService.get<KnowledgeArticle[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/recent?limit=${limit}`
    );
  }

  /**
   * Mark article as helpful
   */
  async markHelpful(articleId: string): Promise<void> {
    await apiService.post(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/articles/${articleId}/helpful`,
      {}
    );
  }

  /**
   * Get related articles
   */
  async getRelatedArticles(articleId: string): Promise<KnowledgeArticle[]> {
    return await apiService.get<KnowledgeArticle[]>(
      `${API_CONFIG.KNOWLEDGE_BASE_ENDPOINT}/articles/${articleId}/related`
    );
  }
}

// Singleton instance
export const knowledgeBaseService = new KnowledgeBaseService();
