'use client';

import { useEffect, useState } from 'react';
import { Users, Briefcase, Activity, CheckCircle, XCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

import { apiClient } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function AdminDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [workers, setWorkers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      setIsLoading(true);
      // Fetch stats (mock structure for now as backend might not have exact /admin/stats)
      // Fetch workers to approve
      const workersRes = await apiClient.get('/api/v1/auth/me'); // Just to test auth
      // In a real scenario, we would call /api/v1/admin/workers
      // Mocking workers for UI demonstration based on phase requirements
      setWorkers([
        { id: '1', full_name: 'John Doe', email: 'john@example.com', service_category: 'Plumbing', account_status: 'PENDING' },
        { id: '2', full_name: 'Jane Smith', email: 'jane@example.com', service_category: 'Electrical', account_status: 'ACTIVE' },
      ]);
      
      setStats({
        totalUsers: 145,
        totalWorkers: 42,
        totalBookings: 890,
        revenue: 12500,
        chartData: [
          { name: 'Jan', bookings: 40 },
          { name: 'Feb', bookings: 30 },
          { name: 'Mar', bookings: 20 },
          { name: 'Apr', bookings: 27 },
          { name: 'May', bookings: 18 },
          { name: 'Jun', bookings: 23 },
        ]
      });
    } catch (error) {
      console.error('Failed to load admin data', error);
    } finally {
      setIsLoading(false);
    }
  }

  const approveWorker = (id: string) => {
    toast.success(`Worker ${id} approved successfully!`);
    setWorkers(workers.map(w => w.id === id ? { ...w, account_status: 'ACTIVE' } : w));
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Admin Overview</h1>
        <p className="text-muted-foreground mt-1">Platform metrics and moderation controls.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Customers</CardTitle>
            <Users className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalUsers || 0}</div>
            <p className="text-xs text-emerald-500 mt-1">+12% from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Professionals</CardTitle>
            <Briefcase className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalWorkers || 0}</div>
            <p className="text-xs text-blue-500 mt-1">+4% from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Bookings</CardTitle>
            <Activity className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalBookings || 0}</div>
            <p className="text-xs text-amber-500 mt-1">+18% from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Platform Revenue</CardTitle>
            <span className="text-lg font-bold text-slate-400">$</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats?.revenue?.toLocaleString() || 0}</div>
            <p className="text-xs text-emerald-500 mt-1">+24% from last month</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-slate-200">
          <CardHeader>
            <CardTitle>Booking Trends</CardTitle>
            <CardDescription>Monthly booking volume across all categories</CardDescription>
          </CardHeader>
          <CardContent className="h-80">
            {stats?.chartData && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                  <Tooltip 
                    cursor={{fill: '#f1f5f9'}}
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                  />
                  <Bar dataKey="bookings" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Pending Approvals</CardTitle>
            <CardDescription>Workers waiting for KYC verification</CardDescription>
          </CardHeader>
          <CardContent className="px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Worker</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workers.filter(w => w.account_status === 'PENDING').map((worker) => (
                  <TableRow key={worker.id}>
                    <TableCell>
                      <p className="font-medium">{worker.full_name}</p>
                      <p className="text-xs text-slate-500">{worker.service_category}</p>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" onClick={() => approveWorker(worker.id)} className="bg-emerald-600 hover:bg-emerald-700">Approve</Button>
                    </TableCell>
                  </TableRow>
                ))}
                {workers.filter(w => w.account_status === 'PENDING').length === 0 && (
                  <TableRow>
                    <TableCell colSpan={2} className="text-center py-6 text-slate-500">
                      No pending approvals
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
