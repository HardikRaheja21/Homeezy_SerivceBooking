import { Badge } from '@/components/ui/badge';
import { normalizeBookingStatus } from '@/lib/booking-utils';

const STATUS_STYLES: Record<string, string> = {
  requested: 'bg-amber-100 text-amber-800 hover:bg-amber-100',
  accepted: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  worker_enroute: 'bg-sky-100 text-sky-800 hover:bg-sky-100',
  in_progress: 'bg-purple-100 text-purple-800 hover:bg-purple-100',
  completed: 'bg-emerald-100 text-emerald-800 hover:bg-emerald-100',
  cancelled: 'bg-red-100 text-red-800 hover:bg-red-100',
  disputed: 'bg-red-100 text-red-800 hover:bg-red-100',
};

const STATUS_LABELS: Record<string, string> = {
  requested: 'Requested',
  accepted: 'Accepted',
  worker_enroute: 'En Route',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  disputed: 'Disputed',
};

export function BookingStatusBadge({ status }: { status: string }) {
  const key = normalizeBookingStatus(status);
  return (
    <Badge variant="secondary" className={STATUS_STYLES[key] || ''}>
      {STATUS_LABELS[key] || status}
    </Badge>
  );
}
