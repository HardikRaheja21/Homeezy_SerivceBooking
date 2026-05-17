'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api/client';

const workerSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  phone: z.string().min(10, 'Please enter a valid phone number'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Must contain at least one special character'),
  city: z.string().min(2, 'City is required'),
  area: z.string().min(2, 'Area is required'),
  pincode: z.string().min(5, 'Pincode is required'),
  service_category: z.string().min(2, 'Service category is required'),
  skills: z.string().min(2, 'Please enter at least one skill'),
  experience_years: z.coerce.number().min(0, 'Must be a positive number'),
  government_id_type: z.string().min(2, 'ID type is required'),
  government_id_number: z.string().min(5, 'ID number is required'),
  base_charge_per_hour: z.coerce.number().min(1, 'Charge must be greater than 0'),
});

type WorkerFormValues = z.infer<typeof workerSchema>;

export default function RegisterWorkerPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<WorkerFormValues>({
    resolver: zodResolver(workerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      phone: '',
      password: '',
      city: '',
      area: '',
      pincode: '',
      service_category: '',
      skills: '',
      experience_years: 0,
      government_id_type: '',
      government_id_number: '',
      base_charge_per_hour: 0,
    },
  });

  async function onSubmit(data: WorkerFormValues) {
    setIsLoading(true);
    try {
      const payload = {
        ...data,
        skills: data.skills.split(',').map((s) => s.trim()).filter(Boolean),
        bank_name: 'Pending',
        account_number: '0000000000',
        ifsc_code: 'PEND000000',
        emergency_contact_name: 'Pending',
        emergency_contact_phone: '0000000000',
      };

      await apiClient.post('/api/v1/auth/register/worker', payload);
      toast.success('Registration successful! Please wait for admin approval before logging in.', {
        duration: 8000,
      });
      
      // Redirect to login page
      router.push('/login');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4 py-10">
      <Card className="w-full max-w-2xl shadow-lg border-muted">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight">Join as a Professional</CardTitle>
          <CardDescription>
            Register to become a verified Homeezy service partner
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              
              <div className="space-y-4">
                <h3 className="text-lg font-semibold border-b pb-2">Personal Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField control={form.control} name="full_name" render={({ field }) => (
                    <FormItem><FormLabel>Full Name</FormLabel><FormControl><Input placeholder="John Doe" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="phone" render={({ field }) => (
                    <FormItem><FormLabel>Phone Number</FormLabel><FormControl><Input placeholder="+1234567890" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="email" render={({ field }) => (
                    <FormItem><FormLabel>Email</FormLabel><FormControl><Input placeholder="you@example.com" type="email" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="password" render={({ field }) => (
                    <FormItem><FormLabel>Password</FormLabel><FormControl><Input placeholder="••••••••" type="password" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold border-b pb-2">Location</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <FormField control={form.control} name="city" render={({ field }) => (
                    <FormItem><FormLabel>City</FormLabel><FormControl><Input placeholder="New York" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="area" render={({ field }) => (
                    <FormItem><FormLabel>Area</FormLabel><FormControl><Input placeholder="Downtown" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="pincode" render={({ field }) => (
                    <FormItem><FormLabel>Pincode</FormLabel><FormControl><Input placeholder="10001" disabled={isLoading} {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold border-b pb-2">Professional Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField control={form.control} name="service_category" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Service Category</FormLabel>
                      <FormControl><Input placeholder="e.g. Plumbing, Cleaning" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="experience_years" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Experience (Years)</FormLabel>
                      <FormControl><Input type="number" min="0" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="skills" render={({ field }) => (
                    <FormItem className="md:col-span-2">
                      <FormLabel>Skills (Comma separated)</FormLabel>
                      <FormControl><Input placeholder="Pipe repair, Leak fixing, AC Gas Refill" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="base_charge_per_hour" render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base Charge / Hour ($)</FormLabel>
                      <FormControl><Input type="number" min="1" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold border-b pb-2">Identity Verification</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField control={form.control} name="government_id_type" render={({ field }) => (
                    <FormItem>
                      <FormLabel>ID Type</FormLabel>
                      <FormControl><Input placeholder="Passport, Driver License" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                  <FormField control={form.control} name="government_id_number" render={({ field }) => (
                    <FormItem>
                      <FormLabel>ID Number</FormLabel>
                      <FormControl><Input placeholder="A12345678" disabled={isLoading} {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                </div>
              </div>

              <Button type="submit" className="w-full mt-6" size="lg" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting Application...
                  </>
                ) : (
                  'Submit Application'
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center border-t p-6">
          <div className="text-sm text-muted-foreground">
            Already a partner?{' '}
            <Link href="/login" className="text-primary font-medium hover:underline">
              Sign in
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
