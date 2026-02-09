import guardianImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';
import { Shield, AlertTriangle, Star, Lock } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { useState } from 'react';

interface GuardianFeedback {
  id: string;
  link_id: string;
  mentee_name: string;
  program_id?: string;
  rating: number;
  date: string;
  comments: string;
}

export default function App() {
  // Simulating role check - in real app, this would come from authentication
  const userRole = 'mentor'; // Change to 'student' to see access denied
  const mentorId = 'mentor_123'; // In real app, would come from session

  // Backend connection status - simulated
  const [backendAvailable] = useState(true);
  const [connectionError] = useState<string | null>(null);

  // Mock backend data - in real app, this would be fetched from MentorshipService
  const [guardianFeedback] = useState<GuardianFeedback[]>([
    // Example data - uncomment to test with data
    // {
    //   id: '1',
    //   link_id: 'AGR-2024-XY789',
    //   mentee_name: 'Sarah Johnson',
    //   program_id: 'PROG-2024-001',
    //   rating: 5,
    //   date: '2024-12-15T10:30:00',
    //   comments: 'Excellent mentor! Very knowledgeable and patient. The mentee has shown significant improvement in technical skills and confidence.'
    // },
    // {
    //   id: '2',
    //   link_id: 'AGR-2024-AB456',
    //   mentee_name: 'Michael Chen',
    //   program_id: 'PROG-2024-002',
    //   rating: 4,
    //   date: '2024-12-10T14:20:00',
    //   comments: 'Great sessions with clear explanations. Would appreciate more focus on practical examples.'
    // },
    // {
    //   id: '3',
    //   link_id: 'AGR-2024-CD123',
    //   mentee_name: 'Emily Williams',
    //   rating: 5,
    //   date: '2024-12-08T09:15:00',
    //   comments: 'Outstanding guidance throughout the mentorship journey. The structured approach and personalized feedback helped me achieve my career goals.'
    // }
  ]);

  // Calculate metrics
  const totalReviews = guardianFeedback.length;
  const averageRating = totalReviews > 0 
    ? guardianFeedback.reduce((sum, fb) => sum + fb.rating, 0) / totalReviews 
    : 0;

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`size-5 ${
          i < rating 
            ? 'fill-yellow-400 text-yellow-400' 
            : 'fill-slate-200 text-slate-200'
        }`}
      />
    ));
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="min-h-screen relative">
      {/* Fixed Background - Exact copy of PNG structure */}
      <div className="fixed inset-0 -z-10">
        {/* Top dark section - 21.5% of viewport */}
        <div className="h-[21.5vh] bg-[#2a2a2a]" />
        
        {/* Middle section with image - 57% of viewport */}
        <div className="h-[57vh]">
          <img 
            src={guardianImage}
            alt="Professional with technology"
            className="w-full h-full object-cover"
          />
        </div>
        
        {/* Bottom dark section - remaining space */}
        <div className="flex-1 bg-[#2a2a2a] min-h-[21.5vh]" />
      </div>
      
      {/* Scrollable Content */}
      <div className="relative">
        {/* Header */}
        <header className="bg-white/95 backdrop-blur-sm border-b border-slate-200 shadow-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center gap-3">
              <Shield className="size-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-semibold text-slate-900">🛡 Guardian Feedback</h1>
                <p className="text-sm text-slate-600">Mentor Portal</p>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Access Control Check */}
          {userRole !== 'mentor' ? (
            <Alert variant="destructive" className="mb-6 bg-white/95 backdrop-blur-sm">
              <AlertTriangle />
              <AlertTitle>Access Denied</AlertTitle>
              <AlertDescription>
                🚫 Mentor access only
              </AlertDescription>
            </Alert>
          ) : !mentorId ? (
            <Alert variant="destructive" className="mb-6 bg-white/95 backdrop-blur-sm">
              <AlertTriangle />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Mentor identity missing from session.
              </AlertDescription>
            </Alert>
          ) : !backendAvailable ? (
            <Alert variant="destructive" className="mb-6 bg-white/95 backdrop-blur-sm">
              <AlertTriangle />
              <AlertTitle>Backend Connection Error</AlertTitle>
              <AlertDescription>
                {connectionError || 'Backend services not available. Please contact support.'}
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {/* Page Description */}
              <Card className="mb-6 bg-white/95 backdrop-blur-sm">
                <CardContent className="pt-6">
                  <p className="text-slate-700">
                    Review feedback provided by guardians regarding your mentorship sessions.
                  </p>
                </CardContent>
              </Card>

              {/* Summary Metrics */}
              {totalReviews > 0 && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <Card className="bg-white/95 backdrop-blur-sm">
                      <CardHeader>
                        <CardDescription>Total Reviews</CardDescription>
                        <CardTitle className="text-3xl">{totalReviews}</CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-white/95 backdrop-blur-sm">
                      <CardHeader>
                        <CardDescription>Average Rating</CardDescription>
                        <CardTitle className="text-3xl">{averageRating.toFixed(1)} / 5.0</CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-white/95 backdrop-blur-sm">
                      <CardHeader>
                        <CardDescription>Backend Status</CardDescription>
                        <CardTitle className="text-sm text-green-600">✓ Connected</CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  <hr className="border-slate-200/50 mb-8" />
                </>
              )}

              {/* Feedback List */}
              {guardianFeedback.length === 0 ? (
                <Card className="bg-white/95 backdrop-blur-sm">
                  <CardContent className="pt-6">
                    <div className="text-center py-12">
                      <Shield className="size-16 text-slate-300 mx-auto mb-4" />
                      <h3 className="font-medium text-slate-900 mb-2">No Guardian Feedback Yet</h3>
                      <p className="text-slate-600 text-sm">
                        No guardian feedback received yet.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <>
                  {/* Privacy Protocol Notice */}
                  <div className="mb-6 bg-green-50/95 backdrop-blur-sm border border-green-300 rounded-lg p-4 shadow-sm">
                    <p className="text-green-800 flex items-start gap-2">
                      <Lock className="size-5 mt-0.5 shrink-0" />
                      <span>
                        <strong>Privacy Protocol Active:</strong> Feedback is strictly confidential and visible ONLY to the two parties in the agreement.
                      </span>
                    </p>
                  </div>

                  <div className="space-y-6">
                    {guardianFeedback.map((fb) => (
                      <Card key={fb.id} className="bg-white/95 backdrop-blur-sm shadow-lg">
                        <CardContent className="pt-6">
                          <div className="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-6">
                            {/* Left Column - Rating and Date */}
                            <div className="space-y-3">
                              <div className="flex gap-1">
                                {renderStars(fb.rating)}
                              </div>
                              <p className="text-sm text-slate-500">
                                Date: {formatDate(fb.date)}
                              </p>
                            </div>

                            {/* Right Column - Feedback Details */}
                            <div className="space-y-4">
                              <div>
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                  Agreement Ref: <code className="bg-slate-100 px-2 py-1 rounded text-sm font-mono">{fb.link_id}</code>
                                </h3>
                                <p className="font-medium text-slate-900">
                                  Mentee: {fb.mentee_name}
                                </p>
                                {fb.program_id && (
                                  <p className="text-sm text-slate-500 mt-1">
                                    Program: {fb.program_id}
                                  </p>
                                )}
                              </div>

                              <div>
                                <h4 className="font-semibold text-slate-900 mb-2">Feedback</h4>
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                  <p className="text-slate-700 leading-relaxed">{fb.comments}</p>
                                </div>
                              </div>

                              <div className="text-sm text-slate-600 flex items-start gap-2 pt-2 border-t border-slate-200">
                                <Lock className="size-4 mt-0.5 shrink-0" />
                                <span className="italic">
                                  <strong>Private Channel:</strong> Visible only to you and {fb.mentee_name}.
                                </span>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </>
              )}

              {/* Footer */}
              <div className="mt-8 text-center">
                <p className="text-sm text-slate-500">Backend-integrated page</p>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
