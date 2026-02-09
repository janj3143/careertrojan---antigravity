import { useState, useMemo } from 'react';
import { Card, CardContent } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { SessionReviewForm, SessionReview } from './components/SessionReviewForm';
import { SessionReviewList } from './components/SessionReviewList';
import { QAAssignmentForm, QAAssignment } from './components/QAAssignmentForm';
import { QAAssignmentList } from './components/QAAssignmentList';
import { NotesList, Note } from './components/NotesList';
import { MessageSquare, FileQuestion, MessageCircle, FolderOpen, Upload, Info, AlertCircle } from 'lucide-react';
import { Toaster } from './components/ui/sonner';
import headerImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

// Interface for mentee connections - data would come from backend
interface Mentee {
  id: string;
  linkId: string;
  anonymousName: string;
  status: 'active' | 'inactive';
}

export default function App() {
  // In production, these would come from backend API
  // For now, starting with empty arrays - backend integration needed
  const [connections, setConnections] = useState<Mentee[]>([]);
  const [selectedMentee, setSelectedMentee] = useState<Mentee | null>(null);
  const [sessionReviews, setSessionReviews] = useState<SessionReview[]>([]);
  const [qaAssignments, setQAAssignments] = useState<QAAssignment[]>([]);

  // Filter data for selected mentee
  const filteredReviews = useMemo(
    () => selectedMentee ? sessionReviews.filter(r => r.linkId === selectedMentee.linkId) : [],
    [sessionReviews, selectedMentee]
  );

  const filteredAssignments = useMemo(
    () => selectedMentee ? qaAssignments.filter(a => a.linkId === selectedMentee.linkId) : [],
    [qaAssignments, selectedMentee]
  );

  const allNotes = useMemo(() => {
    if (!selectedMentee) return [];
    
    const notes: Note[] = [];
    
    // Convert session reviews to notes
    sessionReviews
      .filter(r => r.linkId === selectedMentee.linkId)
      .forEach(review => {
        notes.push({
          id: review.id,
          linkId: review.linkId,
          type: 'session',
          title: review.topic,
          content: `**Date:** ${new Date(review.date).toLocaleDateString()}
**Duration:** ${review.duration} mins

**Summary:**
${review.summary}

**Achievements:**
${review.achievements}

**Action Items:**
${review.actionItems}`,
          shared: review.shared,
          createdAt: review.createdAt,
        });
      });

    // Convert Q&A assignments to notes
    qaAssignments
      .filter(a => a.linkId === selectedMentee.linkId)
      .forEach(assignment => {
        const questionsText = assignment.questions
          .map((q, i) => `${i + 1}. ${q}`)
          .join('\n\n');
        
        notes.push({
          id: assignment.id,
          linkId: assignment.linkId,
          type: 'qa_assignment',
          title: assignment.title,
          content: `**Due:** ${new Date(assignment.dueDate).toLocaleDateString()}

${questionsText}`,
          shared: true,
          createdAt: assignment.createdAt,
        });
      });

    return notes.sort((a, b) => 
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [sessionReviews, qaAssignments, selectedMentee]);

  const handleSaveReview = (review: SessionReview) => {
    setSessionReviews([...sessionReviews, review]);
  };

  const handleSendAssignment = (assignment: QAAssignment) => {
    setQAAssignments([...qaAssignments, assignment]);
  };

  return (
    <div className="min-h-screen relative">
      {/* PNG Background */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url(${headerImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed',
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/60 to-black/70"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        <Toaster position="top-right" />
        
        {/* Header */}
        <div className="relative py-16 md:py-24">
          <div className="text-center text-white px-4">
            <h1 className="text-4xl md:text-6xl mb-3 drop-shadow-2xl">
              💬 Communication Center
            </h1>
            <p className="text-xl md:text-3xl drop-shadow-2xl">
              Mentor Portal
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <Alert className="mb-6 bg-blue-50/95 border-blue-200 backdrop-blur-sm">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-900">Enhanced Mentor-Mentee Communication</AlertTitle>
            <AlertDescription className="text-blue-800">
              <strong>Post-session workflow:</strong> 1) Share session notes • 2) Both parties review • 
              3) Optional homework/reflection • 4) Mentee responds • 5) Sign off on completion
            </AlertDescription>
          </Alert>

          <Separator className="mb-6 bg-white/20" />

          {/* Backend Status Check */}
          {connections.length === 0 && (
            <Alert className="mb-6 bg-amber-50/95 border-amber-200 backdrop-blur-sm">
              <AlertCircle className="h-4 w-4 text-amber-600" />
              <AlertTitle className="text-amber-900">⚠️ Backend Services Unavailable or Mentor ID Missing</AlertTitle>
              <AlertDescription className="text-amber-800">
                Cannot load communication center. Please ensure backend services are connected and you are logged in as a mentor.
              </AlertDescription>
            </Alert>
          )}

          {/* Mentee Selector */}
          {connections.length > 0 ? (
            <Card className="mb-6 bg-white/95 backdrop-blur-sm">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <label className="text-sm">Select Mentee</label>
                  <Select 
                    value={selectedMentee?.linkId || ''} 
                    onValueChange={(linkId) => {
                      const mentee = connections.find(m => m.linkId === linkId);
                      if (mentee) setSelectedMentee(mentee);
                    }}
                  >
                    <SelectTrigger className="w-full md:w-96">
                      <SelectValue placeholder="Select a mentee..." />
                    </SelectTrigger>
                    <SelectContent>
                      {connections.map(mentee => (
                        <SelectItem key={mentee.linkId} value={mentee.linkId}>
                          {mentee.anonymousName} ({mentee.linkId})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="mb-6 bg-white/95 backdrop-blur-sm">
              <CardContent className="py-12 text-center">
                <div className="text-muted-foreground">
                  <Info className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">No active mentees</p>
                  <p className="text-sm mt-2">Session reviews will appear once you have active mentorship connections.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Main Tabs - Only show if mentee is selected */}
          {selectedMentee && (
            <Tabs defaultValue="sessions" className="space-y-6">
              <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 h-auto bg-white/95 backdrop-blur-sm">
                <TabsTrigger value="sessions" className="flex items-center gap-2 py-3">
                  <MessageSquare className="h-4 w-4" />
                  <span className="hidden sm:inline">Session Reviews & Sign-offs</span>
                  <span className="sm:hidden">Sessions</span>
                </TabsTrigger>
                <TabsTrigger value="qa" className="flex items-center gap-2 py-3">
                  <FileQuestion className="h-4 w-4" />
                  <span className="hidden sm:inline">Q&A Assignments (Homework)</span>
                  <span className="sm:hidden">Q&A</span>
                </TabsTrigger>
                <TabsTrigger value="messages" className="flex items-center gap-2 py-3">
                  <MessageCircle className="h-4 w-4" />
                  <span className="hidden sm:inline">Messages & Notes</span>
                  <span className="sm:hidden">Messages</span>
                </TabsTrigger>
                <TabsTrigger value="files" className="flex items-center gap-2 py-3">
                  <FolderOpen className="h-4 w-4" />
                  <span className="hidden sm:inline">File Sharing</span>
                  <span className="sm:hidden">Files</span>
                </TabsTrigger>
              </TabsList>

              {/* Session Reviews & Sign-offs */}
              <TabsContent value="sessions" className="space-y-6">
                <div className="space-y-4">
                  <div className="bg-white/95 backdrop-blur-sm rounded-lg p-6">
                    <h2 className="text-3xl mb-2">📝 Post-Session Review & Agreement</h2>
                    <Alert className="bg-blue-50 border-blue-200">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-800">
                        <strong>Post-Session Workflow:</strong>
                        <ol className="list-decimal list-inside mt-2 space-y-1">
                          <li><strong>Share Session Notes</strong> with mentee (what was covered, action items)</li>
                          <li><strong>Both parties review</strong> and confirm "this is what happened"</li>
                          <li><strong>Optional:</strong> Add reflections or homework questions</li>
                          <li><strong>Sign off</strong> on session completion (triggers payment release)</li>
                        </ol>
                      </AlertDescription>
                    </Alert>
                  </div>

                  <SessionReviewForm
                    menteeName={selectedMentee.anonymousName}
                    linkId={selectedMentee.linkId}
                    onSave={handleSaveReview}
                  />

                  <Separator className="bg-white/20" />

                  <SessionReviewList reviews={filteredReviews} />
                </div>
              </TabsContent>

              {/* Q&A Assignments */}
              <TabsContent value="qa" className="space-y-6">
                <div className="space-y-4">
                  <div className="bg-white/95 backdrop-blur-sm rounded-lg p-6">
                    <h2 className="text-3xl mb-2">❓ Q&A Assignments & Reflections</h2>
                    <Alert className="bg-blue-50 border-blue-200">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-800">
                        <strong>Assign reflective questions or homework to mentees:</strong>
                        <ul className="list-disc list-inside mt-2 space-y-1">
                          <li>What did you learn from today's session?</li>
                          <li>What challenges did you face this week?</li>
                          <li>What are your goals for next session?</li>
                        </ul>
                        <p className="mt-2">Mentees respond directly, creating two-way communication.</p>
                      </AlertDescription>
                    </Alert>
                  </div>

                  <QAAssignmentForm
                    menteeName={selectedMentee.anonymousName}
                    linkId={selectedMentee.linkId}
                    onSend={handleSendAssignment}
                  />

                  <Separator className="bg-white/20" />

                  <QAAssignmentList assignments={filteredAssignments} />
                </div>
              </TabsContent>

              {/* Messages & Notes */}
              <TabsContent value="messages" className="space-y-6">
                <div className="space-y-4">
                  <div className="bg-white/95 backdrop-blur-sm rounded-lg p-6">
                    <h2 className="text-3xl mb-2">💬 Messages & Session Notes</h2>
                    <Alert className="bg-blue-50 border-blue-200">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-800">
                        💬 In-platform messaging will be added here. For now, use session notes and Q&A for communication.
                      </AlertDescription>
                    </Alert>
                  </div>

                  <NotesList notes={allNotes} />
                </div>
              </TabsContent>

              {/* File Sharing */}
              <TabsContent value="files" className="space-y-6">
                <div className="space-y-4">
                  <div className="bg-white/95 backdrop-blur-sm rounded-lg p-6">
                    <h2 className="text-3xl mb-2">📁 File Sharing</h2>
                    <Alert className="bg-blue-50 border-blue-200">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-800">
                        <strong>📎 File sharing capabilities coming soon:</strong>
                        <ul className="list-disc list-inside mt-2 space-y-1">
                          <li>Share documents, slides, resources with mentees</li>
                          <li>Receive homework/project submissions</li>
                          <li>Store session materials</li>
                        </ul>
                        <p className="mt-2">For now, use external file sharing services or embed links in session notes.</p>
                      </AlertDescription>
                    </Alert>
                  </div>

                  <Card className="bg-white/95 backdrop-blur-sm">
                    <CardContent className="py-8">
                      <div className="text-center space-y-4">
                        <div className="flex justify-center">
                          <Upload className="h-16 w-16 text-muted-foreground" />
                        </div>
                        <div>
                          <h3 className="text-xl mb-2">📤 Share Files</h3>
                          <p className="text-sm text-muted-foreground mb-4">
                            Upload documents, presentations, or resources to share with {selectedMentee.anonymousName}
                          </p>
                          <div className="inline-flex items-center justify-center px-6 py-4 border-2 border-dashed border-muted-foreground/25 rounded-lg">
                            <p className="text-sm text-muted-foreground">
                              File upload functionality will be implemented with cloud storage integration
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          )}

          {/* Footer */}
          <Separator className="my-8 bg-white/20" />
          <div className="text-center text-sm text-white/80 pb-8 drop-shadow-lg">
            <strong>💬 Communication Center</strong> | Session Reviews, Q&A & Messaging | IntelliCV Mentor Portal
          </div>
        </div>
      </div>
    </div>
  );
}