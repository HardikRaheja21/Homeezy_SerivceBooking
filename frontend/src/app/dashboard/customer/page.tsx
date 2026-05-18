'use client';

import { useCallback, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, AlertCircle, Wrench, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import Link from 'next/link';

import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/store/useAuth';
import {
  BookingListItem,
  extractListItems,
  mapBookingItem,
  normalizeBookingStatus,
} from '@/lib/booking-utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { useDashboardSync } from '@/lib/hooks/useDashboardSync';

export default function CustomerDashboard() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState<BookingListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Initialize websocket connection
  useWebSocket();

  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/bookings/my-bookings', { params: { page_size: 10 } });
      const items = extractListItems<Record<string, unknown>>(response.data).map(mapBookingItem);
      setBookings(items);
    } catch (error) {
      console.error('Failed to load dashboard data', error);
      toast.error('Could not load your bookings');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useDashboardSync(fetchDashboardData);

  const getStatusBadge = (status: string) => {
    switch (normalizeBookingStatus(status)) {
      case 'requested':
        return <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100">Requested</Badge>;
      case 'accepted':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-100">Accepted</Badge>;
      case 'worker_enroute':
        return <Badge variant="secondary" className="bg-sky-100 text-sky-800 hover:bg-sky-100">En Route</Badge>;
      case 'in_progress':
        return <Badge variant="secondary" className="bg-purple-100 text-purple-800 hover:bg-purple-100">In Progress</Badge>;
      case 'completed':
        return <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">Completed</Badge>;
      case 'cancelled':
        return <Badge variant="destructive">Cancelled</Badge>;
      case 'disputed':
        return <Badge variant="destructive" className="bg-red-100 text-red-800 hover:bg-red-100">Disputed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customer Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back, {user?.full_name}</p>
        </div>
        <Button asChild className="rounded-xl">
          <Link href="/services">Book New Service</Link>
        </Button>
      </div>

      <Tabs defaultValue="bookings" className="space-y-6">
        <TabsList className="bg-slate-100 p-1">
          <TabsTrigger value="bookings" className="rounded-lg">My Bookings</TabsTrigger>
          <TabsTrigger value="profile" className="rounded-lg">Profile Settings</TabsTrigger>
          <TabsTrigger value="complaints" className="rounded-lg">Complaints</TabsTrigger>
        </TabsList>
        
        <TabsContent value="bookings" className="space-y-4">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle>Recent Bookings</CardTitle>
              <CardDescription>Track the status of your requested services.</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex flex-col sm:flex-row justify-between p-4 border rounded-xl gap-4">
                      <div className="space-y-2 w-full">
                        <Skeleton className="h-5 w-1/3" />
                        <Skeleton className="h-4 w-1/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                      <Skeleton className="h-10 w-24 rounded-lg" />
                    </div>
                  ))}
                </div>
              ) : bookings.length > 0 ? (
                <div className="space-y-4">
                  {bookings.map((booking, idx) => (
                    <div 
                      key={booking.id} 
                      className="flex flex-col sm:flex-row justify-between p-5 border border-slate-200 rounded-2xl hover:border-emerald-300 hover:shadow-md transition-all duration-300 bg-white gap-4 group animate-in slide-in-from-bottom-4 fade-in fill-mode-both"
                      style={{ animationDelay: `${idx * 100}ms` }}
                    >
                      <div className="space-y-3">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-lg text-slate-900">{booking.service_category}</h3>
                          {getStatusBadge(booking.status)}
                        </div>
                        <div className="flex items-center text-sm text-slate-500 gap-5">
                          <span className="flex items-center bg-slate-50 px-2 py-1 rounded-md"><Calendar className="h-4 w-4 mr-2 text-slate-400" /> {format(new Date(booking.preferred_date), 'MMM d, yyyy')}</span>
                          <span className="flex items-center bg-slate-50 px-2 py-1 rounded-md"><Clock className="h-4 w-4 mr-2 text-slate-400" /> {format(new Date(booking.preferred_date), 'h:mm a')}</span>
                        </div>
                        <div className="flex items-center text-sm text-slate-500 bg-slate-50 px-2 py-1 rounded-md inline-flex max-w-full">
                          <MapPin className="h-4 w-4 mr-2 flex-shrink-0 text-slate-400" />
                          <span className="truncate">{booking.address}</span>
                        </div>
                      </div>
                      <div className="flex flex-row sm:flex-col justify-between items-end sm:items-end gap-2 mt-4 sm:mt-0">
                        <div className="text-right bg-slate-50 px-3 py-2 rounded-lg border border-slate-100">
                          <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">Estimated</p>
                          <p className="font-bold text-slate-900 text-lg">${booking.estimated_price?.toFixed(2) || '--'}</p>
                        </div>
                        <Button variant="outline" size="sm" className="rounded-xl group-hover:bg-emerald-50 group-hover:text-emerald-700 group-hover:border-emerald-200 transition-colors" asChild>
                          <Link href={`/bookings/${booking.id}`}>
                            View Details <ChevronRight className="h-4 w-4 ml-1" />
                          </Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-300 transition-all hover:bg-slate-100">
                  <div className="h-20 w-20 bg-white rounded-full flex items-center justify-center mx-auto mb-5 shadow-sm border border-slate-100">
                    <Wrench className="h-10 w-10 text-emerald-500" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">No bookings yet</h3>
                  <p className="text-slate-500 mt-2 mb-8 max-w-sm mx-auto">You haven't requested any services yet. Our verified professionals are ready to help.</p>
                  <Button asChild size="lg" className="rounded-full bg-emerald-600 hover:bg-emerald-700 shadow-sm">
                    <Link href="/services">Browse Services</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="profile">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Manage your account details and preferences.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm font-medium text-slate-500">Full Name</p>
                  <p className="text-lg">{user?.full_name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Email Address</p>
                  <p className="text-lg">{user?.email}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Phone Number</p>
                  <p className="text-lg">{user?.phone || 'Not provided'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Account Type</p>
                  <Badge variant="outline" className="mt-1 capitalize">{user?.role}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="complaints">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle>My Complaints</CardTitle>
              <CardDescription>Track issues you've reported.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 px-4 border border-dashed border-slate-200 rounded-xl bg-slate-50">
                <AlertCircle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-lg font-medium text-slate-700">No active complaints</h3>
                <p className="text-slate-500 mt-1">If you have an issue with a booking, you can report it from the booking details page.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
