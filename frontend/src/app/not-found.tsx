import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <h1 className="text-6xl font-bold text-slate-200">404</h1>
      <h2 className="text-2xl font-bold mt-4">Page not found</h2>
      <p className="text-muted-foreground mt-2 max-w-md">
        The page you are looking for does not exist or you do not have permission to view it.
      </p>
      <div className="flex gap-3 mt-8">
        <Button asChild>
          <Link href="/">Home</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/login">Sign in</Link>
        </Button>
      </div>
    </div>
  );
}
