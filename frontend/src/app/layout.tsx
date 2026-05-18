import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/sonner';
import { Navbar } from '@/components/layout/Navbar';
import { ChatWidget } from '@/components/layout/ChatWidget';
import { AuthProvider } from '@/components/providers/AuthProvider';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: {
    default: 'Homeezy | Premium Home Services On-Demand',
    template: '%s | Homeezy',
  },
  description: 'Book verified plumbers, electricians, and cleaners instantly. Homeezy is the modern marketplace for real-time home service tracking and AI-assisted troubleshooting.',
  keywords: ['home services', 'plumber', 'electrician', 'cleaning', 'marketplace', 'on-demand services'],
  authors: [{ name: 'Homeezy Team' }],
  creator: 'Homeezy',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://homeezy.com',
    title: 'Homeezy | Premium Home Services On-Demand',
    description: 'Book verified professionals instantly with real-time tracking and AI assistance.',
    siteName: 'Homeezy',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Homeezy - The Future of Home Services',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Homeezy | Premium Home Services On-Demand',
    description: 'Book verified professionals instantly with real-time tracking and AI assistance.',
    images: ['/og-image.jpg'],
    creator: '@homeezy',
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} font-sans h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Navbar />
        <AuthProvider>
          <main className="flex-1 flex flex-col">{children}</main>
          <ChatWidget />
        </AuthProvider>
        <Toaster position="top-center" richColors />
      </body>
    </html>
  );
}
