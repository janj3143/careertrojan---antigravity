import { QAAssignment } from './QAAssignmentForm';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';

interface QAAssignmentListProps {
  assignments: QAAssignment[];
}

export function QAAssignmentList({ assignments }: QAAssignmentListProps) {
  if (assignments.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          🔄 No Q&A assignments sent yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>📬 Q&A Responses</CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="space-y-2">
          {assignments.map((assignment) => (
            <AccordionItem key={assignment.id} value={assignment.id} className="border rounded-lg px-4">
              <AccordionTrigger>
                <div className="flex items-center gap-4 text-left flex-wrap">
                  <span>📋 {assignment.title}</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(assignment.createdAt).toLocaleDateString()}
                  </span>
                  <Badge variant={assignment.status === 'completed' ? 'default' : 'secondary'}>
                    {assignment.status === 'completed' ? '✓ Completed' : '⏳ Pending'}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-4">
                  <div>
                    <p className="text-sm">
                      <strong>Due:</strong> {new Date(assignment.dueDate).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="space-y-3">
                    {assignment.questions.map((question, index) => (
                      <div key={index} className="border-l-2 border-primary pl-4">
                        <p className="text-sm">
                          <strong>{index + 1}. {question}</strong>
                        </p>
                        {assignment.responses && assignment.responses[index] ? (
                          <p className="text-sm text-muted-foreground mt-2 pl-4">
                            ↳ {assignment.responses[index]}
                          </p>
                        ) : (
                          <p className="text-sm text-muted-foreground mt-2 pl-4 italic">
                            Awaiting response...
                          </p>
                        )}
                      </div>
                    ))}
                  </div>

                  {assignment.status === 'pending' && (
                    <p className="text-sm text-muted-foreground italic">
                      💡 Mentee responses will appear here once submitted
                    </p>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
