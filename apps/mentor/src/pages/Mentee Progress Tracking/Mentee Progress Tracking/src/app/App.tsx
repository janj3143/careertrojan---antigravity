import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import { Alert, AlertDescription } from './components/ui/alert';
import { Progress } from './components/ui/progress';
import { Textarea } from './components/ui/textarea';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './components/ui/accordion';
import { Separator } from './components/ui/separator';
import { 
  FileText, 
  TrendingUp, 
  HelpCircle, 
  MessageSquare, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  Shield,
  Send,
  Plus,
  Target,
  Calendar
} from 'lucide-react';
import heroImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

const hiringFeeAgreement = `## Mentor ↔ Mentee Services Agreement (Hiring / Engagement Fee)

### 1) Purpose
This agreement supplements the mentorship requirement document. It governs the scenario where, during or after a mentorship relationship, a mentee becomes employed by (or otherwise engaged by) the mentor's company, or a company connected to the mentor.

### 2) Key definitions
- **Annual Package / Annual Remuneration**: Basic salary plus bonuses/commission and any taxable allowances or benefits-in-kind connected to the engagement, calculated over 12 months.
- **Engagement / Hire**: Any employment, contract-for-services, consultancy, internship-to-perm conversion, secondment, or other paid engagement, whether direct or indirect.
- **Connected Company**: Any company connected to the mentor (e.g., group company, subsidiary/parent, or where the mentor has a role with hiring influence).

### 3) Trigger event
If the mentee is hired/engaged by the mentor's company (or a connected company) **within 12 months** of the last mentorship session or the last documented mentorship interaction (whichever is later), the Hiring Fee becomes payable.

### 4) Hiring fee
- **Hiring Fee**: **5% of the Annual Package**.
- The fee becomes due when the mentee accepts an offer (written acceptance or equivalent evidence).

### 5) Charity distribution
The Hiring Fee is distributed as follows:
- **25%** to a charity chosen by the mentee
- **25%** to a charity chosen by the mentor
- **25%** to a charity chosen by the platform (IntelliCV)
- **25%** retained by IntelliCV to support administration costs and future development

### 6) Notification and evidence
Both parties agree to notify IntelliCV promptly if a Trigger Event occurs. IntelliCV may request reasonable evidence to calculate the Annual Package and confirm the Trigger Event.

### 7) Confidentiality
Both parties agree to keep non-public information and mentorship materials confidential, except where disclosure is required to administer this agreement, comply with law, or resolve disputes.

### 8) Governing law
This agreement is governed by the law of England and Wales.

### 9) Note
This text is provided for operational clarity and is not legal advice.`;

