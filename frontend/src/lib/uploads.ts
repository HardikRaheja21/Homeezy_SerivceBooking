import { apiClient, getApiErrorMessage } from '@/lib/api/client';

export type UploadStatus = {
  cloudinary_configured: boolean;
  uploads_available: boolean;
  max_file_mb: number;
  allowed_types: string[];
};

const MAX_MB = 5;
const ALLOWED = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];

export async function fetchUploadStatus(): Promise<UploadStatus> {
  const res = await apiClient.get('/api/v1/uploads/status');
  return res.data;
}

export function validateImageFile(file: File): string | null {
  if (!ALLOWED.includes(file.type)) {
    return 'Please upload a JPEG, PNG, or WebP image.';
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    return `Image must be under ${MAX_MB}MB.`;
  }
  return null;
}

export async function uploadProfilePhoto(file: File, onProgress?: (pct: number) => void): Promise<string> {
  const err = validateImageFile(file);
  if (err) throw new Error(err);
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post('/api/v1/uploads/profile-photo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data.url as string;
}

export async function uploadWorkerDocument(
  docType: 'government_id' | 'address_proof' | 'police_verification',
  file: File,
  onProgress?: (pct: number) => void
): Promise<string> {
  const err = validateImageFile(file);
  if (err) throw new Error(err);
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post(`/api/v1/uploads/worker/document?doc_type=${docType}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data.url as string;
}

export async function uploadBookingAttachment(
  bookingId: string,
  file: File,
  onProgress?: (pct: number) => void
): Promise<string[]> {
  const err = validateImageFile(file);
  if (err) throw new Error(err);
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post(`/api/v1/uploads/booking/${bookingId}/attachment`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data.attachments as string[];
}

export { getApiErrorMessage };
