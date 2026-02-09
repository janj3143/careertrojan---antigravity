/**
 * Base API Service
 * 
 * Handles HTTP requests to the backend API
 */

import { API_CONFIG } from './config';

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class APIService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
  }

  /**
   * Make a fetch request with timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new APIError('Request timeout');
      }
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, headers: Record<string, string> = {}): Promise<T> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseURL}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    data: any,
    headers: Record<string, string> = {}
  ): Promise<T> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseURL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    data: any,
    headers: Record<string, string> = {}
  ): Promise<T> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseURL}${endpoint}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, headers: Record<string, string> = {}): Promise<T> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseURL}${endpoint}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }
}

export const apiService = new APIService();
