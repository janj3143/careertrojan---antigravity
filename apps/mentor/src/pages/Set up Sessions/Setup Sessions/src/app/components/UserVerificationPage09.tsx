import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CheckCircle2, XCircle, Shield, AlertCircle, User } from 'lucide-react';
import { toast } from 'sonner';

interface UserVerificationPage09Props {
  userEmail: string;
  userName: string;
  onConfirmed: (confirmed: boolean) => void;
  onCancel: () => void;
}

export function UserVerificationPage09({ userEmail, userName, onConfirmed, onCancel }: UserVerificationPage09Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setLoading(true);
    setError('');

    try {
      // Stub: This would call the user portal API to confirm permissions
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Permission verification complete!');
      onConfirmed(true);
    } catch (err: any) {
      setError(err.message || 'Confirmation failed');
      toast.error('Confirmation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md bg-white shadow-2xl">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <Shield className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <CardTitle>Permission Verification</CardTitle>
              <CardDescription>Page 09 - Role Authorization</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div className="text-sm text-green-900">
                <p className="font-medium mb-1">User Account Verified</p>
                <p className="text-green-800">
                  Your user account has been successfully verified. Now confirming mentor role permissions.
                </p>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Name:</span>
              <span className="font-medium">{userName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Email:</span>
              <span className="font-medium text-sm">{userEmail}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Requested Role:</span>
              <Badge className="bg-blue-100 text-blue-800 border-blue-200">Mentor</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">2FA Status:</span>
              <Badge className="bg-green-100 text-green-800 border-green-200">Enabled</Badge>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-2">Permissions to be granted:</p>
                <ul className="text-xs text-blue-800 space-y-1">
                  <li>✓ Access to mentor portal</li>
                  <li>✓ Manage mentoring sessions</li>
                  <li>✓ View mentee information</li>
                  <li>✓ Calendar integration</li>
                  <li>✓ Communication tools</li>
                </ul>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm flex items-center gap-2">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button
              onClick={handleConfirm}
              className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
              disabled={loading}
            >
              {loading ? 'Confirming...' : 'Confirm & Grant Access'}
            </Button>
            <Button
              onClick={onCancel}
              variant="outline"
              disabled={loading}
            >
              Cancel
            </Button>
          </div>

          <p className="text-xs text-center text-gray-500">
            By confirming, you authorize this account to have mentor-level access
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
