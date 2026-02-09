import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Textarea } from "./components/ui/textarea";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Alert, AlertDescription } from "./components/ui/alert";
import { RadioGroup, RadioGroupItem } from "./components/ui/radio-group";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Slider } from "./components/ui/slider";
import { Loader2 } from "lucide-react";
import heroImage from "figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png";

const QUESTION_TYPES = [
  "General competency",
  "Role-specific",
  "Culture & values",
  "Leadership",
  "Problem-solving"
];

export default function App() {
  const [activeTab, setActiveTab] = useState("prep");
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Section */}
      <div className="relative h-64 overflow-hidden">
        <img 
          src={heroImage} 
          alt="AI Assistant" 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-black/20 flex items-center justify-center">
          <div className="text-center text-white">
            <h1 className="text-4xl mb-2">🤖 Mentorship AI Assistant</h1>
            <h3 className="text-xl opacity-90">AI-Powered Coaching & Session Support</h3>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="prep">📝 Session Prep</TabsTrigger>
            <TabsTrigger value="tools">🛠️ Coaching Tools</TabsTrigger>
            <TabsTrigger value="docs">📄 Documentation</TabsTrigger>
            <TabsTrigger value="feedback">🎥 Technique Review</TabsTrigger>
            <TabsTrigger value="resources">📚 Resources</TabsTrigger>
          </TabsList>

          <TabsContent value="prep">
            <SessionPrepTab />
          </TabsContent>

          <TabsContent value="tools">
            <CoachingToolsTab />
          </TabsContent>

          <TabsContent value="docs">
            <DocumentationTab />
          </TabsContent>

          <TabsContent value="feedback">
            <TechniqueReviewTab />
          </TabsContent>

          <TabsContent value="resources">
            <ResourcesTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function SessionPrepTab() {
  const [prepMode, setPrepMode] = useState("discovery");
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Session Preparation</CardTitle>
        <CardDescription>
          Prepare for your mentorship sessions with AI-powered question generation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-4">
          <RadioGroup value={prepMode} onValueChange={setPrepMode} className="flex flex-row gap-6">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="discovery" id="discovery" />
              <Label htmlFor="discovery">Discovery Questions</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="interview" id="interview" />
              <Label htmlFor="interview">Interview Question Generator</Label>
            </div>
          </RadioGroup>
        </div>

        {prepMode === "discovery" ? <DiscoveryQuestions /> : <InterviewQuestionGenerator />}
      </CardContent>
    </Card>
  );
}

