'use client';

import { useEffect, useState } from 'react';
import { CreditCard, Loader2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  fetchPaymentGatewayStatus,
  fetchBookingPayment,
  initiatePayment,
  completeSimulatedPayment,
  PAYMENT_UNAVAILABLE_MESSAGE,
  type BookingPaymentInfo,
} from '@/lib/payments';
import { getApiErrorMessage } from '@/lib/api/client';
import { emitDashboardRefresh } from '@/lib/realtime-events';

type PaymentCheckoutProps = {
  bookingId: string;
  bookingStatus: string;
  onPaid?: () => void;
};

export function PaymentCheckout({ bookingId, bookingStatus, onPaid }: PaymentCheckoutProps) {
  const [gatewayOk, setGatewayOk] = useState<boolean | null>(null);
  const [paymentInfo, setPaymentInfo] = useState<BookingPaymentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const [gw, info] = await Promise.all([
        fetchPaymentGatewayStatus(),
        fetchBookingPayment(bookingId),
      ]);
      setGatewayOk(gw.payments_available);
      setPaymentInfo(info);
    } catch {
      setGatewayOk(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (bookingStatus === 'completed') load();
  }, [bookingId, bookingStatus]);

  if (bookingStatus !== 'completed') return null;

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
        </CardContent>
      </Card>
    );
  }

  const isPaid = paymentInfo?.payment_status === 'paid';

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <CreditCard className="h-5 w-5 text-emerald-600" />
          Payment
        </CardTitle>
        <CardDescription>
          {isPaid ? 'This booking has been paid.' : 'Complete payment for your service.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between text-sm">
          <span className="text-slate-500">Amount due</span>
          <span className="font-bold text-lg">${paymentInfo?.amount?.toFixed(2) ?? '—'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-500">Status</span>
          <span className="capitalize font-medium">{paymentInfo?.payment_status ?? 'pending'}</span>
        </div>

        {isPaid ? (
          <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg p-3">Payment successful. Thank you!</p>
        ) : !gatewayOk ? (
          <p className="text-sm text-amber-800 bg-amber-50 rounded-lg p-3">{PAYMENT_UNAVAILABLE_MESSAGE}</p>
        ) : (
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              disabled={paying}
              onClick={async () => {
                setPaying(true);
                try {
                  const order = await initiatePayment(bookingId);
                  await completeSimulatedPayment(bookingId, order.gateway_order_id);
                  toast.success('Payment completed!');
                  await load();
                  emitDashboardRefresh();
                  onPaid?.();
                } catch (error) {
                  toast.error(getApiErrorMessage(error, 'Payment failed'));
                } finally {
                  setPaying(false);
                }
              }}
            >
              {paying ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Pay now
            </Button>
            <Button variant="outline" disabled={paying} onClick={load}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
