import { SessionReview } from './SessionReviewForm';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';

interface SessionReviewListProps {
  reviews: SessionReview[];
}

export function SessionReviewList({ reviews }: SessionReviewListProps) {
  if (reviews.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          No session reviews yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>📜 Past Session Reviews</CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="space-y-2">
          {reviews.map((review) => (
            <AccordionItem key={review.id} value={review.id} className="border rounded-lg px-4">
              <AccordionTrigger>
                <div className="flex items-center gap-4 text-left">
                  <span>📝 {review.topic}</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(review.date).toLocaleDateString()}
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-4">
                  <div>
                    <p className="text-sm">
                      <strong>Date:</strong> {new Date(review.date).toLocaleDateString()}
                    </p>
                    <p className="text-sm">
                      <strong>Duration:</strong> {review.duration} mins
                    </p>
                  </div>

                  {review.summary && (
                    <div>
                      <h4>Summary:</h4>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {review.summary}
                      </p>
                    </div>
                  )}

                  {review.achievements && (
                    <div>
                      <h4>Achievements:</h4>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {review.achievements}
                      </p>
                    </div>
                  )}

                  {review.actionItems && (
                    <div>
                      <h4>Action Items:</h4>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {review.actionItems}
                      </p>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 pt-2">
                    {review.shared ? (
                      <Badge variant="default">✅ Shared with mentee</Badge>
                    ) : (
                      <Badge variant="secondary">🔒 Private note</Badge>
                    )}
                    
                    {review.confirmed ? (
                      <Badge variant="default">✓ Confirmed by mentee</Badge>
                    ) : (
                      <Badge variant="outline">⏳ Awaiting mentee confirmation</Badge>
                    )}

                    <Button variant="outline" size="sm">
                      📝 Edit
                    </Button>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
