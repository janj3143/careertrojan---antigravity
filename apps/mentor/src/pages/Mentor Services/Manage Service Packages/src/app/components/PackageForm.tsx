import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import { ServicePackage } from '../App';

interface PackageFormProps {
  onAddPackage: (pkg: Omit<ServicePackage, 'id' | 'total_package_price' | 'guardian_assessed'>) => void;
}

export function PackageForm({ onAddPackage }: PackageFormProps) {
  const [packageName, setPackageName] = useState('');
  const [description, setDescription] = useState('');
  const [sessionCount, setSessionCount] = useState(4);
  const [sessionDuration, setSessionDuration] = useState('60');
  const [pricePerSession, setPricePerSession] = useState(150);
  const [deliverables, setDeliverables] = useState('');
  const [expectedOutcomes, setExpectedOutcomes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!packageName || !description) {
      toast.error('Please fill in all required fields');
      return;
    }

    const deliverablesArray = deliverables
      .split(',')
      .map(d => d.trim())
      .filter(d => d.length > 0);

    onAddPackage({
      package_name: packageName,
      description,
      session_count: sessionCount,
      session_duration: parseInt(sessionDuration),
      price_per_session: pricePerSession,
      deliverables: deliverablesArray,
      expected_outcomes: expectedOutcomes,
      is_active: true,
    });

    // Reset form
    setPackageName('');
    setDescription('');
    setSessionCount(4);
    setSessionDuration('60');
    setPricePerSession(150);
    setDeliverables('');
    setExpectedOutcomes('');
    
    toast.success('Package added successfully!');
  };

  return (
    <Card className="bg-gray-900/80 backdrop-blur-md border-cyan-500/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Plus className="w-5 h-5 text-cyan-400" />
          Create New Package
        </CardTitle>
        <CardDescription className="text-gray-400">
          Define a new service offering for your mentees
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="packageName" className="text-gray-200">
                Package Name*
              </Label>
              <Input
                id="packageName"
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                placeholder="e.g., Leadership Accelerator"
                className="bg-gray-800/50 border-gray-600 text-white placeholder:text-gray-500"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="sessionCount" className="text-gray-200">
                Number of Sessions*
              </Label>
              <Input
                id="sessionCount"
                type="number"
                min="1"
                max="50"
                value={sessionCount}
                onChange={(e) => setSessionCount(parseInt(e.target.value))}
                className="bg-gray-800/50 border-gray-600 text-white"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description" className="text-gray-200">
              Description*
            </Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe who it's for, structure, transformation outcomes..."
              rows={4}
              className="bg-gray-800/50 border-gray-600 text-white placeholder:text-gray-500 resize-none"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sessionDuration" className="text-gray-200">
                Session Duration (minutes)*
              </Label>
              <Select value={sessionDuration} onValueChange={setSessionDuration}>
                <SelectTrigger className="bg-gray-800/50 border-gray-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-600">
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="45">45 minutes</SelectItem>
                  <SelectItem value="60">60 minutes</SelectItem>
                  <SelectItem value="75">75 minutes</SelectItem>
                  <SelectItem value="90">90 minutes</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pricePerSession" className="text-gray-200">
                Price per Session (£)*
              </Label>
              <Input
                id="pricePerSession"
                type="number"
                min="50"
                max="500"
                step="5"
                value={pricePerSession}
                onChange={(e) => setPricePerSession(parseFloat(e.target.value))}
                className="bg-gray-800/50 border-gray-600 text-white"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="deliverables" className="text-gray-200">
              Deliverables (comma separated)
            </Label>
            <Textarea
              id="deliverables"
              value={deliverables}
              onChange={(e) => setDeliverables(e.target.value)}
              placeholder="Roadmap review, Resume overhaul, Mock interview, KPI alignment"
              rows={2}
              className="bg-gray-800/50 border-gray-600 text-white placeholder:text-gray-500 resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="expectedOutcomes" className="text-gray-200">
              Expected Outcomes
            </Label>
            <Textarea
              id="expectedOutcomes"
              value={expectedOutcomes}
              onChange={(e) => setExpectedOutcomes(e.target.value)}
              placeholder="Confidence presenting, strategic thinking clarity, promotion readiness"
              rows={2}
              className="bg-gray-800/50 border-gray-600 text-white placeholder:text-gray-500 resize-none"
            />
          </div>

          <Button 
            type="submit" 
            className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Package
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}