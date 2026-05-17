import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard', '/bookings', '/profile'];
const authRoutes = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const isAuthenticated = request.cookies.get('homeezy_auth')?.value === 'true';
  const userRole = request.cookies.get('homeezy_role')?.value;

  const isProtectedRoute = protectedRoutes.some((route) =>
    request.nextUrl.pathname.startsWith(route)
  );

  const isAuthRoute = authRoutes.some((route) =>
    request.nextUrl.pathname.startsWith(route)
  );

  // Redirect unauthenticated users from protected routes
  if (isProtectedRoute && !isAuthenticated) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect authenticated users from auth routes
  if (isAuthRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Role-based routing for dashboards
  if (isAuthenticated && request.nextUrl.pathname === '/dashboard') {
    if (userRole === 'customer') {
      return NextResponse.rewrite(new URL('/dashboard/customer', request.url));
    } else if (userRole === 'worker') {
      return NextResponse.rewrite(new URL('/dashboard/worker', request.url));
    } else if (userRole === 'admin') {
      return NextResponse.rewrite(new URL('/dashboard/admin', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
