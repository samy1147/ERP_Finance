'use client';

import { useEffect } from 'react';
import { initCsrfToken } from '@/lib/api';

export default function CSRFInitializer() {
  useEffect(() => {
    // Initialize CSRF token when the app loads
    initCsrfToken();
  }, []);

  return null; // This component doesn't render anything
}
