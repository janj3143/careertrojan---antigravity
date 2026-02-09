import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { toast } from 'sonner';

interface SessionReviewFormProps {
  menteeName: string;
  linkId: string;
  onSave: (review: SessionReview) => void;
}

export interface SessionReview {
  id: string;
  linkId: string;
  date: string;
  duration: number;
  topic: string;
  summary: string;
  achievements: string;
  actionItems: string;
  shared: boolean;
  confirmed: boolean;
  createdAt: string;
}

export function SessionReviewForm({ menteeName, linkId, onSave }: SessionReviewFormProps) {
  const [sessionDate, setSessionDate] = useState(new Date().toISOString().split('T')[0]);
  const [duration, setDuration] = useState(60);
  const [topic, setTopic] = useState('');
  const [summary, setSummary] = useState('');
  const [achievements, setAchievements] = useState('');
  const [actionItems, setActionItems] = useState('');
  const [shareWithMentee, setShareWithMentee] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!summary.trim()) {
      toast.error('Please provide a session summary');
      return;
    }

    const review: SessionReview = {
      id: `review-${Date.now()}`,
      linkId,
      date: sessionDate,
      duration,
      topic: topic || 'General Session',
      summary,
      achievements,
      actionItems,
      shared: shareWithMentee,
      confirmed: false,
      createdAt: new Date().toISOString(),
    };

    onSave(review);
    
    // Reset form
    setTopic('');
    setSummary('');
    setAchievements('');
    setActionItems('');
    
    toast.success('✅ Session review saved!');
    toast.info('📧 Mentee will be notified to review and confirm.');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Session Review</CardTitle>
        <CardDescription>Document your session with {menteeName}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h3 className="mb-4">📋 Session Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sessionDate">Session Date</Label>
                <Input
                  id="sessionDate"
                  type="date"
                  value={sessionDate}
                  onChange={(e) => setSessionDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="duration">Duration (minutes)</Label>
                <Input
                  id="duration"
                  type="number"
                  min={15}
                  max={180}
                  step={15}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <Label htmlFor="topic">Session Topic</Label>
              <Input
                id="topic"
                placeholder="Enter a short topic for this session"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="mb-2">📝 Session Summary</h3>
            <Label htmlFor="summary">What was covered in this session?</Label>
            <Textarea
              id="summary"
              placeholder="Summarize what was covered and agreed in this session."
              rows={6}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="resize-none"
            />
          </div>

          <div>
            <h3 className="mb-4">🎯 Key Outcomes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="achievements">Mentee Achievements / Insights</Label>
                <Textarea
                  id="achievements"
                  placeholder="What did the mentee accomplish or learn?"
                  rows={4}
                  value={achievements}
                  onChange={(e) => setAchievements(e.target.value)}
                  className="resize-none"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="actionItems">Action Items for Mentee</Label>
                <Textarea
                  id="actionItems"
                  placeholder="What should the mentee do before next session?"
                  rows={4}
                  value={actionItems}
                  onChange={(e) => setActionItems(e.target.value)}
                  className="resize-none"
                />
              </div>
            </div>
          </div>

          <div>
            <h3 className="mb-4">✅ Share with Mentee</h3>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="shareWithMentee"
                checked={shareWithMentee}
                onCheckedChange={(checked) => setShareWithMentee(checked as boolean)}
              />
              <Label htmlFor="shareWithMentee" className="cursor-pointer">
                Share this session summary with mentee
              </Label>
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Mentee will see this and can confirm 'yes, this is what happened'
            </p>
          </div>

          <Button type="submit" className="w-full md:w-auto">
            💾 Save Session Review
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
