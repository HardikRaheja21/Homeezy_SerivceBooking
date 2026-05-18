'use client';

import { Check, Circle } from 'lucide-react';
import { format } from 'date-fns';
import { normalizeBookingStatus } from '@/lib/booking-utils';
import { cn } from '@/lib/utils';

type TimelineData = {
  requested_at?: string | null;
  accepted_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
};

const STEPS = [
  { key: 'requested', label: 'Requested' },
  { key: 'accepted', label: 'Accepted' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'completed', label: 'Completed' },
] as const;

function stepTimestamp(key: string, timeline: TimelineData): string | null {
  switch (key) {
    case 'requested':
      return timeline.requested_at ?? null;
    case 'accepted':
      return timeline.accepted_at ?? null;
    case 'in_progress':
      return timeline.started_at ?? null;
    case 'completed':
      return timeline.completed_at ?? null;
    default:
      return null;
  }
}

function stepIndex(status: string): number {
  const s = normalizeBookingStatus(status);
  if (s === 'cancelled' || s === 'disputed') return -1;
  if (s === 'requested') return 0;
  if (s === 'accepted' || s === 'worker_enroute') return 1;
  if (s === 'in_progress') return 2;
  if (s === 'completed') return 3;
  return 0;
}

export function BookingTimeline({
  status,
  timeline,
}: {
  status: string;
  timeline: TimelineData;
}) {
  const current = stepIndex(status);
  const normalized = normalizeBookingStatus(status);

  if (normalized === 'cancelled' || normalized === 'disputed') {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
        <p className="font-semibold capitalize">{normalized.replace('_', ' ')}</p>
        {timeline.cancelled_at && (
          <p className="mt-1 text-red-600">
            {format(new Date(timeline.cancelled_at), 'PPp')}
          </p>
        )}
      </div>
    );
  }

  return (
    <ol className="space-y-0">
      {STEPS.map((step, idx) => {
        const done = idx < current;
        const active = idx === current;
        const ts = stepTimestamp(step.key, timeline);

        return (
          <li key={step.key} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'flex h-9 w-9 items-center justify-center rounded-full border-2 transition-colors',
                  done && 'border-emerald-500 bg-emerald-500 text-white',
                  active && !done && 'border-emerald-500 bg-emerald-50 text-emerald-700',
                  !done && !active && 'border-slate-200 bg-white text-slate-400'
                )}
              >
                {done ? <Check className="h-4 w-4" /> : <Circle className="h-3 w-3 fill-current" />}
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={cn('w-0.5 flex-1 min-h-[2rem]', done ? 'bg-emerald-400' : 'bg-slate-200')}
                />
              )}
            </div>
            <div className="pb-8 pt-1">
              <p
                className={cn(
                  'font-medium',
                  active ? 'text-emerald-700' : done ? 'text-slate-800' : 'text-slate-400'
                )}
              >
                {step.label}
              </p>
              {ts && (
                <p className="text-xs text-slate-500 mt-0.5">{format(new Date(ts), 'PPp')}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
