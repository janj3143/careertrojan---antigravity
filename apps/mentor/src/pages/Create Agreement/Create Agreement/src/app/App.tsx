/**
 * 🤖 Mentorship AI Assistant | IntelliCV AI Platform
 * 
 * Backend-only mentor assistant.
 * 
 * Policy:
 * - No fabricated content.
 * - If backend chat is unavailable, the page stops with an explicit error.
 */

import { useState, useEffect } from 'react';
import { Alert, AlertDescription } from './components/ui/alert';
import { Button } from './components/ui/button';
import { Textarea } from './components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Loader, CircleAlert, Bot, Target, FileText, Video, MessageSquare, BookOpen } from 'lucide-react';
import { chatService, authService } from '../services';
import type { ChatMessage } from '../services';
import backgroundImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

function App() {
  const [isInitializing, setIsInitializing] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mentorId, setMentorId] = useState<string | null>(null);
  
  // Tab 1: Questions
  const [menteeGoal, setMenteeGoal] = useState('');
  const [context, setContext] = useState('');
  const [questionsResponse, setQuestionsResponse] = useState('');
  
  // Tab 2: Documents
  const [notes, setNotes] = useState('');
  const [documentResponse, setDocumentResponse] = useState('');
  
  // Tab 3: Technique Review
  const [transcript, setTranscript] = useState('');
  const [techniqueResponse, setTechniqueResponse] = useState('');

  /**
   * Initialize authentication and check backend availability
   */
  useEffect(() => {
    const initialize = async () => {
      try {
        // Initialize session
        await authService.initializeSession();
        
        // Check mentor authentication
        authService.requireMentorAuth();
        
        // Get mentor ID
        const id = authService.getMentorId();
        if (!id) {
          throw new Error('Mentor identity is not available in session (mentor_id missing).');
        }
        setMentorId(id);
        
        // Test chat service connection
        const isAvailable = await chatService.testConnection();
        if (!isAvailable) {
          console.warn('Backend not available, will use fallback if configured');
        }
        
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        
        if (errorMessage.includes('Backend chat bridge not available')) {
          setBackendError(errorMessage);
        } else {
          setAuthError(errorMessage);
        }
      } finally {
        setIsInitializing(false);
      }
    };

    initialize();
  }, []);

  /**
   * Call chat service with proper error handling
   */
  const callChat = async (
    prompt: string,
    systemPrompt: string = 'You are a mentorship assistant. Be precise and do not fabricate.'
  ): Promise<string> => {
    if (!mentorId) {
      throw new Error('Mentor ID not available');
    }

    const messages: ChatMessage[] = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt },
    ];

    try {
      const response = await chatService.sendChat({ messages }, mentorId);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chat service error';
      throw new Error(errorMessage);
    }
  };

  /**
   * Generate discovery questions
   */
  const handleGenerateQuestions = async () => {
    if (!menteeGoal.trim()) {
      setError('Please provide the mentee goal.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setQuestionsResponse('');

    try {
      const prompt = `Generate discovery questions for a mentor session. Mentee goal: ${menteeGoal.trim()}\n\nContext: ${context.trim()}`;
      const response = await callChat(
        prompt,
        'You generate mentorship discovery questions.'
      );
      setQuestionsResponse(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Generate mentorship document
   */
  const handleGenerateDocument = async () => {
    if (!notes.trim()) {
      setError('Please provide input notes.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setDocumentResponse('');

    try {
      const prompt = `Draft a mentorship requirement document from these notes. Do not invent facts; if something is missing, mark it as unknown.\n\nNOTES:\n${notes.trim()}`;
      const response = await callChat(
        prompt,
        'You produce structured mentorship documents.'
      );
      setDocumentResponse(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Analyze mentorship technique
   */
  const handleAnalyzeTechnique = async () => {
    if (!transcript.trim()) {
      setError('Please provide a transcript or summary.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setTechniqueResponse('');

    try {
      const prompt = `Analyze the mentor's questioning technique. Provide strengths, risks, and actionable improvements.\n\nTRANSCRIPT/SUMMARY:\n${transcript.trim()}`;
      const response = await callChat(
        prompt,
        'You critique coaching technique.'
      );
      setTechniqueResponse(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state during initialization
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Initializing Mentorship AI Assistant...</p>
        </div>
      </div>
    );
  }

  // Show backend error if chat service is unavailable
  if (backendError) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center relative"
        style={{ backgroundImage: `url(${backgroundImage})` }}
      >
        <div className="absolute inset-0 bg-black/50" />
        <Alert className="max-w-2xl relative z-10 bg-white/95 backdrop-blur">
          <CircleAlert className="h-4 w-4" />
          <AlertDescription>{backendError}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Show authentication error
  if (authError) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center relative"
        style={{ backgroundImage: `url(${backgroundImage})` }}
      >
        <div className="absolute inset-0 bg-black/50" />
        <Alert className="max-w-2xl relative z-10 bg-white/95 backdrop-blur">
          <CircleAlert className="h-4 w-4" />
          <AlertDescription>{authError}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen bg-cover bg-center relative"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      {/* Overlay for better readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/60" />
      
      {/* Content */}
      <div className="relative z-10 container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Bot className="h-8 w-8 text-blue-400" />
          <h1 className="text-3xl text-white drop-shadow-lg">🤖 Mentorship AI Assistant</h1>
        </div>

        {error && (
          <Alert className="mb-6 bg-red-50/95 border-red-200 backdrop-blur">
            <CircleAlert className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="questions" className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-white/90 backdrop-blur">
            <TabsTrigger value="questions" className="gap-2">
              <Target className="h-4 w-4" />
              🎯 Questions
            </TabsTrigger>
            <TabsTrigger value="documents" className="gap-2">
              <FileText className="h-4 w-4" />
              📝 Documents
            </TabsTrigger>
            <TabsTrigger value="technique" className="gap-2">
              <Video className="h-4 w-4" />
              🎥 Technique Review
            </TabsTrigger>
            <TabsTrigger value="forum" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              💬 Forum
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="gap-2">
              <BookOpen className="h-4 w-4" />
              📚 Knowledge Base
            </TabsTrigger>
          </TabsList>

          <TabsContent value="questions">
            <Card className="bg-white/95 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle>🎯 Discovery Question Generator</CardTitle>
                <CardDescription>
                  Generate powerful discovery questions tailored to your mentee's goals
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block mb-2">
                    Mentee goal <span className="text-red-500">*</span>
                  </label>
                  <Textarea
                    value={menteeGoal}
                    onChange={(e) => setMenteeGoal(e.target.value)}
                    placeholder="Enter the mentee's primary goal..."
                    className="min-h-[120px]"
                  />
                </div>
                <div>
                  <label className="block mb-2">Optional context</label>
                  <Textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="Add any additional context..."
                    className="min-h-[120px]"
                  />
                </div>
                <Button
                  onClick={handleGenerateQuestions}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader className="mr-2 h-4 w-4 animate-spin" />
                      Calling backend...
                    </>
                  ) : (
                    'Generate Questions'
                  )}
                </Button>
                {questionsResponse && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                      {questionsResponse}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents">
            <Card className="bg-white/95 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle>📝 Requirement / Session Document Generator</CardTitle>
                <CardDescription>
                  Transform session notes into structured mentorship documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block mb-2">
                    Session notes / requirements input <span className="text-red-500">*</span>
                  </label>
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Enter your session notes or requirements..."
                    className="min-h-[200px]"
                  />
                </div>
                <Button
                  onClick={handleGenerateDocument}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader className="mr-2 h-4 w-4 animate-spin" />
                      Calling backend...
                    </>
                  ) : (
                    'Generate Document'
                  )}
                </Button>
                {documentResponse && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                      {documentResponse}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="technique">
            <Card className="bg-white/95 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle>🎥 Technique Review</CardTitle>
                <CardDescription>
                  Get AI-powered feedback on your mentorship questioning techniques
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block mb-2">
                    Session transcript or summary <span className="text-red-500">*</span>
                  </label>
                  <Textarea
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    placeholder="Paste your session transcript or provide a summary..."
                    className="min-h-[220px]"
                  />
                </div>
                <Button
                  onClick={handleAnalyzeTechnique}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader className="mr-2 h-4 w-4 animate-spin" />
                      Calling backend...
                    </>
                  ) : (
                    'Analyze Technique'
                  )}
                </Button>
                {techniqueResponse && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                      {techniqueResponse}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="forum">
            <Card className="bg-white/95 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle>💬 Community Forum</CardTitle>
                <CardDescription>
                  Connect with other mentors and share experiences
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert className="bg-blue-50/95 border-blue-200">
                  <CircleAlert className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-800">
                    Forum features require a backend endpoint; no local placeholder content is shown.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="knowledge">
            <Card className="bg-white/95 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle>📚 Knowledge Base</CardTitle>
                <CardDescription>
                  Access curated mentorship resources and best practices
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert className="bg-blue-50/95 border-blue-200">
                  <CircleAlert className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-800">
                    Knowledge base retrieval requires a backend endpoint; no local placeholder content is shown.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;