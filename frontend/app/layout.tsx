import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from './providers';
import { TranslationProvider } from '@/contexts/TranslationContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Funding Intelligence',
  description: 'AI-powered bidirectional matching platform for founders and investors',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <TranslationProvider>
            {children}
          </TranslationProvider>
        </Providers>
      </body>
    </html>
  );
}
