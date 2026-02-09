/**
 * Forum Service
 * 
 * Handles community forum operations
 */

import { apiService } from './api';
import { API_CONFIG } from './config';

export interface ForumPost {
  id: string;
  title: string;
  content: string;
  author: {
    id: string;
    name: string;
    role: string;
  };
  created_at: string;
  updated_at: string;
  replies_count: number;
  likes_count: number;
  tags: string[];
}

export interface ForumReply {
  id: string;
  post_id: string;
  content: string;
  author: {
    id: string;
    name: string;
    role: string;
  };
  created_at: string;
  likes_count: number;
}

class ForumService {
  /**
   * Get forum posts
   */
  async getPosts(params?: {
    page?: number;
    limit?: number;
    tag?: string;
  }): Promise<{ posts: ForumPost[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.tag) queryParams.set('tag', params.tag);

    const endpoint = `${API_CONFIG.FORUM_ENDPOINT}/posts${
      queryParams.toString() ? `?${queryParams}` : ''
    }`;

    return await apiService.get<{ posts: ForumPost[]; total: number }>(endpoint);
  }

  /**
   * Get single post with replies
   */
  async getPost(postId: string): Promise<{
    post: ForumPost;
    replies: ForumReply[];
  }> {
    return await apiService.get<{ post: ForumPost; replies: ForumReply[] }>(
      `${API_CONFIG.FORUM_ENDPOINT}/posts/${postId}`
    );
  }

  /**
   * Create new post
   */
  async createPost(data: {
    title: string;
    content: string;
    tags?: string[];
  }): Promise<ForumPost> {
    return await apiService.post<ForumPost>(
      `${API_CONFIG.FORUM_ENDPOINT}/posts`,
      data
    );
  }

  /**
   * Create reply
   */
  async createReply(postId: string, content: string): Promise<ForumReply> {
    return await apiService.post<ForumReply>(
      `${API_CONFIG.FORUM_ENDPOINT}/posts/${postId}/replies`,
      { content }
    );
  }

  /**
   * Like post
   */
  async likePost(postId: string): Promise<void> {
    await apiService.post(`${API_CONFIG.FORUM_ENDPOINT}/posts/${postId}/like`, {});
  }

  /**
   * Search posts
   */
  async searchPosts(query: string): Promise<ForumPost[]> {
    return await apiService.get<ForumPost[]>(
      `${API_CONFIG.FORUM_ENDPOINT}/search?q=${encodeURIComponent(query)}`
    );
  }
}

// Singleton instance
export const forumService = new ForumService();
