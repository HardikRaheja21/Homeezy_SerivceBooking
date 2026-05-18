'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/store/useAuth';

/** Redirect /dashboard to the role-specific dashboard */
export default function DashboardIndexPage() {
  const router = useRouter();
  const user = useAuth((s) => s.user);

  useEffect(() => {
    const role = user?.role;
    if (role === 'customer') router.replace('/dashboard/customer');
    else if (role === 'worker') router.replace('/dashboard/worker');
    else if (role === 'admin') router.replace('/dashboard/admin');
    else router.replace('/login');
  }, [user, router]);

  return (
    <div className="flex flex-1 items-center justify-center min-h-[50vh]">
      <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
    </div>
  );
}
