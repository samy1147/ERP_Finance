import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/globals.css';
import CSRFInitializer from '@/components/CSRFInitializer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Finance ERP',
  description: 'Finance ERP System - GL, AR, AP Management',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CSRFInitializer />
        {children}
      </body>
    </html>
  );
}
