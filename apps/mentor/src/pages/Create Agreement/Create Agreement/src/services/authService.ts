/**
 * Authentication Service
 * 
 * Handles user authentication and session management
 */

import { apiService } from './api';
import { API_CONFIG } from './config';

export interface User {
  id: string;
  role: 'mentor' | 'mentee' | 'admin';
  email?: string;
  name?: string;
  mentor_id?: string;
}

export interface SessionState {
  user: User | null;
  isAuthenticated: boolean;
  token?: string;
}

class AuthService {
  private session: SessionState = {
    user: null,
    isAuthenticated: false,
  };

  /**
   * Initialize session from localStorage or backend
   */
  async initializeSession(): Promise<SessionState> {
    // Check localStorage first
    const storedSession = localStorage.getItem('session');
    if (storedSession) {
      try {
        const parsed = JSON.parse(storedSession);
        this.session = parsed;
        
        // Validate session with backend
        await this.validateSession();
        return this.session;
      } catch {
        localStorage.removeItem('session');
      }
    }

    // Try to get session from backend
    try {
      const response = await apiService.get<{ user: User; token: string }>(
        `${API_CONFIG.AUTH_ENDPOINT}/session`
      );
      
      this.session = {
        user: response.user,
        isAuthenticated: true,
        token: response.token,
      };
      
      this.saveSession();
      return this.session;
    } catch {
      // No session available, use mock session for development
      this.session = this.getMockSession();
      return this.session;
    }
  }

  /**
   * Validate current session with backend
   */
  private async validateSession(): Promise<boolean> {
    if (!this.session.token) return false;

    try {
      await apiService.get(`${API_CONFIG.AUTH_ENDPOINT}/validate`, {
        Authorization: `Bearer ${this.session.token}`,
      });
      return true;
    } catch {
      this.clearSession();
      return false;
    }
  }

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<User> {
    try {
      const response = await apiService.post<{ user: User; token: string }>(
        `${API_CONFIG.AUTH_ENDPOINT}/login`,
        { email, password }
      );

      this.session = {
        user: response.user,
        isAuthenticated: true,
        token: response.token,
      };

      this.saveSession();
      return response.user;
    } catch (error) {
      throw new Error('Login failed: Invalid credentials');
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      if (this.session.token) {
        await apiService.post(`${API_CONFIG.AUTH_ENDPOINT}/logout`, {}, {
          Authorization: `Bearer ${this.session.token}`,
        });
      }
    } catch {
      // Ignore logout errors
    } finally {
      this.clearSession();
    }
  }

  /**
   * Get current session
   */
  getSession(): SessionState {
    return this.session;
  }

  /**
   * Check if user is mentor
   */
  isMentor(): boolean {
    return this.session.user?.role === 'mentor';
  }

  /**
   * Get mentor ID
   */
  getMentorId(): string | null {
    if (this.session.user?.role === 'mentor') {
      return this.session.user.mentor_id || this.session.user.id;
    }
    return null;
  }

  /**
   * Save session to localStorage
   */
  private saveSession(): void {
    localStorage.setItem('session', JSON.stringify(this.session));
  }

  /**
   * Clear session
   */
  private clearSession(): void {
    this.session = {
      user: null,
      isAuthenticated: false,
    };
    localStorage.removeItem('session');
  }

  /**
   * Get mock session for development
   */
  private getMockSession(): SessionState {
    return {
      user: {
        id: 'mentor_dev_001',
        role: 'mentor',
        email: 'mentor@intellicv.ai',
        name: 'Development Mentor',
        mentor_id: 'mentor_dev_001',
      },
      isAuthenticated: true,
      token: 'dev_token_12345',
    };
  }

  /**
   * Require mentor authentication
   * Throws error if user is not a mentor
   */
  requireMentorAuth(): void {
    if (!this.session.isAuthenticated) {
      throw new Error('Authentication required');
    }

    if (this.session.user?.role !== 'mentor') {
      throw new Error('🚫 Mentor access only');
    }

    const mentorId = this.getMentorId();
    if (!mentorId) {
      throw new Error('Mentor identity is not available in session (mentor_id missing).');
    }
  }
}

// Singleton instance
export const authService = new AuthService();
