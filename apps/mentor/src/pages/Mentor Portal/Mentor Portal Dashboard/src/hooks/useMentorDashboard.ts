/**
 * Custom Hook for Mentor Dashboard Data
 * 
 * Manages all data fetching and state for the mentor dashboard.
 * Ready for backend integration.
 */

import { useState, useEffect } from 'react';
import { mentorshipService } from '../services/mentorship-service';

export interface DashboardMetrics {
  totalEarnings: number;
  sessionsCompleted: number;
  averageRating: number;
  activeMentees: number;
  rebookingRate: string;
}

export interface MonthlyEarning {
  month: string;
  earnings: number;
  sessions: number;
}

export interface StatusDistribution {
  name: string;
  value: number;
  color: string;
}

export function useMentorDashboard(mentorId: string | null) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalEarnings: 0,
    sessionsCompleted: 0,
    averageRating: 0,
    activeMentees: 0,
    rebookingRate: 'N/A',
  });

  const [earningsData, setEarningsData] = useState<MonthlyEarning[]>([]);
  const [statusDistribution, setStatusDistribution] = useState<StatusDistribution[]>([]);
  const [activeMentees, setActiveMentees] = useState<any[]>([]);
  const [actionItems, setActionItems] = useState({
    pendingPayout: 0,
    pendingDocuments: 0,
    newReviews: 0,
  });

  useEffect(() => {
    if (!mentorId) {
      setLoading(false);
      return;
    }

    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch all data in parallel
        const [
          invoices,
          connections,
          sessionsCount,
          avgRating
        ] = await Promise.all([
          mentorshipService.getMentorInvoices(mentorId),
          mentorshipService.getMentorConnections(mentorId),
          mentorshipService.getSessionsCompleted(mentorId),
          mentorshipService.getAverageRating(mentorId),
        ]);

        // Calculate total earnings
        const totalEarnings = invoices
          .filter(inv => ['paid', 'released'].includes(inv.status))
          .reduce((sum, inv) => sum + inv.mentor_portion, 0);

        // Get active mentees
        const activeConnections = connections.filter(c => c.status === 'active');

        // Calculate pending payout
        const pendingPayout = invoices
          .filter(inv => inv.status === 'held')
          .reduce((sum, inv) => sum + inv.mentor_portion, 0);

        // Update metrics
        setMetrics({
          totalEarnings,
          sessionsCompleted: sessionsCount,
          averageRating: avgRating,
          activeMentees: activeConnections.length,
          rebookingRate: 'N/A', // TODO: Calculate from backend
        });

        // Update charts data
        const monthlyEarnings = mentorshipService.calculateMonthlyEarnings(invoices);
        setEarningsData(monthlyEarnings);

        const distribution = mentorshipService.calculateStatusDistribution(connections);
        setStatusDistribution(distribution);

        // Update lists
        setActiveMentees(activeConnections.slice(0, 5)); // Top 5

        // Update action items
        setActionItems({
          pendingPayout,
          pendingDocuments: 0, // TODO: Fetch from backend
          newReviews: 0, // TODO: Fetch from backend
        });

      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [mentorId]);

  return {
    loading,
    error,
    metrics,
    earningsData,
    statusDistribution,
    activeMentees,
    actionItems,
  };
}
