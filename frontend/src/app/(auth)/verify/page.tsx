'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Suspense } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient, getApiErrorMessage } from '@/lib/api/client';

function VerifyForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const phone = searchParams.get('phone') || '';

  const [emailOtp, setEmailOtp] = useState('');
  const [phoneOtp, setPhoneOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);

  async function verify(type: 'email' | 'phone', otp: string, identifier: string) {
    if (!identifier || otp.length < 4) {
      toast.error('Enter a valid OTP');
      return;
    }
    setIsLoading(true);
    try {
      const res = await apiClient.post('/api/v1/auth/verify-otp', {
        identifier,
        otp,
        type,
      });
      if (type === 'email') setEmailVerified(true);
      else setPhoneVerified(true);
      toast.success(res.data?.message || 'Verified');
      if (res.data?.account_active) {
        toast.success('Account activated! You can sign in now.');
        router.push('/login');
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Verification failed'));
    } finally {
      setIsLoading(false);
    }
  }

  async function resend(type: 'email' | 'phone', identifier: string) {
    if (!identifier) return;
    try {
      await apiClient.post('/api/v1/auth/resend-otp', { identifier, type });
      toast.success(`OTP resent to your ${type}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not resend OTP'));
    }
  }

  return (
    <Card className="w-full max-w-md shadow-lg">
      <CardHeader>
        <CardTitle>Verify your account</CardTitle>
        <CardDescription>Enter the codes sent to your email and phone</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label>Email OTP {email ? `(${email})` : ''}</Label>
          <div className="flex gap-2">
            <Input
              placeholder="6-digit code"
              value={emailOtp}
              onChange={(e) => setEmailOtp(e.target.value)}
              disabled={isLoading || emailVerified}
              maxLength={6}
            />
            <Button
              type="button"
              disabled={isLoading || emailVerified || !email}
              onClick={() => verify('email', emailOtp, email)}
            >
              {emailVerified ? 'Done' : 'Verify'}
            </Button>
          </div>
          {email && !emailVerified && (
            <Button variant="link" className="px-0 h-auto text-xs" onClick={() => resend('email', email)}>
              Resend email OTP
            </Button>
          )}
        </div>

        <div className="space-y-2">
          <Label>Phone OTP {phone ? `(${phone})` : ''}</Label>
          <div className="flex gap-2">
            <Input
              placeholder="6-digit code"
              value={phoneOtp}
              onChange={(e) => setPhoneOtp(e.target.value)}
              disabled={isLoading || phoneVerified}
              maxLength={6}
            />
            <Button
              type="button"
              disabled={isLoading || phoneVerified || !phone}
              onClick={() => verify('phone', phoneOtp, phone)}
            >
              {phoneVerified ? 'Done' : 'Verify'}
            </Button>
          </div>
          {phone && !phoneVerified && (
            <Button variant="link" className="px-0 h-auto text-xs" onClick={() => resend('phone', phone)}>
              Resend phone OTP
            </Button>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-center border-t p-6">
        <Link href="/login" className="text-sm text-primary hover:underline">
          Back to sign in
        </Link>
      </CardFooter>
    </Card>
  );
}

export default function VerifyPage() {
  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <Suspense fallback={<Loader2 className="h-8 w-8 animate-spin" />}>
        <VerifyForm />
      </Suspense>
    </div>
  );
}
