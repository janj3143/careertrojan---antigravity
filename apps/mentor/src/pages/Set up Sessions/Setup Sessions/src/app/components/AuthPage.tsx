import { useState } from 'react';
import { projectId, publicAnonKey } from '../../../utils/supabase/info';
import { supabase } from '../../../utils/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Calendar, Shield, Copy, Check, AlertCircle, User, Link as LinkIcon } from 'lucide-react';
import { InputOTP, InputOTPGroup, InputOTPSlot } from './ui/input-otp';
import { toast, Toaster } from 'sonner';
import backgroundImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';
import { UserVerificationPage03 } from './UserVerificationPage03';
import { UserVerificationPage09 } from './UserVerificationPage09';

const API_BASE = `https://${projectId}.supabase.co/functions/v1/make-server-f4611869`;

interface AuthPageProps {
  onAuthSuccess: (session: any) => void;
}

type AuthStep = 'form' | '2fa-setup' | '2fa-verify' | 'user-verify-03' | 'user-verify-09';

export function AuthPage({ onAuthSuccess }: AuthPageProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [authStep, setAuthStep] = useState<AuthStep>('form');
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [userVerified, setUserVerified] = useState(false);
  const [permissionsGranted, setPermissionsGranted] = useState(false);

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<'mentor' | 'mentee'>('mentor');
  const [otpCode, setOtpCode] = useState('');

  // 2FA state
  const [twoFactorSecret, setTwoFactorSecret] = useState('');
  const [twoFactorQR, setTwoFactorQR] = useState('');
  const [tempUserId, setTempUserId] = useState('');

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${publicAnonKey}`
        },
        body: JSON.stringify({ email, password, name, role })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Signup failed');
      }

      if (role === 'mentor') {
        // For mentors, require 2FA setup
        setTwoFactorSecret(data.twoFactorSecret);
        setTwoFactorQR(data.twoFactorQR);
        setTempUserId(data.userId);
        setAuthStep('2fa-setup');
        toast.success('Account created! Please set up 2FA');
      } else {
        // For mentees, sign in directly
        const { data: authData, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password
        });

        if (signInError) throw signInError;
        
        toast.success('Account created successfully!');
        onAuthSuccess(authData.session);
      }
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account');
      toast.error(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify2FASetup = async () => {
    if (otpCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/verify-2fa-setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${publicAnonKey}`
        },
        body: JSON.stringify({
          userId: tempUserId,
          token: otpCode
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || '2FA verification failed');
      }

      toast.success('2FA verified! Now linking to user account...');
      setAuthStep('user-verify-03');
    } catch (err: any) {
      console.error('2FA verification error:', err);
      setError(err.message || 'Invalid verification code');
      toast.error(err.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // First, sign in with email/password
      const { data: authData, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (signInError) throw signInError;

      // Check if this is a mentor account (requires 2FA)
      const response = await fetch(`${API_BASE}/check-role`, {
        headers: {
          'Authorization': `Bearer ${authData.session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      const roleData = await response.json();

      if (roleData.role === 'mentor') {
        // Mentor needs 2FA verification
        setTempUserId(authData.user.id);
        setAuthStep('2fa-verify');
        await supabase.auth.signOut(); // Sign out until 2FA is verified
        toast.info('Please enter your 2FA code');
      } else {
        // Mentee can proceed directly
        toast.success('Welcome back!');
        onAuthSuccess(authData.session);
      }
    } catch (err: any) {
      console.error('Sign in error:', err);
      setError(err.message || 'Invalid email or password');
      toast.error(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify2FA = async () => {
    if (otpCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/verify-2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${publicAnonKey}`
        },
        body: JSON.stringify({
          email,
          password,
          token: otpCode
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || '2FA verification failed');
      }

      // Now sign in with Supabase
      const { data: authData, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (signInError) throw signInError;

      toast.success('Welcome back!');
      onAuthSuccess(authData.session);
    } catch (err: any) {
      console.error('2FA verification error:', err);
      setError(err.message || 'Invalid verification code');
      toast.error(err.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    navigator.clipboard.writeText(twoFactorSecret);
    setCopiedSecret(true);
    toast.success('Secret copied to clipboard');
    setTimeout(() => setCopiedSecret(false), 2000);
  };

  const handleUserVerified = async (verified: boolean) => {
    if (verified) {
      setUserVerified(true);
      setAuthStep('user-verify-09');
      toast.success('User account verified!');
    }
  };

  const handlePermissionsGranted = async (granted: boolean) => {
    if (granted) {
      setPermissionsGranted(true);
      
      // Complete signup by signing in
      try {
        const { data: authData, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password
        });

        if (signInError) throw signInError;

        toast.success('Setup complete! Welcome to the mentor portal!');
        onAuthSuccess(authData.session);
      } catch (err: any) {
        console.error('Final signin error:', err);
        toast.error('Setup complete, but signin failed. Please try signing in manually.');
        setAuthStep('form');
      }
    }
  };

  // Show user verification pages
  if (authStep === 'user-verify-03') {
    return (
      <UserVerificationPage03
        userEmail={email}
        onVerified={handleUserVerified}
        onCancel={() => setAuthStep('form')}
      />
    );
  }

  if (authStep === 'user-verify-09') {
    return (
      <UserVerificationPage09
        userEmail={email}
        userName={name}
        onConfirmed={handlePermissionsGranted}
        onCancel={() => setAuthStep('form')}
      />
    );
  }

  return (
    <div className="min-h-screen relative flex items-center justify-center p-4">
      <Toaster />
      
      {/* Background Image - Exact PNG, No Overlay */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          imageRendering: 'crisp-edges',
        }}
      />

      {/* Auth Card */}
      <div className="relative z-10 w-full max-w-md">
        {authStep === '2fa-setup' ? (
          <Card className="bg-white/95 backdrop-blur-md shadow-2xl border-white/20">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle>Set Up 2FA</CardTitle>
                  <CardDescription>Secure your mentor account</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-2">
                  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <div className="text-sm text-blue-900">
                    <p className="font-medium mb-1">Security Required</p>
                    <p className="text-blue-800">
                      All mentor accounts must use Two-Factor Authentication (2FA) for enhanced security.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-3">Step 1: Scan QR Code</p>
                  <div className="bg-white p-4 rounded-lg border-2 border-gray-200 flex justify-center">
                    <img src={twoFactorQR} alt="2FA QR Code" className="w-48 h-48" />
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Use Google Authenticator, Authy, or any TOTP app
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium mb-2">Or enter this secret manually:</p>
                  <div className="flex gap-2">
                    <Input
                      value={twoFactorSecret}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={copySecret}
                      className="flex-shrink-0"
                    >
                      {copiedSecret ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <Label htmlFor="otp-verify">Step 2: Enter 6-digit code</Label>
                  <div className="flex justify-center mt-2">
                    <InputOTP
                      maxLength={6}
                      value={otpCode}
                      onChange={setOtpCode}
                      onComplete={handleVerify2FASetup}
                    >
                      <InputOTPGroup>
                        <InputOTPSlot index={0} />
                        <InputOTPSlot index={1} />
                        <InputOTPSlot index={2} />
                        <InputOTPSlot index={3} />
                        <InputOTPSlot index={4} />
                        <InputOTPSlot index={5} />
                      </InputOTPGroup>
                    </InputOTP>
                  </div>
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
                    {error}
                  </div>
                )}

                <Button
                  onClick={handleVerify2FASetup}
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                  disabled={loading || otpCode.length !== 6}
                >
                  {loading ? 'Verifying...' : 'Verify & Continue'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : authStep === '2fa-verify' ? (
          <Card className="bg-white/95 backdrop-blur-md shadow-2xl border-white/20">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle>2FA Verification</CardTitle>
                  <CardDescription>Enter your authentication code</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex gap-2">
                  <Shield className="w-5 h-5 text-green-600 flex-shrink-0" />
                  <div className="text-sm text-green-900">
                    <p className="font-medium mb-1">Security Check</p>
                    <p className="text-green-800">
                      Open your authenticator app and enter the 6-digit code.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="otp-signin">6-digit verification code</Label>
                  <div className="flex justify-center mt-2">
                    <InputOTP
                      maxLength={6}
                      value={otpCode}
                      onChange={setOtpCode}
                      onComplete={handleVerify2FA}
                    >
                      <InputOTPGroup>
                        <InputOTPSlot index={0} />
                        <InputOTPSlot index={1} />
                        <InputOTPSlot index={2} />
                        <InputOTPSlot index={3} />
                        <InputOTPSlot index={4} />
                        <InputOTPSlot index={5} />
                      </InputOTPGroup>
                    </InputOTP>
                  </div>
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
                    {error}
                  </div>
                )}

                <Button
                  onClick={handleVerify2FA}
                  className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
                  disabled={loading || otpCode.length !== 6}
                >
                  {loading ? 'Verifying...' : 'Verify & Sign In'}
                </Button>

                <Button
                  variant="outline"
                  onClick={() => {
                    setAuthStep('form');
                    setOtpCode('');
                    setError('');
                  }}
                  className="w-full"
                >
                  Back to Sign In
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-white/95 backdrop-blur-md shadow-2xl border-white/20">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle>Sessions Calendar</CardTitle>
                  <CardDescription>Mentor Portal • Secure Access</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="signin" className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="signin">Sign In</TabsTrigger>
                  <TabsTrigger value="signup">Sign Up</TabsTrigger>
                </TabsList>

                <TabsContent value="signin">
                  <form onSubmit={handleSignIn} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="signin-email">Email</Label>
                      <Input
                        id="signin-email"
                        type="email"
                        placeholder="mentor@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signin-password">Password</Label>
                      <Input
                        id="signin-password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                      />
                    </div>

                    {error && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
                        {error}
                      </div>
                    )}

                    <Button
                      type="submit"
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                      disabled={loading}
                    >
                      {loading ? 'Signing in...' : 'Sign In'}
                    </Button>
                  </form>
                </TabsContent>

                <TabsContent value="signup">
                  <form onSubmit={handleSignUp} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="signup-name">Full Name</Label>
                      <Input
                        id="signup-name"
                        type="text"
                        placeholder="John Doe"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-email">Email</Label>
                      <Input
                        id="signup-email"
                        type="email"
                        placeholder="mentor@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-password">Password</Label>
                      <Input
                        id="signup-password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={8}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-role">Role</Label>
                      <Select value={role} onValueChange={(value: 'mentor' | 'mentee') => setRole(value)}>
                        <SelectTrigger id="signup-role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mentor">
                            <div className="flex items-center gap-2">
                              <Shield className="w-4 h-4" />
                              Mentor (2FA Required)
                            </div>
                          </SelectItem>
                          <SelectItem value="mentee">
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4" />
                              Mentee
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {role === 'mentor' && (
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <div className="flex gap-2">
                          <Shield className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                          <p className="text-xs text-amber-900">
                            <strong>Mentor accounts require:</strong> 2FA setup + User portal verification (Pages 03 & 09)
                          </p>
                        </div>
                      </div>
                    )}

                    {error && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
                        {error}
                      </div>
                    )}

                    <Button
                      type="submit"
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                      disabled={loading}
                    >
                      {loading ? 'Creating account...' : 'Create Account'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}