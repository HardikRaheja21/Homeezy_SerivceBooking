'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Loader2,
  MapPin,
  Phone,
  User,
  Wrench,
} from 'lucide-react';
import { toast } from 'sonner';

import { apiClient, getApiErrorMessage } from '@/lib/api/client';
import { useAuth } from '@/store/useAuth';
import { normalizeBookingStatus } from '@/lib/booking-utils';
import type { BookingDetail } from '@/types/booking';
import { PaymentCheckout } from '@/components/payment/PaymentCheckout';
import { ImageUploader } from '@/components/upload/ImageUploader';
import { uploadBookingAttachment } from '@/lib/uploads';
import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { emitDashboardRefresh } from '@/lib/realtime-events';
import { BookingStatusBadge } from '@/components/booking/BookingStatusBadge';
import { BookingTimeline } from '@/components/booking/BookingTimeline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;
  const { user } = useAuth();

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [showCancelForm, setShowCancelForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const { joinBookingRoom, leaveBookingRoom } = useWebSocket();

  const fetchBooking = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get(`/api/v1/bookings/${bookingId}`);
      setBooking(res.data);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to load booking'));
      router.push(user?.role ? `/dashboard/${user.role}` : '/login');
    } finally {
      setIsLoading(false);
    }
  }, [bookingId, router, user?.role]);

  useEffect(() => {
    if (bookingId) fetchBooking();
  }, [bookingId, fetchBooking]);

  useEffect(() => {
    if (bookingId) {
      joinBookingRoom(bookingId);
      return () => leaveBookingRoom(bookingId);
    }
  }, [bookingId, joinBookingRoom, leaveBookingRoom]);

  const runAction = async (fn: () => Promise<void>, successMsg: string) => {
    setActionLoading(true);
    try {
      await fn();
      toast.success(successMsg);
      emitDashboardRefresh();
      await fetchBooking();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Action failed'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleAccept = () =>
    runAction(
      () => apiClient.post(`/api/v1/bookings/${bookingId}/accept`),
      'Job accepted!'
    );

  const handleDecline = () =>
    runAction(
      () =>
        apiClient.post(`/api/v1/bookings/${bookingId}/update-status`, {
          status: 'cancelled',
          reason: 'Declined by worker',
        }),
      'Request declined'
    );

  const handleStatus = (status: string) =>
    runAction(
      () => apiClient.post(`/api/v1/bookings/${bookingId}/update-status`, { status }),
      'Status updated'
    );

  const handleCancel = () =>
    runAction(
      () =>
        apiClient.post(`/api/v1/bookings/${bookingId}/update-status`, {
          status: 'cancelled',
          reason: cancelReason || 'Cancelled by customer',
        }),
      'Booking cancelled'
    ).then(() => setShowCancelForm(false));

  const handleReview = () =>
    runAction(async () => {
      await apiClient.post('/api/v1/reviews/create', {
        booking_id: bookingId,
        rating: reviewRating,
        review_text: reviewText,
      });
      setShowReviewForm(false);
      emitDashboardRefresh();
    }, 'Thank you for your review!');

  if (isLoading) {
    return <BookingDetailSkeleton />;
  }

  if (!booking) return null;

  const status = normalizeBookingStatus(booking.status);
  const dashboardHref = `/dashboard/${user?.role || 'customer'}`;

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <Button variant="ghost" asChild className="mb-6 -ml-2">
        <Link href={dashboardHref}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to dashboard
        </Link>
      </Button>

      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight capitalize">
              {booking.service_category}
            </h1>
            <BookingStatusBadge status={booking.status} />
          </div>
          <p className="text-muted-foreground mt-1 text-sm">
            Booking #{booking.id.substring(0, 8)} · Requested{' '}
            {booking.timeline.requested_at
              ? format(new Date(booking.timeline.requested_at), 'PPp')
              : '—'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Service details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 text-sm">
                <Wrench className="h-4 w-4 mt-0.5 text-emerald-600 shrink-0" />
                <div>
                  <p className="font-medium text-slate-900">Description</p>
                  <p className="text-slate-600 mt-1">
                    {booking.problem_description || booking.service_description}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 text-sm">
                <MapPin className="h-4 w-4 mt-0.5 text-emerald-600 shrink-0" />
                <div>
                  <p className="font-medium text-slate-900">Address</p>
                  <p className="text-slate-600 mt-1">{booking.address}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                <span className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg">
                  <Calendar className="h-4 w-4 text-slate-400" />
                  {format(new Date(booking.preferred_date), 'PPP')}
                </span>
                <span className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg">
                  <Clock className="h-4 w-4 text-slate-400" />
                  {booking.preferred_time_slot}
                </span>
              </div>
              {booking.special_instructions && (
                <p className="text-sm text-slate-600 bg-amber-50 border border-amber-100 rounded-lg p-3">
                  <span className="font-medium text-amber-900">Notes: </span>
                  {booking.special_instructions}
                </p>
              )}
              {booking.cancellation_reason && (
                <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg p-3">
                  <span className="font-medium">Cancellation reason: </span>
                  {booking.cancellation_reason}
                </p>
              )}
            </CardContent>
          </Card>

          {(booking.customer_attachments?.length ?? 0) > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Photos</CardTitle>
                <CardDescription>Images attached to this booking</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {booking.customer_attachments?.map((url) => (
                    <a
                      key={url}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block h-24 w-24 rounded-xl overflow-hidden border border-slate-200 hover:ring-2 ring-emerald-400"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={url} alt="Booking attachment" className="h-full w-full object-cover" />
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {booking.permissions.can_upload_photos && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Add photos</CardTitle>
                <CardDescription>Help the professional understand the issue</CardDescription>
              </CardHeader>
              <CardContent>
                <ImageUploader
                  label="Problem photo"
                  onUpload={(file, p) => uploadBookingAttachment(bookingId, file, p)}
                  onSuccess={() => fetchBooking()}
                />
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Progress</CardTitle>
              <CardDescription>Track your booking through each stage</CardDescription>
            </CardHeader>
            <CardContent>
              <BookingTimeline status={booking.status} timeline={booking.timeline} />
            </CardContent>
          </Card>

          {booking.permissions.can_review && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Leave a review</CardTitle>
                <CardDescription>Share your experience with the professional</CardDescription>
              </CardHeader>
              <CardContent>
                {!showReviewForm ? (
                  <Button onClick={() => setShowReviewForm(true)}>Write a review</Button>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <Label>Rating (1–5)</Label>
                      <Input
                        type="number"
                        min={1}
                        max={5}
                        value={reviewRating}
                        onChange={(e) => setReviewRating(Number(e.target.value))}
                        className="w-24 mt-1"
                      />
                    </div>
                    <div>
                      <Label>Your review</Label>
                      <Textarea
                        className="mt-1 min-h-[100px]"
                        value={reviewText}
                        onChange={(e) => setReviewText(e.target.value)}
                        placeholder="How was the service?"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleReview}
                        disabled={actionLoading || reviewText.length < 5}
                      >
                        {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Submit'}
                      </Button>
                      <Button variant="outline" onClick={() => setShowReviewForm(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <PaymentCheckout
            bookingId={bookingId}
            bookingStatus={status}
            onPaid={() => fetchBooking()}
          />

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">People</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex gap-3">
                <User className="h-4 w-4 text-slate-400 mt-0.5" />
                <div>
                  <p className="font-medium">Customer</p>
                  <p>{booking.customer.name}</p>
                  {booking.customer.phone && (
                    <p className="flex items-center gap-1 text-slate-500 mt-1">
                      <Phone className="h-3 w-3" />
                      {booking.customer.phone}
                    </p>
                  )}
                </div>
              </div>
              {booking.worker ? (
                <div className="flex gap-3">
                  <User className="h-4 w-4 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Professional</p>
                    <p>{booking.worker.name}</p>
                    {booking.worker.phone && (
                      <p className="flex items-center gap-1 text-slate-500 mt-1">
                        <Phone className="h-3 w-3" />
                        {booking.worker.phone}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 italic">Waiting for a professional to accept</p>
              )}
            </CardContent>
          </Card>

          <BookingActionsPanel
            booking={booking}
            status={status}
            actionLoading={actionLoading}
            showCancelForm={showCancelForm}
            cancelReason={cancelReason}
            onCancelReasonChange={setCancelReason}
            onShowCancelForm={setShowCancelForm}
            onAccept={handleAccept}
            onDecline={handleDecline}
            onStatus={handleStatus}
            onCancel={handleCancel}
          />
        </div>
      </div>
    </div>
  );
}

function BookingActionsPanel({
  booking,
  status,
  actionLoading,
  showCancelForm,
  cancelReason,
  onCancelReasonChange,
  onShowCancelForm,
  onAccept,
  onDecline,
  onStatus,
  onCancel,
}: {
  booking: BookingDetail;
  status: string;
  actionLoading: boolean;
  showCancelForm: boolean;
  cancelReason: string;
  onCancelReasonChange: (v: string) => void;
  onShowCancelForm: (v: boolean) => void;
  onAccept: () => void;
  onDecline: () => void;
  onStatus: (s: string) => void;
  onCancel: () => void;
}) {
  const { permissions } = booking;
  const hasActions =
    permissions.can_accept ||
    permissions.can_decline ||
    permissions.can_cancel ||
    (permissions.is_worker && ['accepted', 'worker_enroute', 'in_progress'].includes(status));

  if (!hasActions) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {permissions.can_accept && (
          <Button className="w-full bg-emerald-600 hover:bg-emerald-700" onClick={onAccept} disabled={actionLoading}>
            {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Accept job'}
          </Button>
        )}
        {(permissions.can_decline || permissions.can_accept) && status === 'requested' && !permissions.is_customer && (
          <Button variant="outline" className="w-full text-destructive" onClick={onDecline} disabled={actionLoading}>
            Decline
          </Button>
        )}

        {permissions.is_worker && status === 'accepted' && (
          <Button className="w-full" onClick={() => onStatus('worker_enroute')} disabled={actionLoading}>
            Start trip
          </Button>
        )}
        {permissions.is_worker && status === 'worker_enroute' && (
          <Button className="w-full" onClick={() => onStatus('in_progress')} disabled={actionLoading}>
            Start job
          </Button>
        )}
        {permissions.is_worker && status === 'in_progress' && (
          <Button className="w-full bg-emerald-600" onClick={() => onStatus('completed')} disabled={actionLoading}>
            Mark completed
          </Button>
        )}

        {permissions.can_cancel && !showCancelForm && (
          <Button variant="destructive" className="w-full" onClick={() => onShowCancelForm(true)}>
            Cancel booking
          </Button>
        )}
        {permissions.can_cancel && showCancelForm && (
          <div className="space-y-2">
            <Textarea
              placeholder="Reason for cancellation (optional)"
              value={cancelReason}
              onChange={(e) => onCancelReasonChange(e.target.value)}
            />
            <Button variant="destructive" className="w-full" onClick={onCancel} disabled={actionLoading}>
              Confirm cancellation
            </Button>
            <Button variant="ghost" className="w-full" onClick={() => onShowCancelForm(false)}>
              Keep booking
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BookingDetailSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl space-y-6">
      <Skeleton className="h-8 w-40" />
      <Skeleton className="h-10 w-2/3" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-64 lg:col-span-2" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}
