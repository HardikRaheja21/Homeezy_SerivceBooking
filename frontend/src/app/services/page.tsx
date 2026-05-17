'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Search, Loader2 } from 'lucide-react';

import { apiClient } from '@/lib/api/client';
import { ServiceCategory } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

function ServicesContent() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get('category') || '';
  
  const [services, setServices] = useState<ServiceCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(initialCategory);

  useEffect(() => {
    async function fetchServices() {
      try {
        setIsLoading(true);
        const response = await apiClient.get('/api/v1/services');
        const data = response.data?.data?.items || response.data?.items || response.data || [];
        setServices(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Failed to fetch services', error);
        setServices([]);
      } finally {
        setIsLoading(false);
      }
    }
    fetchServices();
  }, []);

  const filteredServices = services.filter((service) => 
    service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    service.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto px-4 py-10 min-h-screen">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Our Services</h1>
          <p className="text-muted-foreground mt-1">Find the right professional for your home.</p>
        </div>
        
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search services (e.g. Plumbing, Cleaning)..." 
            className="pl-9 bg-white"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden">
              <Skeleton className="h-40 w-full rounded-none" />
              <CardContent className="p-6">
                <Skeleton className="h-6 w-2/3 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-4/5" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredServices.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredServices.map((service) => (
            <Card key={service.id} className="flex flex-col border-slate-200 hover:border-emerald-200 hover:shadow-md transition-all bg-white">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-xl flex items-center gap-2">
                    <span className="text-2xl bg-slate-100 p-2 rounded-xl">{service.icon || '🛠️'}</span>
                    {service.name}
                  </CardTitle>
                </div>
                <CardDescription className="mt-2 line-clamp-2">
                  {service.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="flex flex-wrap gap-2 mb-4">
                  {service.skills?.slice(0, 3).map((skill) => (
                    <span key={skill} className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-full font-medium">
                      {skill}
                    </span>
                  ))}
                  {(service.skills?.length || 0) > 3 && (
                    <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-full font-medium">
                      +{service.skills.length - 3} more
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-sm font-medium text-emerald-600">
                  <span>Starts at ${service.base_price.toFixed(2)}</span>
                </div>
              </CardContent>
              <CardFooter className="border-t bg-slate-50 p-4">
                <Button className="w-full rounded-xl" asChild>
                  <Link href={`/bookings/new?service=${service.slug}`}>
                    Book Now
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
          <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold">No services found</h3>
          <p className="text-muted-foreground mt-1">Try adjusting your search query.</p>
          <Button 
            variant="outline" 
            className="mt-6 rounded-xl" 
            onClick={() => setSearchQuery('')}
          >
            Clear Search
          </Button>
        </div>
      )}
    </div>
  );
}

export default function ServicesPage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    }>
      <ServicesContent />
    </Suspense>
  );
}
