'use client';

import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Calendar, Clock, MapPin, CheckCircle, XCircle, Briefcase, DollarSign, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/store/useAuth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

import { useWebSocket } from '@/lib/hooks/useWebSocket';

export default function WorkerDashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize websocket connection
  useWebSocket();

  useEffect(() => {
    fetchJobs();
  }, []);

  async function fetchJobs() {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/api/v1/bookings', { params: { worker_id: user?.id, limit: 10 } });
      const items = response.data?.data?.items || response.data?.items || response.data || [];
      setJobs(Array.isArray(items) ? items : []);
    } catch (error) {
      console.error('Failed to load jobs', error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleStatusUpdate = async (bookingId: string, newStatus: string) => {
    try {
      await apiClient.put(`/api/v1/bookings/${bookingId}/status`, { status: newStatus });
      toast.success(`Booking status updated to ${newStatus}`);
      fetchJobs();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update status');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'REQUESTED': return <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100">New Request</Badge>;
      case 'ASSIGNED': return <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-100">Assigned</Badge>;
      case 'IN_PROGRESS': return <Badge variant="secondary" className="bg-purple-100 text-purple-800 hover:bg-purple-100">In Progress</Badge>;
      case 'COMPLETED': return <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">Completed</Badge>;
      case 'CANCELLED': return <Badge variant="destructive">Cancelled</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const activeJobs = jobs.filter(j => ['ASSIGNED', 'IN_PROGRESS'].includes(j.status));
  const newRequests = jobs.filter(j => j.status === 'REQUESTED');
  const pastJobs = jobs.filter(j => ['COMPLETED', 'CANCELLED'].includes(j.status));

  // Determine worker approval status
  const isApproved = user?.account_status === 'ACTIVE';

  if (!isApproved) {
    return (
      <div className="container mx-auto px-4 py-20 max-w-4xl text-center flex flex-col items-center">
        <div className="h-24 w-24 bg-amber-100 rounded-full flex items-center justify-center mb-6">
          <Clock className="h-12 w-12 text-amber-600" />
        </div>
        <h1 className="text-3xl font-bold mb-4">Account Pending Approval</h1>
        <p className="text-lg text-slate-600 max-w-xl">
          Your professional account is currently under review by our admin team. 
          We are verifying your KYC details and experience. This usually takes 24-48 hours.
        </p>
      </div>
    );
  }

  const renderJobCard = (job: any, isNewRequest: boolean, index: number = 0) => (
    <div 
      key={job.id} 
      className="animate-in slide-in-from-bottom-4 fade-in fill-mode-both"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <Card className="border-slate-200 shadow-sm overflow-hidden group hover:border-emerald-300 hover:shadow-md transition-all duration-300">
        <div className="bg-slate-50 px-6 py-4 border-b flex justify-between items-center transition-colors group-hover:bg-emerald-50/50">
          <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Booking #{job.id.substring(0,8)}</span>
          {getStatusBadge(job.status)}
        </div>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">{job.service_category}</h3>
              <div className="space-y-3 text-sm text-slate-600">
                <div className="flex items-center"><Calendar className="h-4 w-4 mr-3 text-emerald-500" /> <span className="font-medium text-slate-700">{format(new Date(job.preferred_date), 'MMMM d, yyyy')}</span></div>
                <div className="flex items-center"><Clock className="h-4 w-4 mr-3 text-emerald-500" /> <span className="font-medium text-slate-700">{format(new Date(job.preferred_date), 'h:mm a')}</span></div>
                <div className="flex items-start"><MapPin className="h-4 w-4 mr-3 mt-0.5 text-emerald-500 flex-shrink-0" /> <span className="text-slate-700 leading-snug">{job.address}</span></div>
              </div>
            </div>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <p className="text-xs text-slate-500 font-bold mb-2 uppercase tracking-wider">Problem Description</p>
              <p className="text-sm text-slate-700 leading-relaxed line-clamp-4">{job.problem_description}</p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="bg-white border-t p-5 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Payout Estimate</span>
            <span className="font-extrabold text-2xl text-emerald-700">
              ${job.estimated_price?.toFixed(2) || '--'}
            </span>
          </div>
          <div className="flex gap-3 w-full sm:w-auto">
            {isNewRequest ? (
              <>
                <Button variant="outline" size="lg" className="w-full sm:w-auto text-destructive border-destructive/20 hover:bg-destructive/10 hover:border-destructive/30" onClick={() => handleStatusUpdate(job.id, 'CANCELLED')}>
                  Decline
                </Button>
                <Button size="lg" className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 shadow-sm shadow-emerald-600/20" onClick={() => handleStatusUpdate(job.id, 'ASSIGNED')}>
                  Accept Job
                </Button>
              </>
            ) : job.status === 'ASSIGNED' ? (
              <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 shadow-sm shadow-blue-600/20" onClick={() => handleStatusUpdate(job.id, 'IN_PROGRESS')}>
                Start Job
              </Button>
            ) : job.status === 'IN_PROGRESS' ? (
              <Button size="lg" className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 shadow-sm shadow-emerald-600/20" onClick={() => handleStatusUpdate(job.id, 'COMPLETED')}>
                Mark Completed
              </Button>
            ) : (
               <Button variant="outline" size="lg" className="w-full sm:w-auto">View Details <ChevronRight className="h-4 w-4 ml-2" /></Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Worker Dashboard</h1>
        <p className="text-muted-foreground mt-1">Manage your jobs and availability.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="h-12 w-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center">
              <Briefcase className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Active Jobs</p>
              <p className="text-2xl font-bold">{activeJobs.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="h-12 w-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center">
              <Calendar className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">New Requests</p>
              <p className="text-2xl font-bold">{newRequests.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="h-12 w-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
              <DollarSign className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Completed Jobs</p>
              <p className="text-2xl font-bold">{pastJobs.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="bg-slate-100 p-1">
          <TabsTrigger value="active" className="rounded-lg">Active Jobs ({activeJobs.length})</TabsTrigger>
          <TabsTrigger value="requests" className="rounded-lg relative">
            New Requests
            {newRequests.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {newRequests.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" className="rounded-lg">History</TabsTrigger>
        </TabsList>
        
        <TabsContent value="active" className="space-y-6 mt-6">
          {isLoading ? (
             <div className="space-y-4">
               {[1,2].map(i => <Skeleton key={i} className="h-[240px] w-full rounded-2xl" />)}
             </div>
          ) : activeJobs.length > 0 ? (
            <div className="space-y-6">
              {activeJobs.map((job, idx) => renderJobCard(job, false, idx))}
            </div>
          ) : (
            <div className="text-center py-24 bg-slate-50 border border-dashed border-slate-300 rounded-2xl transition-all hover:bg-slate-100">
              <div className="h-20 w-20 bg-white rounded-full flex items-center justify-center mx-auto mb-5 shadow-sm border border-slate-100">
                <CheckCircle className="h-10 w-10 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">No active jobs</h3>
              <p className="text-slate-500 mt-2 max-w-sm mx-auto">You're all caught up! Check the requests tab for new jobs matching your skills.</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="requests" className="space-y-6 mt-6">
          {isLoading ? (
             <div className="space-y-4">
               {[1,2].map(i => <Skeleton key={i} className="h-[240px] w-full rounded-2xl" />)}
             </div>
          ) : newRequests.length > 0 ? (
            <div className="space-y-6">
              {newRequests.map((job, idx) => renderJobCard(job, true, idx))}
            </div>
          ) : (
            <div className="text-center py-24 bg-slate-50 border border-dashed border-slate-300 rounded-2xl transition-all hover:bg-slate-100">
              <div className="h-20 w-20 bg-white rounded-full flex items-center justify-center mx-auto mb-5 shadow-sm border border-slate-100">
                <Briefcase className="h-10 w-10 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">No new requests</h3>
              <p className="text-slate-500 mt-2 max-w-sm mx-auto">We will notify you instantly when new jobs match your service category and location.</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-6 mt-6">
          {isLoading ? (
             <div className="space-y-4">
               {[1,2].map(i => <Skeleton key={i} className="h-[240px] w-full rounded-2xl" />)}
             </div>
          ) : pastJobs.length > 0 ? (
            <div className="space-y-6">
              {pastJobs.map((job, idx) => renderJobCard(job, false, idx))}
            </div>
          ) : (
            <div className="text-center py-16 bg-slate-50 border border-dashed rounded-xl">
              <CheckCircle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-slate-700">No history</h3>
              <p className="text-slate-500 mt-1">Your completed and cancelled jobs will appear here.</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
