import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { Plus, Trash2 } from 'lucide-react';

interface QAAssignmentFormProps {
  menteeName: string;
  linkId: string;
  onSend: (assignment: QAAssignment) => void;
}

export interface QAAssignment {
  id: string;
  linkId: string;
  title: string;
  questions: string[];
  dueDate: string;
  responses?: string[];
  createdAt: string;
  status: 'pending' | 'completed';
}

export function QAAssignmentForm({ menteeName, linkId, onSend }: QAAssignmentFormProps) {
  const [title, setTitle] = useState('');
  const [questions, setQuestions] = useState(['']);
  const [dueDate, setDueDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() + 7);
    return date.toISOString().split('T')[0];
  });

  const addQuestion = () => {
    if (questions.length < 10) {
      setQuestions([...questions, '']);
    }
  };

  const removeQuestion = (index: number) => {
    if (questions.length > 1) {
      setQuestions(questions.filter((_, i) => i !== index));
    }
  };

  const updateQuestion = (index: number, value: string) => {
    const newQuestions = [...questions];
    newQuestions[index] = value;
    setQuestions(newQuestions);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error('Please provide an assignment title');
      return;
    }

    const validQuestions = questions.filter(q => q.trim());
    if (validQuestions.length === 0) {
      toast.error('Please provide at least one question');
      return;
    }

    const assignment: QAAssignment = {
      id: `qa-${Date.now()}`,
      linkId,
      title,
      questions: validQuestions,
      dueDate,
      createdAt: new Date().toISOString(),
      status: 'pending',
    };

    onSend(assignment);
    
    // Reset form
    setTitle('');
    setQuestions(['']);
    const date = new Date();
    date.setDate(date.getDate() + 7);
    setDueDate(date.toISOString().split('T')[0]);
    
    toast.success('✅ Q&A assignment sent!');
    toast.info('Mentee will be notified.');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Q&A Assignment</CardTitle>
        <CardDescription>Assign reflective questions to {menteeName}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h3 className="mb-4">📋 Assignment Details</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Assignment Title</Label>
                <Input
                  id="title"
                  placeholder="e.g., Week 2 Reflection"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dueDate">Due Date</Label>
                <Input
                  id="dueDate"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h3>❓ Questions</h3>
              {questions.length < 10 && (
                <Button type="button" variant="outline" size="sm" onClick={addQuestion}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Question
                </Button>
              )}
            </div>
            <div className="space-y-4">
              {questions.map((question, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={`question-${index}`}>Question {index + 1}</Label>
                    {questions.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeQuestion(index)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    )}
                  </div>
                  <Textarea
                    id={`question-${index}`}
                    placeholder="e.g., What was your biggest takeaway from our last session?"
                    rows={3}
                    value={question}
                    onChange={(e) => updateQuestion(index, e.target.value)}
                    className="resize-none"
                  />
                </div>
              ))}
            </div>
          </div>

          <Button type="submit" className="w-full md:w-auto">
            📤 Send Q&A to Mentee
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
