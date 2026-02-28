/**
 * Support Service — Zendesk Integration Client
 * 
 * TypeScript client for the CareerTrojan Support Bridge.
 * Creates tickets, lists tickets, and tracks ticket status.
 * 
 * Usage:
 *   import { supportService } from '@/services/supportService';
 *   
 *   const ticket = await supportService.createTicket({
 *     subject: 'Issue with resume parsing',
 *     description: 'My resume failed to upload...',
 *     category: 'bugs',
 *   });
 */

import { API } from '../lib/apiConfig';

// ══════════════════════════════════════════════════════════════════════════
// Types
// ══════════════════════════════════════════════════════════════════════════

export type TicketCategory = 'billing' | 'login' | 'ai_output' | 'bugs' | 'feature_request';
export type TicketPortal = 'user_portal' | 'admin_portal' | 'mentor_portal';
export type TicketStatus = 'new' | 'open' | 'pending' | 'hold' | 'solved' | 'closed';
export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface CreateTicketRequest {
  subject: string;
  description: string;
  category: TicketCategory;
  portal?: TicketPortal;
  requestId?: string;
  resumeVersionId?: number;
  extraMetadata?: Record<string, unknown>;
}

export interface TicketResponse {
  ticket_id: number;
  zendesk_ticket_id: number | null;
  zendesk_url: string | null;
  status: TicketStatus;
  priority: TicketPriority;
}

export interface TicketListItem {
  ticket_id: number;
  zendesk_ticket_id: number | null;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  created_at: string | null;
}

export interface TicketDetail extends TicketListItem {
  zendesk_url: string | null;
  description: string;
  portal: TicketPortal;
  updated_at: string | null;
  resolved_at: string | null;
}

// ══════════════════════════════════════════════════════════════════════════
// Helper: Get auth token
// ══════════════════════════════════════════════════════════════════════════

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('ct_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ══════════════════════════════════════════════════════════════════════════
// Support Service
// ══════════════════════════════════════════════════════════════════════════

export const supportService = {
  /**
   * Create a new support ticket
   */
  async createTicket(request: CreateTicketRequest): Promise<TicketResponse> {
    const response = await fetch(`${API.support}/tickets`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        subject: request.subject,
        description: request.description,
        category: request.category,
        portal: request.portal || 'admin_portal',
        request_id: request.requestId,
        resume_version_id: request.resumeVersionId,
        extra_metadata: request.extraMetadata,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create ticket' }));
      throw new Error(error.detail || 'Failed to create ticket');
    }

    return response.json();
  },

  /**
   * List the current user's support tickets
   */
  async listTickets(status?: TicketStatus, limit = 20): Promise<TicketListItem[]> {
    const params = new URLSearchParams();
    if (status) params.set('status_filter', status);
    params.set('limit', String(limit));

    const response = await fetch(`${API.support}/tickets?${params}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch tickets');
    }

    return response.json();
  },

  /**
   * Get details of a specific ticket
   */
  async getTicket(ticketId: number): Promise<TicketDetail> {
    const response = await fetch(`${API.support}/tickets/${ticketId}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Ticket not found');
    }

    return response.json();
  },

  /**
   * Check support service health
   */
  async checkHealth(): Promise<{ status: string; zendesk_configured: boolean }> {
    const response = await fetch(`${API.support}/health`);
    if (!response.ok) {
      throw new Error('Support service unavailable');
    }
    return response.json();
  },
};

export default supportService;
