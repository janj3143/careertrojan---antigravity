import { useState, useEffect } from 'react';
import { projectId, publicAnonKey } from '../../../utils/supabase/info';
import { supabase } from '../../../utils/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Calendar, Clock, User, Package, LogOut, Plus, Check, X, Clock3, FileText } from 'lucide-react';
import { AddSessionDialog } from './AddSessionDialog';
import { toast } from 'sonner';
import { Toaster } from './ui/sonner';
import backgroundImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

const API_BASE = `https://${projectId}.supabase.co/functions/v1/make-server-f4611869`;

interface Session {
  id: string;
  mentor_id: string;
  mentee_id: string | null;
  mentee_name: string;
  package_name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  created_at: string;
  updated_at: string;
}

interface Activity {
  user_id: string;
  action: string;
  details: string;
  timestamp: string;
}

interface SessionCalendarProps {
  session: any;
  onSignOut: () => void;
}

export function SessionCalendar({ session, onSignOut }: SessionCalendarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([loadSessions(), loadActivities()]);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/sessions`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
      throw error;
    }
  };

  const loadActivities = async () => {
    try {
      const response = await fetch(`${API_BASE}/activities`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch activities');
      }

      const data = await response.json();
      setActivities(data.activities || []);
    } catch (error) {
      console.error('Error loading activities:', error);
      throw error;
    }
  };

  const handleUpdateStatus = async (sessionId: string, status: string) => {
    try {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
      });

      if (!response.ok) {
        throw new Error('Failed to update session');
      }

      await loadData();
      toast.success(`Session ${status}`);
    } catch (error) {
      console.error('Error updating session:', error);
      toast.error('Failed to update session');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to cancel this session?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      await loadData();
      toast.success('Session cancelled');
    } catch (error) {
      console.error('Error deleting session:', error);
      toast.error('Failed to cancel session');
    }
  };

  const handleAddSession = async (data: any) => {
    try {
      const response = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      await loadData();
      setShowAddDialog(false);
      toast.success('Session added successfully');
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Failed to create session');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'confirmed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'completed':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const formatActivityTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Filter upcoming sessions (next 14 days)
  const now = new Date();
  const fourteenDaysLater = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);
  const upcomingSessions = sessions
    .filter(s => {
      const startDate = new Date(s.start_time);
      return startDate >= now && startDate <= fourteenDaysLater;
    })
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading sessions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Image - Exact PNG, No Overlay */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          imageRendering: 'crisp-edges',
        }}
      />

      {/* Content */}
      <div className="relative z-10">
        <Toaster />
        
        {/* Header */}
        <div className="bg-white/95 backdrop-blur-sm border-b border-white/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center shadow-lg">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Sessions & Availability</h1>
                  <p className="text-sm text-gray-600">Mentor Portal</p>
                </div>
              </div>
              <Button variant="outline" onClick={onSignOut} className="bg-white/80 backdrop-blur-sm">
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Sessions List */}
            <div className="lg:col-span-2">
              <Card className="bg-white/95 backdrop-blur-sm shadow-2xl border-white/20">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle>🗓 Upcoming Sessions</CardTitle>
                      <CardDescription>Next 14 days</CardDescription>
                    </div>
                    <Button onClick={() => setShowAddDialog(true)} className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Session
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {upcomingSessions.length === 0 ? (
                    <div className="text-center py-12">
                      <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">No sessions scheduled</p>
                      <Button 
                        variant="outline" 
                        className="mt-4"
                        onClick={() => setShowAddDialog(true)}
                      >
                        Schedule your first session
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {upcomingSessions.map((session) => (
                        <div
                          key={session.id}
                          className="border border-gray-200 bg-white rounded-lg p-4 hover:shadow-xl transition-all duration-200 hover:border-blue-300"
                        >
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h3 className="font-semibold text-gray-900">{session.mentee_name}</h3>
                                <Badge className={getStatusColor(session.status)}>
                                  {session.status.toUpperCase()}
                                </Badge>
                              </div>
                              <div className="space-y-1 text-sm text-gray-600">
                                <div className="flex items-center gap-2">
                                  <Package className="w-4 h-4" />
                                  <span>{session.package_name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Clock className="w-4 h-4" />
                                  <span>{formatDate(session.start_time)}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Clock3 className="w-4 h-4" />
                                  <span>{session.duration_minutes} minutes</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="flex gap-2 flex-wrap">
                            {session.status === 'pending' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleUpdateStatus(session.id, 'confirmed')}
                                className="text-green-600 hover:text-green-700 hover:bg-green-50"
                              >
                                <Check className="w-3 h-3 mr-1" />
                                Confirm
                              </Button>
                            )}
                            {session.status !== 'cancelled' && session.status !== 'completed' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => toast.info('Rescheduling flow to be integrated with calendar API')}
                                  className="hover:bg-blue-50"
                                >
                                  <Clock className="w-3 h-3 mr-1" />
                                  Reschedule
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteSession(session.id)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <X className="w-3 h-3 mr-1" />
                                  Cancel
                                </Button>
                              </>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => toast.info('Session notes feature coming soon')}
                              className="hover:bg-gray-50"
                            >
                              <FileText className="w-3 h-3 mr-1" />
                              Notes
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Activity Feed */}
            <div>
              <Card className="bg-white/95 backdrop-blur-sm shadow-2xl border-white/20">
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>Last 30 activities</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[600px]">
                    {activities.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 text-sm">
                        No recent activity
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {activities.map((activity, index) => (
                          <div key={index}>
                            <div className="flex gap-3">
                              <div className="flex-shrink-0">
                                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-900">{activity.details}</p>
                                <p className="text-xs text-gray-500 mt-1">
                                  {formatActivityTime(activity.timestamp)}
                                </p>
                              </div>
                            </div>
                            {index < activities.length - 1 && (
                              <Separator className="my-3" />
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="mt-6 text-center text-sm text-white/90 bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
            <p className="font-medium">Mentor Portal • Sessions Calendar</p>
            <p className="mt-1">Planned enhancements: ICS sync, Google Calendar, reminders, rescheduling rules</p>
          </div>
        </div>
      </div>

      <AddSessionDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onSubmit={handleAddSession}
      />
    </div>
  );
}