'use client';

import { useCallback, useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { apiClient, getApiErrorMessage } from '@/lib/api/client';
import { ImageUploader } from '@/components/upload/ImageUploader';
import { uploadProfilePhoto, uploadWorkerDocument } from '@/lib/uploads';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

type WorkerProfile = {
  profile_photo?: string | null;
  government_id_document?: string | null;
  address_proof_document?: string | null;
  police_verification_document?: string | null;
  service_category?: string;
  verification_status?: string;
};

export function WorkerProfilePanel() {
  const [profile, setProfile] = useState<WorkerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/v1/workers/profile');
      setProfile(res.data);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to load profile'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <Skeleton className="h-64 w-full rounded-xl" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile & documents</CardTitle>
        <CardDescription>
          Upload your photo and verification documents for admin review.
          Status: <span className="capitalize font-medium">{profile?.verification_status}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-8 md:grid-cols-2">
        <ImageUploader
          label="Profile photo"
          currentUrl={profile?.profile_photo}
          onUpload={(file, onProgress) => uploadProfilePhoto(file, onProgress)}
          onSuccess={() => load()}
        />
        <ImageUploader
          label="Government ID"
          hint="Aadhar, passport, or driver license"
          currentUrl={profile?.government_id_document}
          onUpload={(file, p) => uploadWorkerDocument('government_id', file, p)}
          onSuccess={() => load()}
        />
        <ImageUploader
          label="Address proof"
          currentUrl={profile?.address_proof_document}
          onUpload={(file, p) => uploadWorkerDocument('address_proof', file, p)}
          onSuccess={() => load()}
        />
        <ImageUploader
          label="Police verification (optional)"
          currentUrl={profile?.police_verification_document}
          onUpload={(file, p) => uploadWorkerDocument('police_verification', file, p)}
          onSuccess={() => load()}
        />
      </CardContent>
    </Card>
  );
}