export default function App() {
  const [userRole] = useState<'mentee' | 'mentor'>('mentee');
  const linkId = 'LINK_2024_001';
  const mentorshipName = 'Career Transition Mentorship';
  
  const [goalInput, setGoalInput] = useState('');
  const [currentExperience, setCurrentExperience] = useState('');
  const [successMetrics, setSuccessMetrics] = useState('');
  const [message, setMessage] = useState('');
  const [menteeCharity, setMenteeCharity] = useState('');
  const [mentorCharity, setMentorCharity] = useState('');
  const [signatureName, setSignatureName] = useState('');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Section */}
      <div className="relative h-[300px] overflow-hidden">
        <div className="absolute inset-0">
          <img 
            src={heroImage} 
            alt="Mentorship Technology" 
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative container mx-auto px-6 py-12 h-full flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-10 h-10 text-white" />
            <h1 className="text-white">My Mentorship: Agreements & Progress</h1>
          </div>
          <p className="text-white/90 text-lg max-w-2xl">
            Track your mentorship journey, complete assignments, and stay aligned with your mentor
          </p>
          {userRole === 'mentor' && (
            <Alert className="mt-4 max-w-2xl bg-white/10 border-white/30 text-white">
              <AlertDescription>
                👁️ <strong>Mentor View:</strong> You're viewing this as a mentor. Mentees see a similar interface.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Mentorship Selection */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Active Mentorship</CardTitle>
                <CardDescription>
                  Link ID: {linkId} | Privacy-protected mentorship system
                </CardDescription>
              </div>
              <Badge variant="default" className="bg-green-500">Active</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Mentorship Program</p>
                <p>{mentorshipName}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant="outline" className="text-green-600 border-green-600">
                  ✓ Active
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs defaultValue="requirements" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 h-auto">
            <TabsTrigger value="requirements" className="flex items-center gap-2 py-3">
              <FileText className="w-4 h-4" />
              <span className="hidden sm:inline">Requirements</span>
            </TabsTrigger>
            <TabsTrigger value="progress" className="flex items-center gap-2 py-3">
              <TrendingUp className="w-4 h-4" />
              <span className="hidden sm:inline">Progress</span>
            </TabsTrigger>
            <TabsTrigger value="assignments" className="flex items-center gap-2 py-3">
              <HelpCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Assignments</span>
            </TabsTrigger>
            <TabsTrigger value="communication" className="flex items-center gap-2 py-3">
              <MessageSquare className="w-4 h-4" />
              <span className="hidden sm:inline">Communication</span>
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: REQUIREMENTS & AGREEMENT */}
          <TabsContent value="requirements" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>📄 Mentorship Requirement Document</CardTitle>
                <CardDescription>
                  Define your goals, review mentor's delivery plan, and formalize your agreement
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <Alert>
                  <AlertDescription>
                    <strong>How this works:</strong>
                    <ol className="mt-2 ml-4 space-y-1 list-decimal">
                      <li><strong>You define your goals</strong> - What do you want to achieve?</li>
                      <li><strong>Mentor creates delivery plan</strong> - What they will help you with</li>
                      <li><strong>Both sign off</strong> - Agreement is finalized</li>
                      <li><strong>Guardian oversight</strong> - Admin can review if any issues arise</li>
                    </ol>
                  </AlertDescription>
                </Alert>

                <Separator />

                {/* Step 1: Define Goals */}
                <Accordion type="single" collapsible defaultValue="goals">
                  <AccordionItem value="goals">
                    <AccordionTrigger>
                      <div className="flex items-center gap-2">
                        <Target className="w-5 h-5" />
                        <span>✏️ Step 1: Define Your Goals</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4 pt-4">
                      <div>
                        <Label htmlFor="goal">🎯 Your Primary Goal</Label>
                        <Textarea
                          id="goal"
                          placeholder="Describe a specific goal you want to achieve."
                          value={goalInput}
                          onChange={(e) => setGoalInput(e.target.value)}
                          className="mt-2"
                          rows={4}
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                          Be specific! This helps your mentor create a focused plan.
                        </p>
                      </div>

                      <div>
                        <Label htmlFor="experience">📊 Current State</Label>
                        <Textarea
                          id="experience"
                          placeholder="Summarize your experience, strengths, and current gaps."
                          value={currentExperience}
                          onChange={(e) => setCurrentExperience(e.target.value)}
                          className="mt-2"
                          rows={4}
                        />
                      </div>

                      <div>
                        <Label htmlFor="metrics">✅ Success Metrics</Label>
                        <Textarea
                          id="metrics"
                          placeholder="List measurable outcomes (projects, promotions, portfolio, skills)."
                          value={successMetrics}
                          onChange={(e) => setSuccessMetrics(e.target.value)}
                          className="mt-2"
                          rows={4}
                        />
                      </div>

                      <Button className="w-full sm:w-auto">
                        💾 Save My Goals
                      </Button>
                    </AccordionContent>
                  </AccordionItem>

                  {/* Step 2: Review Mentor's Plan */}
                  <AccordionItem value="review">
                    <AccordionTrigger>
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        <span>👁️ Step 2: Review Mentor's Delivery Plan</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4 pt-4">
                      <Alert>
                        <Clock className="h-4 w-4" />
                        <AlertDescription>
                          ⏳ Waiting for mentor to create a requirement document...
                        </AlertDescription>
                      </Alert>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                <Separator />

                {/* Guardian Oversight */}
                <Alert className="bg-blue-50 border-blue-200">
                  <Shield className="h-4 w-4 text-blue-600" />
                  <AlertDescription>
                    <strong>🛡️ Guardian Oversight</strong>
                    <p className="mt-2 text-sm">
                      This agreement is stored in the admin portal. If any disputes arise during your mentorship,
                      guardians can review this signed document to help resolve issues fairly.
                    </p>
                  </AlertDescription>
                </Alert>

                <Separator />

                {/* Hiring Fee Agreement */}
                <div className="space-y-4">
                  <h3 className="flex items-center gap-2">
                    🧾 Hiring / Engagement Fee Agreement
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Explicit agreement for mentorship → employment outcomes. 
                    If a Trigger Event occurs, a fee equal to 5% of the Annual Package is payable and distributed to charities/admin as defined below.
                  </p>

                  <Accordion type="single" collapsible>
                    <AccordionItem value="hiring-agreement">
                      <AccordionTrigger>📄 View Agreement Text</AccordionTrigger>
                      <AccordionContent>
                        <div className="prose prose-sm max-w-none p-4 bg-slate-50 rounded-lg">
                          <pre className="whitespace-pre-wrap font-sans text-sm">
                            {hiringFeeAgreement}
                          </pre>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Agreement Status</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Alert>
                          <AlertDescription>
                            Agreement record not created yet. Mentor must create the agreement first.
                          </AlertDescription>
                        </Alert>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Sign Agreement</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <Label htmlFor="mentee-charity">Mentee charity choice</Label>
                          <Input
                            id="mentee-charity"
                            placeholder="Name or registration number"
                            value={menteeCharity}
                            onChange={(e) => setMenteeCharity(e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <Label htmlFor="mentor-charity">Mentor charity choice</Label>
                          <Input
                            id="mentor-charity"
                            placeholder="Name or registration number"
                            value={mentorCharity}
                            onChange={(e) => setMentorCharity(e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <Label htmlFor="signature">Type your full legal name to sign</Label>
                          <Input
                            id="signature"
                            placeholder="Full name"
                            value={signatureName}
                            onChange={(e) => setSignatureName(e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        <Button className="w-full" disabled>
                          Sign Hiring Fee Agreement
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          Agreement record must be created first
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 2: PROGRESS & MILESTONES */}
          <TabsContent value="progress" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  📈 Progress Tracking & Milestones
                </CardTitle>
                <CardDescription>
                  Track your progress toward your mentorship goals
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Overall Progress */}
                <div className="p-6 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg space-y-4">
                  <h3>📊 Overall Progress</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <p className="text-sm text-muted-foreground">Completed</p>
                      <p className="text-2xl">0/0</p>
                      <p className="text-xs text-muted-foreground">milestones</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <p className="text-sm text-muted-foreground">In Progress</p>
                      <p className="text-2xl">0</p>
                      <p className="text-xs text-muted-foreground">active tasks</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <p className="text-sm text-muted-foreground">Overall Progress</p>
                      <p className="text-2xl">0%</p>
                      <Progress value={0} className="mt-2" />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Milestones List */}
                <div className="space-y-4">
                  <h3 className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    🎯 Current Milestones
                  </h3>
                  
                  <Alert>
                    <AlertDescription>No milestones available yet.</AlertDescription>
                  </Alert>
                </div>

                <Separator />

                {/* Add Milestone */}
                <Card className="border-dashed">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-3">
                      <Plus className="w-8 h-8 mx-auto text-muted-foreground" />
                      <h4 className="text-muted-foreground">➕ Add New Milestone</h4>
                      <p className="text-sm text-muted-foreground">
                        Milestone creation requires backend integration.
                      </p>
                      <Button variant="outline">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Milestone
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 3: ASSIGNMENTS & Q&A */}
          <TabsContent value="assignments" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HelpCircle className="w-5 h-5" />
                  ❓ Assignments & Reflections
                </CardTitle>
                <CardDescription>
                  Complete assignments and reflection questions from your mentor
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Pending Assignments */}
                <div className="space-y-4">
                  <h3>📝 Pending Assignments</h3>
                  
                  <Alert>
                    <AlertDescription>No assignments available.</AlertDescription>
                  </Alert>
                </div>

                <Separator />

                {/* Completed Assignments */}
                <div className="space-y-4">
                  <h3>✅ Completed Assignments</h3>
                  <Alert>
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertDescription>No completed assignments yet</AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 4: COMMUNICATION */}
          <TabsContent value="communication" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  💬 Communication with Mentor
                </CardTitle>
                <CardDescription>
                  Session notes and messages with your mentor
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Session Notes */}
                <div className="space-y-4">
                  <h3>📝 Session Notes from Mentor</h3>
                  
                  <Alert>
                    <AlertDescription>No session notes available.</AlertDescription>
                  </Alert>
                </div>

                <Separator />

                {/* Send Message */}
                <div className="space-y-4">
                  <h3>📨 Send Message to Mentor</h3>
                  <Card>
                    <CardContent className="pt-6 space-y-4">
                      <div>
                        <Label htmlFor="message">Message</Label>
                        <Textarea
                          id="message"
                          placeholder="Ask a question or share an update..."
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          rows={6}
                          className="mt-2"
                        />
                      </div>
                      <Button className="w-full sm:w-auto">
                        <Send className="w-4 h-4 mr-2" />
                        📤 Send Message
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer - Help & Support */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              🛡️ Need Help?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Alert className="bg-blue-50 border-blue-200">
                <AlertDescription>
                  <strong>If you have concerns about your mentorship:</strong>
                  <ul className="mt-2 ml-4 space-y-1 list-disc text-sm">
                    <li>Disagreement about requirements</li>
                    <li>Session completion disputes</li>
                    <li>Payment issues</li>
                  </ul>
                  <p className="mt-3 text-sm">
                    Contact guardian support - they have access to all signed agreements and session records.
                  </p>
                </AlertDescription>
              </Alert>
              
              <div className="flex items-center justify-center">
                <Button variant="outline" className="w-full" size="lg">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  🚨 Report Issue to Guardian
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer Info */}
        <div className="mt-8 text-center space-y-2 text-sm text-muted-foreground">
          <p>
            <strong>📋 Mentee Dashboard</strong> | Agreements, Progress & Communication | IntelliCV Mentor Portal
          </p>
          <p>Link ID: {linkId} | Privacy-protected mentorship system</p>
        </div>
      </div>
    </div>
  );
}
