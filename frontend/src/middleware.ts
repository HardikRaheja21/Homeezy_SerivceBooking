import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard', '/bookings', '/profile'];
const authRoutes = ['/login', '/register', '/verify'];

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

  // Role-based access for dashboard sub-routes
  if (isAuthenticated && request.nextUrl.pathname.startsWith('/dashboard/')) {
    const segment = request.nextUrl.pathname.split('/')[2];
    if (segment && segment !== userRole && segment !== 'page') {
      return NextResponse.redirect(new URL(`/dashboard/${userRole || 'customer'}`, request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
