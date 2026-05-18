'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { Users, Briefcase, Activity, Search } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

import { apiClient, getApiErrorMessage } from '@/lib/api/client';
import { useDashboardSync } from '@/lib/hooks/useDashboardSync';
import { emitDashboardRefresh } from '@/lib/realtime-events';
import { BookingStatusBadge } from '@/components/booking/BookingStatusBadge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

type PendingWorker = {
  id: string;
  full_name: string;
  email: string;
  service_category: string;
  government_id_document?: string | null;
  address_proof_document?: string | null;
  profile_photo?: string | null;
};

type RecentBooking = {
  id: string;
  customer_name: string;
  worker_name: string;
  service_category: string;
  status: string;
  estimated_price: number;
  requested_at: string;
};

type DashboardStats = {
  total_users: number;
  total_customers: number;
  total_workers: number;
  pending_worker_approvals: number;
  total_bookings: number;
  completed_bookings: number;
  todays_bookings: number;
  total_platform_revenue: number;
};

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [workers, setWorkers] = useState<PendingWorker[]>([]);
  const [bookings, setBookings] = useState<RecentBooking[]>([]);
  const [workerSearch, setWorkerSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [statsRes, workersRes, bookingsRes] = await Promise.all([
        apiClient.get('/api/v1/admin/dashboard/stats'),
        apiClient.get('/api/v1/admin/workers/pending'),
        apiClient.get('/api/v1/admin/bookings/recent', { params: { limit: 20 } }),
      ]);
      setStats(statsRes.data);
      setWorkers(Array.isArray(workersRes.data) ? workersRes.data : []);
      setBookings(Array.isArray(bookingsRes.data) ? bookingsRes.data : []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to load admin dashboard'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useDashboardSync(fetchData);

  async function approveWorker(workerId: string, approved: boolean) {
    try {
      await apiClient.post('/api/v1/admin/workers/approve', {
        worker_id: workerId,
        approved,
        rejection_reason: approved ? null : 'Did not meet requirements',
      });
      toast.success(approved ? 'Worker approved' : 'Worker rejected');
      emitDashboardRefresh();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Action failed'));
    }
  }

  const filteredWorkers = useMemo(() => {
    const q = workerSearch.toLowerCase().trim();
    if (!q) return workers;
    return workers.filter(
      (w) =>
        w.full_name.toLowerCase().includes(q) ||
        w.email.toLowerCase().includes(q) ||
        w.service_category.toLowerCase().includes(q)
    );
  }, [workers, workerSearch]);

  const chartData = stats
    ? [
        { name: 'Customers', bookings: stats.total_customers },
        { name: 'Workers', bookings: stats.total_workers },
        { name: 'Bookings', bookings: stats.total_bookings },
        { name: 'Completed', bookings: stats.completed_bookings },
        { name: 'Today', bookings: stats.todays_bookings },
      ]
    : [];

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Admin Overview</h1>
        <p className="text-muted-foreground mt-1">Platform metrics and moderation controls.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {isLoading ? (
          [1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />)
        ) : (
          <>
            <StatCard label="Total Users" value={stats?.total_users ?? 0} icon={<Users className="h-4 w-4 text-emerald-500" />} />
            <StatCard label="Professionals" value={stats?.total_workers ?? 0} icon={<Briefcase className="h-4 w-4 text-blue-500" />} />
            <StatCard label="Total Bookings" value={stats?.total_bookings ?? 0} icon={<Activity className="h-4 w-4 text-amber-500" />} />
            <StatCard label="Revenue" value={`$${(stats?.total_platform_revenue ?? 0).toLocaleString()}`} icon={<span className="text-lg font-bold text-slate-400">$</span>} />
          </>
        )}
      </div>

      <Card className="mb-8 border-slate-200">
        <CardHeader>
          <CardTitle>Platform Activity</CardTitle>
          <CardDescription>Live counts from your database</CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          {isLoading ? <Skeleton className="h-full w-full" /> : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="bookings" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="workers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workers">Worker approvals ({workers.length})</TabsTrigger>
          <TabsTrigger value="bookings">Recent bookings</TabsTrigger>
        </TabsList>

        <TabsContent value="workers">
          <Card>
            <CardHeader>
              <CardTitle>Pending worker approvals</CardTitle>
              <div className="relative mt-2 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, email, category..."
                  className="pl-9"
                  value={workerSearch}
                  onChange={(e) => setWorkerSearch(e.target.value)}
                />
              </div>
            </CardHeader>
            <CardContent className="px-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={3}><Skeleton className="h-10" /></TableCell></TableRow>
                  ) : filteredWorkers.length > 0 ? (
                    filteredWorkers.map((worker) => (
                      <TableRow key={worker.id}>
                        <TableCell>
                          <p className="font-medium">{worker.full_name}</p>
                          <p className="text-xs text-slate-500">{worker.email}</p>
                        </TableCell>
                        <TableCell>
                          <p>{worker.service_category}</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {worker.profile_photo && (
                              <a href={worker.profile_photo} target="_blank" rel="noreferrer" className="text-xs text-emerald-600 underline">
                                Photo
                              </a>
                            )}
                            {worker.government_id_document && (
                              <a href={worker.government_id_document} target="_blank" rel="noreferrer" className="text-xs text-emerald-600 underline">
                                ID doc
                              </a>
                            )}
                            {worker.address_proof_document && (
                              <a href={worker.address_proof_document} target="_blank" rel="noreferrer" className="text-xs text-emerald-600 underline">
                                Address
                              </a>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right space-x-2">
                          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => approveWorker(worker.id, true)}>
                            Approve
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => approveWorker(worker.id, false)}>
                            Reject
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center py-8 text-slate-500">
                        No pending workers match your search
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bookings">
          <Card>
            <CardHeader>
              <CardTitle>Recent bookings</CardTitle>
              <CardDescription>Monitor platform activity in real time</CardDescription>
            </CardHeader>
            <CardContent className="px-0 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Service</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Worker</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead className="text-right">View</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={6}><Skeleton className="h-10" /></TableCell></TableRow>
                  ) : bookings.length > 0 ? (
                    bookings.map((b) => (
                      <TableRow key={b.id}>
                        <TableCell className="font-medium capitalize">{b.service_category}</TableCell>
                        <TableCell>{b.customer_name}</TableCell>
                        <TableCell>{b.worker_name}</TableCell>
                        <TableCell><BookingStatusBadge status={b.status} /></TableCell>
                        <TableCell>${b.estimated_price?.toFixed(2)}</TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="outline" asChild>
                            <Link href={`/bookings/${b.id}`}>Details</Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-500">No bookings yet</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}
