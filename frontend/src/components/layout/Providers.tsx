'use client';

import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAppStore } from '../../store/useAppStore';
import { AuthModal } from '../auth/AuthModal';

function AuthInitializer({ children }: { children: React.ReactNode }) {
  const loadAuthFromStorage = useAppStore((s) => s.loadAuthFromStorage);

  useEffect(() => {
    loadAuthFromStorage();
  }, [loadAuthFromStorage]);

  return <>{children}</>;
}

function ThemeInitializer({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const saved = localStorage.getItem('vyron_theme');
    const theme = saved === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
  }, []);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 5000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeInitializer>
        <AuthInitializer>
          {children}
          <AuthModal />
        </AuthInitializer>
      </ThemeInitializer>
    </QueryClientProvider>
  );
}
