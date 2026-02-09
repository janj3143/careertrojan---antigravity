/**
 * Mentorship Service - Backend API Integration
 * 
 * This service provides methods to interact with the mentorship backend.
 * Currently implemented as stubs ready for live API connection.
 */

export interface Invoice {
  id: string;
  mentor_portion: number;
  status: 'pending' | 'held' | 'paid' | 'released';
  paid_date?: string;
  created_at: string;
}

export interface MenteeConnection {
  link_id: string;
  anonymous_name: string;
  status: 'active' | 'completed' | 'pending' | 'cancelled';
  created_at: string;
  updated_at: string;
}

export interface SessionData {
  id: string;
  mentee_id: string;
  scheduled_date: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  duration_minutes: number;
}

export interface Review {
  id: string;
  mentee_id: string;
  rating: number;
  comment: string;
  created_at: string;
}

export class MentorshipService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Get all invoices for a mentor
   */
  async getMentorInvoices(mentorId: string): Promise<Invoice[]> {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${this.baseUrl}/mentors/${mentorId}/invoices`);
      // return await response.json();
      
      return []; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching mentor invoices:', error);
      return [];
    }
  }

  /**
   * Get mentor connections (mentees)
   */
  async getMentorConnections(
    mentorId: string, 
    status?: 'active' | 'completed' | 'pending'
  ): Promise<MenteeConnection[]> {
    try {
      // TODO: Replace with actual API call
      // const url = status 
      //   ? `${this.baseUrl}/mentors/${mentorId}/connections?status=${status}`
      //   : `${this.baseUrl}/mentors/${mentorId}/connections`;
      // const response = await fetch(url);
      // return await response.json();
      
      return []; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching mentor connections:', error);
      return [];
    }
  }

  /**
   * Get completed sessions count
   */
  async getSessionsCompleted(mentorId: string): Promise<number> {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${this.baseUrl}/mentors/${mentorId}/sessions/completed/count`);
      // const data = await response.json();
      // return data.count;
      
      return 0; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching sessions completed:', error);
      return 0;
    }
  }

  /**
   * Get average rating from reviews
   */
  async getAverageRating(mentorId: string): Promise<number> {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${this.baseUrl}/mentors/${mentorId}/reviews/average`);
      // const data = await response.json();
      // return data.average;
      
      return 0; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching average rating:', error);
      return 0;
    }
  }

  /**
   * Get upcoming sessions
   */
  async getUpcomingSessions(mentorId: string): Promise<SessionData[]> {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${this.baseUrl}/mentors/${mentorId}/sessions/upcoming`);
      // return await response.json();
      
      return []; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching upcoming sessions:', error);
      return [];
    }
  }

  /**
   * Get recent reviews
   */
  async getRecentReviews(mentorId: string, limit: number = 5): Promise<Review[]> {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${this.baseUrl}/mentors/${mentorId}/reviews?limit=${limit}`);
      // return await response.json();
      
      return []; // Empty for now - ready for backend connection
    } catch (error) {
      console.error('Error fetching recent reviews:', error);
      return [];
    }
  }

  /**
   * Calculate earnings by month for charts
   */
  calculateMonthlyEarnings(invoices: Invoice[]): Array<{
    month: string;
    earnings: number;
    sessions: number;
  }> {
    const monthlyData: Record<string, { earnings: number; sessions: number }> = {};

    invoices.forEach(inv => {
      if (inv.paid_date) {
        const monthKey = inv.paid_date.substring(0, 7); // YYYY-MM
        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = { earnings: 0, sessions: 0 };
        }
        monthlyData[monthKey].earnings += inv.mentor_portion;
        monthlyData[monthKey].sessions += 1;
      }
    });

    const sortedMonths = Object.keys(monthlyData).sort().slice(-6); // Last 6 months
    
    return sortedMonths.map(month => ({
      month,
      earnings: monthlyData[month].earnings,
      sessions: monthlyData[month].sessions,
    }));
  }

  /**
   * Calculate status distribution for pie chart
   */
  calculateStatusDistribution(connections: MenteeConnection[]): Array<{
    name: string;
    value: number;
    color: string;
  }> {
    const statusCounts: Record<string, number> = {};
    const statusColors: Record<string, string> = {
      'active': '#22c55e',
      'completed': '#3b82f6',
      'pending': '#f59e0b',
      'cancelled': '#ef4444',
    };

    connections.forEach(conn => {
      const status = conn.status;
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });

    return Object.entries(statusCounts).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      color: statusColors[name] || '#6b7280',
    }));
  }
}

// Export singleton instance
export const mentorshipService = new MentorshipService();
