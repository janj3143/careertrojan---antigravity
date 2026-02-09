import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { CheckCircle2, XCircle, User, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface UserVerificationPage03Props {
  userEmail: string;
  onVerified: (verified: boolean) => void;
  onCancel: () => void;
}

export function UserVerificationPage03({ userEmail, onVerified, onCancel }: UserVerificationPage03Props) {
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');

  const handleVerify = async () => {
    if (!verificationCode) {
      setError('Please enter the verification code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Stub: This would call the user portal API to verify
      // For now, accept code "USER123" as valid
      if (verificationCode === 'USER123') {
        toast.success('User account verified successfully!');
        onVerified(true);
      } else {
        throw new Error('Invalid verification code');
      }
    } catch (err: any) {
      setError(err.message || 'Verification failed');
      toast.error('Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md bg-white shadow-2xl">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <CardTitle>User Portal Verification</CardTitle>
              <CardDescription>Page 03 - Account Linking</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">Verify Your User Account</p>
                <p className="text-blue-800">
                  To become a mentor, you must link your mentor account to an existing user account.
                  Check your email <strong>{userEmail}</strong> for the verification code.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="verification-code">Verification Code from User Portal</Label>
            <Input
              id="verification-code"
              type="text"
              placeholder="Enter code (e.g., USER123)"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.toUpperCase())}
              className="font-mono"
            />
            <p className="text-xs text-gray-500">
              Demo code for testing: <code className="bg-gray-100 px-2 py-1 rounded">USER123</code>
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm flex items-center gap-2">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-sm text-gray-700 font-medium mb-2">What this verifies:</p>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>✓ You have an active user account</li>
              <li>✓ Email address matches across accounts</li>
              <li>✓ User portal access rights</li>
              <li>✓ Identity confirmation</li>
            </ul>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleVerify}
              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
              disabled={loading || !verificationCode}
            >
              {loading ? 'Verifying...' : 'Verify Account'}
            </Button>
            <Button
              onClick={onCancel}
              variant="outline"
              disabled={loading}
            >
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