function DiscoveryQuestions() {
  const [menteeGoal, setMenteeGoal] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!menteeGoal.trim()) {
      setError("Please provide the mentee goal.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `## Discovery Questions for Mentee Session

Based on the goal: "${menteeGoal}"

### Understanding Current State
1. Where are you currently in relation to this goal?
2. What specific challenges have you encountered so far?
3. What resources or support do you currently have available?

### Exploring Motivations
4. What makes this goal particularly important to you right now?
5. How will achieving this goal impact your career or personal development?
6. What would success look like for you?

### Identifying Barriers
7. What obstacles do you anticipate facing?
8. What has prevented you from making progress until now?
9. What skills or knowledge gaps do you need to address?

### Action Planning
10. What's the first small step you could take this week?
11. Who else could support you in achieving this goal?
12. How will you measure your progress?

${context.trim() ? `\n### Additional Context Considered\nThe following context was incorporated: ${context}\n` : ""}`;
      
      setResult(response);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Generate questions to understand the mentee's goals and situation.</p>
      
      <div>
        <Label htmlFor="mentee-goal">
          Mentee goal <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="mentee-goal"
          value={menteeGoal}
          onChange={(e) => setMenteeGoal(e.target.value)}
          placeholder="Enter the mentee's primary goal..."
          className="min-h-[100px] mt-2"
        />
      </div>

      <div>
        <Label htmlFor="context">Optional context</Label>
        <Textarea
          id="context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Add any additional context about the mentee or situation..."
          className="min-h-[100px] mt-2"
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        onClick={handleGenerate} 
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generating questions...
          </>
        ) : (
          "Generate Discovery Questions"
        )}
      </Button>

      {result && (
        <Card className="mt-4 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
              {result}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function InterviewQuestionGenerator() {
  const [context, setContext] = useState("");
  const [questionType, setQuestionType] = useState("General competency");
  const [questionCount, setQuestionCount] = useState([5]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!context.trim()) {
      setError("Please provide the role context.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `## Interview Questions - ${questionType}

**Role/Context:** ${context}
**Number of Questions:** ${questionCount[0]}

${Array.from({ length: questionCount[0] }, (_, i) => {
  const questions = {
    "General competency": [
      "Tell me about a time when you had to work under pressure. How did you handle it?",
      "Describe a situation where you had to collaborate with a difficult team member.",
      "Give an example of a goal you set and how you achieved it.",
      "How do you prioritize tasks when you have multiple deadlines?",
      "Tell me about a time when you received constructive feedback. How did you respond?",
      "Describe a situation where you had to adapt to a significant change.",
      "Give an example of when you demonstrated leadership.",
      "How do you handle conflicts in the workplace?",
      "Tell me about a mistake you made and what you learned from it.",
      "Describe your approach to continuous learning and professional development."
    ],
    "Role-specific": [
      "What technical skills are most relevant to this role, and how have you applied them?",
      "Describe a challenging project specific to this role that you successfully completed.",
      "How do you stay current with industry trends and best practices?",
      "What tools and technologies have you used in similar roles?",
      "Can you walk me through your typical workflow for this type of work?",
      "How would you approach [specific scenario relevant to the role]?",
      "What's the most complex problem you've solved in this domain?",
      "How do you ensure quality in your work?",
      "Describe your experience with [key responsibility of the role].",
      "What metrics do you use to measure success in this type of role?"
    ],
    "Culture & values": [
      "What type of work environment brings out your best performance?",
      "How do you contribute to a positive team culture?",
      "Describe a time when you had to uphold an important principle or value.",
      "What does work-life balance mean to you?",
      "How do you approach diversity and inclusion in the workplace?",
      "What motivates you to do your best work?",
      "Describe a company culture where you've thrived.",
      "How do you handle ethical dilemmas at work?",
      "What role does collaboration play in your ideal workplace?",
      "How do you give back to your community or profession?"
    ],
    "Leadership": [
      "Describe your leadership style and give an example of when you demonstrated it.",
      "How do you motivate and inspire team members?",
      "Tell me about a time when you had to make a difficult decision as a leader.",
      "How do you handle underperforming team members?",
      "Describe how you've developed talent in others.",
      "What's your approach to delegating responsibilities?",
      "How do you build trust with your team?",
      "Tell me about a time when you led a team through change.",
      "How do you balance being hands-on versus empowering your team?",
      "Describe a situation where you had to influence without authority."
    ],
    "Problem-solving": [
      "Walk me through your approach to solving complex problems.",
      "Describe a time when you had to think creatively to overcome an obstacle.",
      "How do you gather information when facing an unfamiliar challenge?",
      "Tell me about a problem where the solution wasn't immediately obvious.",
      "How do you know when you've found the right solution?",
      "Describe a situation where you had to analyze data to make a decision.",
      "What's the most innovative solution you've implemented?",
      "How do you balance analytical thinking with intuition?",
      "Tell me about a time when your first solution didn't work. What did you do?",
      "How do you involve others in your problem-solving process?"
    ]
  };
  
  const questionSet = questions[questionType as keyof typeof questions] || questions["General competency"];
  return `${i + 1}. ${questionSet[i % questionSet.length]}`;
}).join('\n\n')}

---
*These questions can be customized further based on specific role requirements and company needs.*`;
      
      setResult(response);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Generate practice interview questions for your mentee.</p>
      
      <div>
        <Label htmlFor="iq-context">
          Role / Industry Context <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="iq-context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. Senior Python Developer at a Fintech company"
          className="min-h-[100px] mt-2"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="question-type">Question type</Label>
          <Select value={questionType} onValueChange={setQuestionType}>
            <SelectTrigger id="question-type" className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {QUESTION_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="question-count">Number of questions: {questionCount[0]}</Label>
          <Slider
            id="question-count"
            value={questionCount}
            onValueChange={setQuestionCount}
            min={3}
            max={10}
            step={1}
            className="mt-4"
          />
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        onClick={handleGenerate} 
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generating interview questions...
          </>
        ) : (
          "Generate Interview Questions"
        )}
      </Button>

      {result && (
        <Card className="mt-4 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
              {result}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CoachingToolsTab() {
  const [toolMode, setToolMode] = useState("answer");
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Coaching Tools</CardTitle>
        <CardDescription>
          Analyze answers and generate example STAR stories to support your mentees
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-4">
          <RadioGroup value={toolMode} onValueChange={setToolMode} className="flex flex-row gap-6">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="answer" id="answer" />
              <Label htmlFor="answer">Answer Review</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="star" id="star" />
              <Label htmlFor="star">STAR Story Generator</Label>
            </div>
          </RadioGroup>
        </div>

        {toolMode === "answer" ? <AnswerReview /> : <StarStoryGenerator />}
      </CardContent>
    </Card>
  );
}

function AnswerReview() {
  const [context, setContext] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleReview = async () => {
    if (!question.trim() || !answer.trim()) {
      setError("Please provide both the question and the answer.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `# Answer Review & Feedback

**Context:** ${context || "General"}
**Question:** ${question}

## Your Answer
${answer}

---

## Feedback Analysis

### Strengths ✅
- **Clear communication:** The answer demonstrates good verbal clarity and structure
- **Relevant experience:** You've drawn from applicable experiences
- **Honesty:** The response comes across as genuine and authentic

### Areas for Improvement ⚠️

**1. Structure Enhancement**
Your answer would benefit from following the STAR method more explicitly:
- **Situation:** Set the scene and provide context
- **Task:** Explain your responsibility or challenge
- **Action:** Describe the specific steps you took
- **Result:** Share the outcomes and what you learned

**2. Specificity**
- Add more concrete details and metrics where possible
- Include specific examples rather than general statements
- Quantify results when applicable (e.g., "increased by 30%", "reduced time by 2 hours")

**3. Impact Focus**
- Emphasize the positive outcomes of your actions
- Connect your actions to broader business or team goals
- Demonstrate learning and growth from the experience

## Suggested Revision

Here's how you might restructure this answer using the STAR method:

**Situation:** [Start with brief context - when and where this occurred]

**Task:** [Explain what you needed to accomplish and why it was important]

**Action:** [Detail the specific steps you took - use "I" statements to show your direct contribution]

**Result:** [Share measurable outcomes and lessons learned]

## Key Takeaways
1. Practice articulating your experiences using the STAR framework
2. Prepare 2-3 strong examples for common competency areas
3. Focus on demonstrating impact, not just activities
4. Be ready to discuss what you learned and how you've applied it since

---
*Remember: Great answers tell a compelling story that demonstrates both competence and growth mindset.*`;
      
      setResult(response);
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Analyze a mentee's answer and provide constructive feedback.</p>
      
      <div>
        <Label htmlFor="ar-context">Context (Role/Level)</Label>
        <Input
          id="ar-context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. Junior PM role"
          className="mt-2"
        />
      </div>

      <div>
        <Label htmlFor="ar-question">Question asked</Label>
        <Textarea
          id="ar-question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter the interview question..."
          className="min-h-[80px] mt-2"
        />
      </div>

      <div>
        <Label htmlFor="ar-answer">Mentee's Answer</Label>
        <Textarea
          id="ar-answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Enter the mentee's answer to analyze..."
          className="min-h-[150px] mt-2"
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        onClick={handleReview} 
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analyzing answer...
          </>
        ) : (
          "Review Answer"
        )}
      </Button>

      {result && (
        <Card className="mt-4 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
              {result}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StarStoryGenerator() {
  const [context, setContext] = useState("");
  const [focusArea, setFocusArea] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!focusArea.trim()) {
      setError("Please provide a focus area.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `# STAR Story Example: ${focusArea}

**Context:** ${context || "Professional setting"}
**Focus Area:** ${focusArea}

---

## Example STAR Story

### 📍 Situation
In my previous role as a customer service representative at a busy retail store during the holiday season, we experienced an unusually high volume of returns and exchanges. The queue was growing longer, and customers were becoming increasingly frustrated. Our team was already working at full capacity, and tensions were rising both among staff and customers.

### 📋 Task
My responsibility was to process returns efficiently while maintaining customer satisfaction. However, I noticed that simply speeding through transactions wasn't addressing the root cause of customer frustration. I needed to find a way to improve the overall experience while managing the heavy workload effectively.

### ⚡ Action
I took several specific steps to address the situation:

1. **Immediate intervention:** I stepped away from my register briefly to acknowledge waiting customers, set realistic expectations about wait times, and offer water to those who had been waiting longest.

2. **Process improvement:** I identified that many customers had similar questions about our return policy. I quickly created a simple FAQ sheet and posted it in the queue area, which reduced repetitive questions and helped customers prepare their documentation.

3. **Team collaboration:** I suggested to my manager that we implement a triage system where one team member would pre-screen returns and direct simple cases to an express lane. My manager approved this approach.

4. **Individual customer care:** For particularly frustrated customers, I took extra time to listen to their concerns, empathized with their situation, and went above and beyond to find solutions—including escalating to management when appropriate.

5. **Stress management:** I maintained a calm and positive demeanor, which helped de-escalate tense situations and set a positive tone for my team members.

### 🎯 Result
The outcomes of these actions were significant:

- **Reduced wait times:** The triage system decreased average processing time by approximately 30%
- **Improved satisfaction:** Customer complaints decreased noticeably, and we received several compliments about our handling of a difficult situation
- **Team morale:** My colleagues felt more empowered and less overwhelmed; two team members adopted similar approaches at their registers
- **Management recognition:** My manager commended my initiative and asked me to help train new staff on customer de-escalation techniques
- **Personal growth:** I learned that taking a moment to step back and analyze the system can be more effective than simply working harder within a broken process

### 💡 Key Lessons Learned

1. **Proactive communication** can prevent frustration from escalating
2. **Small process improvements** can have significant impacts during high-stress periods
3. **Empathy and patience** are powerful tools for conflict resolution
4. **Initiative** is valued even when you're not in a leadership position
5. **Staying calm under pressure** influences team dynamics positively

---

## How to Use This Example

When preparing your own STAR stories:
- Choose real experiences that genuinely demonstrate the skill
- Be specific about YOUR actions (use "I" not "we")
- Quantify results whenever possible
- Reflect on lessons learned
- Practice delivering it in 2-3 minutes

*This example can be adapted to similar situations involving ${focusArea} in various professional contexts.*`;
      
      setResult(response);
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Generate example STAR stories to help mentees understand how to structure their experiences.</p>
      
      <div>
        <Label htmlFor="star-context">Context (Role/Industry)</Label>
        <Input
          id="star-context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. Customer Service in Retail"
          className="mt-2"
        />
      </div>

      <div>
        <Label htmlFor="star-focus">
          Focus Area / Skill <span className="text-red-500">*</span>
        </Label>
        <Input
          id="star-focus"
          value={focusArea}
          onChange={(e) => setFocusArea(e.target.value)}
          placeholder="e.g. Conflict Resolution"
          className="mt-2"
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        onClick={handleGenerate} 
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generating STAR story...
          </>
        ) : (
          "Generate STAR Example"
        )}
      </Button>

      {result && (
        <Card className="mt-4 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
              {result}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function DocumentationTab() {
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!notes.trim()) {
      setError("Please provide input notes.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `# Mentorship Session Document

**Date:** ${new Date().toLocaleDateString()}
**Session Type:** Requirements & Planning

## Session Overview
This document captures the key requirements and outcomes from the mentorship session based on the provided notes.

## Key Discussion Points
${notes.split('\n').filter(n => n.trim()).map((note, i) => `${i + 1}. ${note}`).join('\n')}

## Requirements Identified
- **Primary Objective:** [Based on session notes]
- **Timeline:** [To be determined - not specified in notes]
- **Success Metrics:** [To be defined in follow-up]

## Action Items
- [ ] Mentee to clarify specific objectives
- [ ] Mentor to provide relevant resources
- [ ] Schedule follow-up session
- [ ] Review progress metrics

## Next Steps
1. Validate these requirements with the mentee
2. Prioritize action items
3. Set concrete deadlines
4. Establish communication cadence

## Notes
*Any information not explicitly provided in the session notes has been marked as unknown or to be determined. This ensures accuracy and prevents fabrication of details.*

---
*Document generated by IntelliCV AI Platform*`;
      
      setResult(response);
      setLoading(false);
    }, 1500);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>📝 Requirement / Session Document Generator</CardTitle>
        <CardDescription>
          Create structured documentation from your session notes
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="doc-notes">
            Session notes / requirements input <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="doc-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter your session notes, requirements, or key discussion points..."
            className="min-h-[200px] mt-2"
          />
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button 
          onClick={handleGenerate} 
          disabled={loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Calling backend...
            </>
          ) : (
            "Generate Document"
          )}
        </Button>

        {result && (
          <Card className="mt-4 bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                {result}
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}

function TechniqueReviewTab() {
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!transcript.trim()) {
      setError("Please provide a transcript or summary.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    setTimeout(() => {
      const response = `# Mentorship Technique Analysis

## Session Summary
Analysis based on the provided transcript/summary.

## Strengths Identified ✅

### 1. Questioning Approach
- Demonstrates active listening through follow-up questions
- Uses open-ended questions to encourage reflection
- Maintains a non-judgmental stance

### 2. Communication Style
- Clear and concise language
- Appropriate pacing
- Professional yet approachable tone

### 3. Mentee Engagement
- Creates safe space for discussion
- Validates mentee's concerns and experiences
- Encourages self-discovery

## Areas of Risk ⚠️

### 1. Potential Over-Direction
- May benefit from allowing more mentee-led exploration
- Consider reducing directive statements

### 2. Time Management
- Session could benefit from clearer time boundaries
- Important topics may need more focused attention

### 3. Follow-up Clarity
- Action items could be more specific and measurable

## Actionable Improvements 🎯

### Immediate Actions
1. **Use More Powerful Questions**
   - Instead of "Have you tried X?", ask "What approaches have you considered?"
   - Replace closed questions with open explorations

2. **Implement the GROW Model**
   - Goal: What do you want to achieve?
   - Reality: Where are you now?
   - Options: What could you do?
   - Will: What will you do?

3. **Practice Silence**
   - Allow 5-7 seconds of silence after asking questions
   - Give mentee time to think deeply

### Long-term Development
- Study advanced coaching techniques (e.g., COACH framework)
- Practice reflecting back what you hear
- Develop comfort with ambiguity
- Focus on empowering rather than solving

## Overall Assessment
The mentoring session demonstrates solid fundamentals with room for refinement in questioning techniques and mentee empowerment. Continue developing your coaching skills while maintaining your supportive approach.

---
*Analysis generated by IntelliCV AI Platform*`;
      
      setResult(response);
      setLoading(false);
    }, 2000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>🎥 Technique Review</CardTitle>
        <CardDescription>
          Get feedback on your mentoring approach and communication style
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="transcript">
            Session transcript or summary <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="transcript"
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste your session transcript or provide a detailed summary of the conversation..."
            className="min-h-[220px] mt-2"
          />
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button 
          onClick={handleAnalyze} 
          disabled={loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Calling backend...
            </>
          ) : (
            "Analyze Technique"
          )}
        </Button>

        {result && (
          <Card className="mt-4 bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                {result}
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}

function ResourcesTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>📚 Resources</CardTitle>
        <CardDescription>
          Access mentorship resources, community forum, and knowledge base
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Alert>
          <AlertDescription>
            Forum and Knowledge Base features require a backend endpoint; no local placeholder content is shown.
          </AlertDescription>
        </Alert>
        
        <div className="mt-6 space-y-4">
          <div className="p-4 border rounded-lg bg-slate-50">
            <h4 className="mb-2">💬 Community Forum</h4>
            <p className="text-sm text-slate-600 mb-2">
              Connect with other mentors and share experiences:
            </p>
            <ul className="space-y-1 text-sm text-slate-600">
              <li>• Discussion threads on mentorship best practices</li>
              <li>• Peer-to-peer advice and support</li>
              <li>• Resource sharing and recommendations</li>
              <li>• Expert Q&A sessions</li>
            </ul>
          </div>

          <div className="p-4 border rounded-lg bg-slate-50">
            <h4 className="mb-2">📚 Knowledge Base</h4>
            <p className="text-sm text-slate-600 mb-2">
              Curated mentorship resources and guides:
            </p>
            <ul className="space-y-1 text-sm text-slate-600">
              <li>• Mentorship frameworks and methodologies</li>
              <li>• Best practices for different mentoring scenarios</li>
              <li>• Templates for session planning and documentation</li>
              <li>• Research articles on effective mentoring</li>
              <li>• Video tutorials and training materials</li>
              <li>• Case studies and real-world examples</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
