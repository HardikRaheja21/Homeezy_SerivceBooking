import { apiClient } from '@/lib/api/client';

export type PaymentGatewayStatus = {
  razorpay_configured: boolean;
  stripe_configured: boolean;
  payments_available: boolean;
};

export type BookingPaymentInfo = {
  booking_id: string;
  payment_status: string;
  amount: number;
  payment_record?: {
    id: string;
    status: string;
    gateway_order_id: string;
  } | null;
};

export const PAYMENT_UNAVAILABLE_MESSAGE =
  'Online payments are temporarily unavailable. Your booking is still confirmed — you can pay when this feature is enabled.';

let cachedGatewayStatus: PaymentGatewayStatus | null = null;

export async function fetchPaymentGatewayStatus(): Promise<PaymentGatewayStatus> {
  try {
    const res = await apiClient.get('/api/v1/payments/status');
    cachedGatewayStatus = res.data;
    return res.data;
  } catch {
    return {
      razorpay_configured: false,
      stripe_configured: false,
      payments_available: false,
    };
  }
}

export async function isPaymentsAvailable(): Promise<boolean> {
  if (process.env.NEXT_PUBLIC_PAYMENTS_ENABLED === 'true') return true;
  const status = cachedGatewayStatus ?? (await fetchPaymentGatewayStatus());
  return status.payments_available;
}

export async function fetchBookingPayment(bookingId: string): Promise<BookingPaymentInfo> {
  const res = await apiClient.get(`/api/v1/payments/booking/${bookingId}`);
  return res.data;
}

export async function initiatePayment(bookingId: string) {
  const res = await apiClient.post('/api/v1/payments/initiate', {
    booking_id: bookingId,
    payment_method: 'razorpay',
  });
  return res.data as {
    payment_id: string;
    gateway_order_id: string;
    amount: number;
    currency: string;
    razorpay_key_id?: string;
  };
}

export async function verifyPayment(
  bookingId: string,
  gatewayOrderId: string,
  gatewayTransactionId: string,
  signature: string
) {
  const res = await apiClient.post('/api/v1/payments/verify', {
    booking_id: bookingId,
    gateway_order_id: gatewayOrderId,
    gateway_transaction_id: gatewayTransactionId,
    signature,
  });
  return res.data;
}

/** Simulated checkout when Razorpay keys are not configured (backend accepts test_signature) */
export async function completeSimulatedPayment(bookingId: string, gatewayOrderId: string) {
  return verifyPayment(bookingId, gatewayOrderId, `sim_${Date.now()}`, 'test_signature');
}
