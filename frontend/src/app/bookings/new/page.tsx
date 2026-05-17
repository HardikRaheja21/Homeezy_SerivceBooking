'use client';

import { useState, useEffect, Suspense } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Loader2, ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/store/useAuth';
import { cn } from '@/lib/utils';

const bookingSchema = z.object({
  service_category: z.string().min(2, 'Service is required'),
  address: z.string().min(5, 'Address is required'),
  problem_description: z.string().min(10, 'Please describe the problem in more detail'),
  preferred_date: z.date({
    required_error: "A date is required.",
  }),
  preferred_time: z.string().min(1, 'Time is required'),
});

type BookingFormValues = z.infer<typeof bookingSchema>;

const TIME_SLOTS = [
  '09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM',
  '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM', '06:00 PM'
];

function BookingForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuth();
  
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [services, setServices] = useState<any[]>([]);

  const form = useForm<BookingFormValues>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      service_category: searchParams.get('service') || '',
      address: '',
      problem_description: '',
      preferred_time: '',
    },
  });

  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please log in to book a service');
      router.push(`/login?redirect=/bookings/new?service=${searchParams.get('service')}`);
    }

    async function fetchServices() {
      try {
        const response = await apiClient.get('/api/v1/services');
        const data = response.data?.data?.items || response.data?.items || response.data || [];
        setServices(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Failed to fetch services', error);
      }
    }
    fetchServices();
  }, [isAuthenticated, router, searchParams]);

  async function onSubmit(data: BookingFormValues) {
    if (step < 3) {
      // Move to next step if validation passes
      const fieldsToValidate = step === 1 
        ? ['service_category', 'address', 'problem_description'] 
        : ['preferred_date', 'preferred_time'];
        
      const isValid = await form.trigger(fieldsToValidate as any);
      if (isValid) setStep(step + 1);
      return;
    }

    // Final Submit
    setIsLoading(true);
    try {
      // Parse time and date
      const timeStr = data.preferred_time;
      let [time, modifier] = timeStr.split(' ');
      let [hours, minutes] = time.split(':');
      if (hours === '12') hours = '00';
      if (modifier === 'PM') hours = String(parseInt(hours, 10) + 12);
      
      const targetDate = new Date(data.preferred_date);
      targetDate.setHours(parseInt(hours, 10));
      targetDate.setMinutes(parseInt(minutes, 10));

      const payload = {
        service_category: data.service_category,
        address: data.address,
        problem_description: data.problem_description,
        preferred_date: targetDate.toISOString(),
      };

      await apiClient.post('/api/v1/bookings', payload);
      toast.success('Booking created successfully!');
      router.push('/dashboard/customer');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create booking');
    } finally {
      setIsLoading(false);
    }
  }

  const currentService = services.find(s => s.slug === form.watch('service_category') || s.name === form.watch('service_category'));

    <div className="w-full max-w-3xl mx-auto">
      {/* Premium Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Book a Professional</h1>
        <p className="text-slate-500 mt-2">Secure your appointment in just a few steps.</p>
      </div>

      {/* Progress Steps */}
      <div className="flex justify-between items-center mb-8 relative px-4">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-100 -z-10 rounded-full" />
        <div 
          className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-emerald-500 -z-10 rounded-full transition-all duration-500 ease-out" 
          style={{ width: `${((step - 1) / 2) * 100}%` }}
        />
        
        {[1, 2, 3].map((s) => (
          <div key={s} className={`flex flex-col items-center gap-2 bg-white px-2 transition-all duration-300 ${step >= s ? 'text-emerald-600' : 'text-slate-400'}`}>
            <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-colors duration-300 ${
              step > s ? 'bg-emerald-500 border-emerald-500 text-white' : 
              step === s ? 'border-emerald-500 bg-white text-emerald-600' : 
              'border-slate-200 bg-white text-slate-400'
            }`}>
              {step > s ? <CheckCircle2 className="h-4 w-4" /> : s}
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider hidden sm:block">
              {s === 1 ? 'Details' : s === 2 ? 'Schedule' : 'Confirm'}
            </span>
          </div>
        ))}
      </div>

      <Card className="w-full shadow-xl shadow-slate-200/40 border-slate-200/60 rounded-3xl overflow-hidden">
        <div className="bg-slate-50/50 p-6 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-800">
            {step === 1 ? 'Service Details' : step === 2 ? 'Date & Time' : 'Review & Confirm'}
          </h2>
          <span className="text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">Step {step} of 3</span>
        </div>
        
        <CardContent className="p-6 sm:p-8">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            
            {/* STEP 1: Details */}
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                <FormField
                  control={form.control}
                  name="service_category"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Select Service</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a service category" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {services.map((s) => (
                            <SelectItem key={s.id || s.slug} value={s.slug || s.name}>
                              {s.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="address"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Service Address</FormLabel>
                      <FormControl>
                        <Input placeholder="123 Main St, Apt 4B, New York, NY 10001" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="problem_description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Problem Description</FormLabel>
                      <FormControl>
                        <Textarea 
                          placeholder="Please describe what needs to be fixed..." 
                          className="min-h-[100px]"
                          {...field} 
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* STEP 2: Schedule */}
            {step === 2 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <FormField
                  control={form.control}
                  name="preferred_date"
                  render={({ field }) => (
                    <FormItem className="flex flex-col">
                      <FormLabel>Select Date</FormLabel>
                      <Popover>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant={"outline"}
                              className={cn(
                                "w-[240px] pl-3 text-left font-normal",
                                !field.value && "text-muted-foreground"
                              )}
                            >
                              {field.value ? (
                                format(field.value, "PPP")
                              ) : (
                                <span>Pick a date</span>
                              )}
                              <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={field.value}
                            onSelect={field.onChange}
                            disabled={(date) =>
                              date < new Date(new Date().setHours(0, 0, 0, 0))
                            }
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="preferred_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Select Time Slot</FormLabel>
                      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                        {TIME_SLOTS.map((time) => (
                          <div
                            key={time}
                            onClick={() => field.onChange(time)}
                            className={cn(
                              "cursor-pointer rounded-xl border text-center p-2 text-sm transition-all hover:border-emerald-500",
                              field.value === time 
                                ? "bg-emerald-50 border-emerald-500 text-emerald-700 font-medium" 
                                : "bg-white text-slate-600"
                            )}
                          >
                            {time}
                          </div>
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* STEP 3: Confirm */}
            {step === 3 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                  <h3 className="font-semibold text-lg mb-4 flex items-center">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500 mr-2" />
                    Booking Summary
                  </h3>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-slate-200 pb-2">
                      <span className="text-slate-500">Service</span>
                      <span className="font-medium text-slate-900">{currentService?.name || form.getValues('service_category')}</span>
                    </div>
                    <div className="flex justify-between border-b border-slate-200 pb-2">
                      <span className="text-slate-500">Base Price</span>
                      <span className="font-medium text-slate-900">${currentService?.base_price?.toFixed(2) || '--'}</span>
                    </div>
                    <div className="flex justify-between border-b border-slate-200 pb-2">
                      <span className="text-slate-500">Schedule</span>
                      <span className="font-medium text-slate-900">
                        {form.getValues('preferred_date') ? format(form.getValues('preferred_date'), 'PPP') : ''} at {form.getValues('preferred_time')}
                      </span>
                    </div>
                    <div className="flex flex-col border-b border-slate-200 pb-2">
                      <span className="text-slate-500 mb-1">Address</span>
                      <span className="font-medium text-slate-900">{form.getValues('address')}</span>
                    </div>
                    <div className="flex flex-col pb-2">
                      <span className="text-slate-500 mb-1">Problem</span>
                      <span className="font-medium text-slate-900">{form.getValues('problem_description')}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-50 text-amber-800 p-4 rounded-xl text-sm">
                  <strong>Note:</strong> The final price will be determined by the professional after inspection. You will only be charged a base visit fee if you decline the final quote.
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4 border-t border-slate-100">
              {step > 1 ? (
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setStep(step - 1)}
                  disabled={isLoading}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back
                </Button>
              ) : (
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => router.back()}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
              )}

              <Button type="submit" size="lg" disabled={isLoading} className={`rounded-xl shadow-sm ${step === 3 ? "bg-emerald-600 hover:bg-emerald-700 w-full sm:w-auto px-8" : "w-full sm:w-auto px-8"}`}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : step < 3 ? (
                  <>
                    Continue <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                ) : (
                  'Confirm Booking'
                )}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
    </div>
  );
}

export default function NewBookingPage() {
  return (
    <div className="container mx-auto px-4 py-10 min-h-[80vh] flex flex-col justify-center">
      <Suspense fallback={<div className="flex justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}>
        <BookingForm />
      </Suspense>
    </div>
  );
}
