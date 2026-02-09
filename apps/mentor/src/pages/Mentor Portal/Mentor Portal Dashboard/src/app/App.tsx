import { useState } from 'react';
import { 
  DollarSign, 
  Calendar, 
  Star, 
  Users, 
  RefreshCw, 
  TrendingUp,
  FileText,
  Eye,
  Package,
  MessageSquare,
  Shield,
  ArrowRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Alert, AlertDescription } from './components/ui/alert';
import { 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Line,
  ComposedChart
} from 'recharts';
import headerImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';
import { useMentorDashboard } from '../hooks/useMentorDashboard';

// Authentication state - to be connected to real auth system
// TODO: Replace with actual authentication context/provider
const mockUser = {
  authenticated: false,
  name: '', // Will be populated from auth system
  role: '', // 'mentor' or 'admin'
  id: null, // Mentor ID from backend
};

export default function App() {
  const [timePeriod, setTimePeriod] = useState('This Month');
  
  // Fetch dashboard data using custom hook
  const {
    loading,
    error,
    metrics,
    earningsData,
    statusDistribution,
    activeMentees,
    actionItems,
  } = useMentorDashboard(mockUser.id);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header with Background Image */}
      <div className="relative h-48 bg-gradient-to-r from-blue-600 to-blue-800 overflow-hidden">
        <img 
          src={headerImage} 
          alt="Mentor Dashboard" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 flex flex-col justify-center px-8">
          <h1 className="text-white mb-2">📊 Mentor Dashboard</h1>
          <p className="text-blue-100">
            {mockUser.name ? (
              <>
                <strong>Welcome back, {mockUser.name}!</strong> | Here is your professional overview.
              </>
            ) : (
              <>
                <strong>Welcome back!</strong> | Here is your professional overview.
              </>
            )}
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Quick Actions Section */}
        <div className="mb-8">
          <h2 className="mb-4">🚀 Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button 
              variant="outline" 
              className="h-auto py-4 flex items-center justify-start gap-3"
            >
              <Package className="h-5 w-5 text-blue-600" />
              <div className="text-left">
                <div className="font-medium">Service Packages</div>
                <div className="text-xs text-slate-500">Manage offerings</div>
              </div>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto py-4 flex items-center justify-start gap-3"
            >
              <MessageSquare className="h-5 w-5 text-green-600" />
              <div className="text-left">
                <div className="font-medium">Message Center</div>
                <div className="text-xs text-slate-500">Chat with mentees</div>
              </div>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto py-4 flex items-center justify-start gap-3"
            >
              <DollarSign className="h-5 w-5 text-purple-600" />
              <div className="text-left">
                <div className="font-medium">Financials</div>
                <div className="text-xs text-slate-500">View earnings</div>
              </div>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto py-4 flex items-center justify-start gap-3"
            >
              <Shield className="h-5 w-5 text-orange-600" />
              <div className="text-left">
                <div className="font-medium">Guardian Feedback</div>
                <div className="text-xs text-slate-500">Parent reviews</div>
              </div>
            </Button>
          </div>
        </div>

        <Separator className="my-8" />

        {/* Time Period Selector */}
        <div className="flex justify-between items-center mb-6">
          <h2>📈 Performance Metrics</h2>
          <Select value={timePeriod} onValueChange={setTimePeriod}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="This Week">This Week</SelectItem>
              <SelectItem value="This Month">This Month</SelectItem>
              <SelectItem value="Last 3 Months">Last 3 Months</SelectItem>
              <SelectItem value="All Time">All Time</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Performance Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
              <DollarSign className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                £{metrics.totalEarnings.toLocaleString()}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {metrics.totalEarnings > 0 ? 'All time' : 'No earnings yet'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sessions Done</CardTitle>
              <Calendar className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.sessionsCompleted}</div>
              <p className="text-xs text-slate-500 mt-1">
                {metrics.sessionsCompleted > 0 ? 'Completed' : 'No sessions yet'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Rating</CardTitle>
              <Star className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.averageRating > 0 ? `${metrics.averageRating.toFixed(1)}/5` : 'N/A'}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {metrics.averageRating > 0 ? 'From reviews' : 'No reviews yet'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Mentees</CardTitle>
              <Users className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.activeMentees}</div>
              <p className="text-xs text-slate-500 mt-1">
                {metrics.activeMentees > 0 ? 'Currently mentoring' : 'No mentees yet'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Rebooking</CardTitle>
              <RefreshCw className="h-4 w-4 text-indigo-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.rebookingRate}</div>
              <p className="text-xs text-slate-500 mt-1">Repeat rate</p>
            </CardContent>
          </Card>
        </div>

        <Separator className="my-8" />

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Earnings Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                💵 Earnings Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              {earningsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={earningsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="month" 
                      tickFormatter={(value) => {
                        const date = new Date(value + '-01');
                        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                      }}
                    />
                    <YAxis yAxisId="left" orientation="left" stroke="#22c55e" />
                    <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" />
                    <Tooltip 
                      labelFormatter={(value) => {
                        const date = new Date(value + '-01');
                        return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
                      }}
                    />
                    <Legend />
                    <Bar yAxisId="left" dataKey="earnings" fill="#22c55e" name="Earnings (£)" />
                    <Line yAxisId="right" type="monotone" dataKey="sessions" stroke="#3b82f6" name="Sessions" strokeWidth={3} />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex items-center justify-center text-slate-500">
                  No earnings data to display.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Mentee Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-600" />
                📊 Mentee Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              {statusDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <PieChart>
                    <Pie
                      data={statusDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      innerRadius={60}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex items-center justify-center text-slate-500">
                  No mentee connections found.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Separator className="my-8" />

        {/* Lists Section - Upcoming Sessions & Action Items */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Upcoming Sessions - Takes 2 columns */}
          <div className="lg:col-span-2">
            <h2 className="mb-4">📅 Upcoming Sessions</h2>
            <Card>
              <CardContent className="pt-6">
                {activeMentees.length > 0 ? (
                  <>
                    <Alert className="mb-4 bg-blue-50 border-blue-200">
                      <Calendar className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-900">
                        📅 Calendar integration is being finalized. Please coordinate via Message Center.
                      </AlertDescription>
                    </Alert>
                    
                    <div className="space-y-4">
                      {activeMentees.map((mentee) => (
                        <div key={mentee.link_id}>
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <p className="font-medium">👤 {mentee.anonymous_name}</p>
                              <p className="text-sm text-slate-500">ID: {mentee.link_id}</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                {mentee.status.charAt(0).toUpperCase() + mentee.status.slice(1)}
                              </Badge>
                              <Button size="sm" variant="outline">
                                View Progress
                                <ArrowRight className="h-3 w-3 ml-1" />
                              </Button>
                            </div>
                          </div>
                          {mentee.link_id !== activeMentees[activeMentees.length - 1].link_id && (
                            <Separator className="mt-4" />
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="text-center text-slate-500 py-12">
                    <Calendar className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                    <p>No active sessions scheduled.</p>
                    <p className="text-sm mt-1">Start mentoring to see your sessions here.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Action Items - Takes 1 column */}
          <div>
            <h2 className="mb-4">✅ Action Items</h2>
            <div className="space-y-4">
              {/* Pending Payout */}
              <Card className={actionItems.pendingPayout > 0 ? "bg-amber-50 border-amber-200" : "bg-green-50 border-green-200"}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <DollarSign className={`h-5 w-5 mt-1 ${actionItems.pendingPayout > 0 ? 'text-amber-600' : 'text-green-600'}`} />
                    <div className="flex-1">
                      <p className={`font-medium ${actionItems.pendingPayout > 0 ? 'text-amber-900' : 'text-green-900'}`}>
                        {actionItems.pendingPayout > 0 ? 'Pending Payout' : 'Payouts Up to Date'}
                      </p>
                      <p className={`text-sm mt-1 ${actionItems.pendingPayout > 0 ? 'text-amber-700' : 'text-green-700'}`}>
                        {actionItems.pendingPayout > 0 
                          ? `£${actionItems.pendingPayout.toLocaleString()} ready`
                          : '£0.00 pending'
                        }
                      </p>
                      {actionItems.pendingPayout > 0 && (
                        <Button size="sm" className="mt-3" variant="outline">
                          Go to Financials
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Pending Documents */}
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <FileText className="h-5 w-5 text-blue-600 mt-1" />
                    <div className="flex-1">
                      <p className="font-medium text-blue-900">Document Signatures</p>
                      <p className="text-sm text-blue-700 mt-1">
                        {actionItems.pendingDocuments > 0 
                          ? `${actionItems.pendingDocuments} pending`
                          : 'No pending signatures'
                        }
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* New Reviews */}
              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <Star className="h-5 w-5 text-purple-600 mt-1" />
                    <div className="flex-1">
                      <p className="font-medium text-purple-900">New Reviews</p>
                      <p className="text-sm text-purple-700 mt-1">
                        {actionItems.newReviews > 0 
                          ? `${actionItems.newReviews} to moderate`
                          : 'No new reviews'
                        }
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Footer */}
        <Separator className="my-8" />
        <div className="text-center text-sm text-slate-500 pb-8">
          <p>📊 IntelliCV Mentor Portal | Business Performance Overview</p>
        </div>
      </div>
    </div>
  );
}