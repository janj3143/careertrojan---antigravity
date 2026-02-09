import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface AddSessionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: any) => void;
}

export function AddSessionDialog({ open, onOpenChange, onSubmit }: AddSessionDialogProps) {
  const [formData, setFormData] = useState({
    mentee_name: '',
    package_name: '',
    date: '',
    time: '',
    duration_minutes: 60
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Combine date and time
    const startTime = new Date(`${formData.date}T${formData.time}`);

    onSubmit({
      mentee_name: formData.mentee_name,
      package_name: formData.package_name,
      start_time: startTime.toISOString(),
      duration_minutes: formData.duration_minutes
    });

    // Reset form
    setFormData({
      mentee_name: '',
      package_name: '',
      date: '',
      time: '',
      duration_minutes: 60
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>➕ Add Session</DialogTitle>
          <DialogDescription>
            Schedule a new mentoring session manually
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="mentee_name">Mentee Name *</Label>
            <Input
              id="mentee_name"
              type="text"
              placeholder="John Doe"
              value={formData.mentee_name}
              onChange={(e) => setFormData({ ...formData, mentee_name: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="package_name">Package Name *</Label>
            <Input
              id="package_name"
              type="text"
              placeholder="Career Development"
              value={formData.package_name}
              onChange={(e) => setFormData({ ...formData, package_name: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="date">Date *</Label>
              <Input
                id="date"
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
                min={new Date().toISOString().split('T')[0]}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="time">Start Time *</Label>
              <Input
                id="time"
                type="time"
                value={formData.time}
                onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="duration">Duration (minutes) *</Label>
            <Select
              value={formData.duration_minutes.toString()}
              onValueChange={(value) => setFormData({ ...formData, duration_minutes: parseInt(value) })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30">30 minutes</SelectItem>
                <SelectItem value="45">45 minutes</SelectItem>
                <SelectItem value="60">60 minutes</SelectItem>
                <SelectItem value="75">75 minutes</SelectItem>
                <SelectItem value="90">90 minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit">
              Add Session
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
