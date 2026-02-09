import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';

export interface Note {
  id: string;
  linkId: string;
  type: 'session' | 'qa_assignment' | 'observation' | 'progress';
  title: string;
  content: string;
  shared: boolean;
  createdAt: string;
}

interface NotesListProps {
  notes: Note[];
}

const noteIcons: Record<Note['type'], string> = {
  session: '📝',
  qa_assignment: '❓',
  observation: '🔍',
  progress: '📈',
};

export function NotesList({ notes }: NotesListProps) {
  if (notes.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          No notes yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>All Notes</CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="space-y-2">
          {notes.map((note) => (
            <AccordionItem key={note.id} value={note.id} className="border rounded-lg px-4">
              <AccordionTrigger>
                <div className="flex items-center gap-4 text-left flex-wrap">
                  <span>
                    {noteIcons[note.type]} {note.title}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(note.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-4">
                  <div className="whitespace-pre-wrap text-sm text-muted-foreground">
                    {note.content}
                  </div>

                  <div>
                    {note.shared ? (
                      <Badge variant="default">✅ Shared with mentee</Badge>
                    ) : (
                      <Badge variant="secondary">🔒 Private note</Badge>
                    )}
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
