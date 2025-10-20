'use client';

import React, { useState, useEffect } from 'react';
import { accountsAPI } from '../../services/api';

export default function TestAPIPage() {
  const [status, setStatus] = useState('Testing connection...');
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    testConnection();
  }, []);

  const testConnection = async () => {
    try {
      setStatus('Attempting to connect to backend...');
      console.log('API Base URL:', process.env.NEXT_PUBLIC_API_URL);
      
      const response = await accountsAPI.list();
      setStatus('✅ Connection successful!');
      setData(response.data);
      console.log('Response:', response.data);
    } catch (err: any) {
      setStatus('❌ Connection failed');
      setError({
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        config: {
          url: err.config?.url,
          baseURL: err.config?.baseURL,
          method: err.config?.method,
        }
      });
      console.error('Error details:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">API Connection Test</h1>
      
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
        <p className="text-lg mb-4">{status}</p>
        
        <div className="bg-gray-100 p-4 rounded">
          <p className="font-mono text-sm mb-2">
            <strong>API URL:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}
          </p>
          <p className="font-mono text-sm">
            <strong>Testing endpoint:</strong> /accounts/
          </p>
        </div>
      </div>

      {error && (
        <div className="card bg-red-50 border-red-200 mb-6">
          <h2 className="text-xl font-semibold text-red-800 mb-4">Error Details</h2>
          <pre className="bg-white p-4 rounded border overflow-auto text-sm">
            {JSON.stringify(error, null, 2)}
          </pre>
        </div>
      )}

      {data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-xl font-semibold text-green-800 mb-4">Success! Data Received</h2>
          <p className="mb-2">Found {Array.isArray(data) ? data.length : 0} accounts</p>
          <pre className="bg-white p-4 rounded border overflow-auto text-sm max-h-96">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      <div className="mt-6">
        <button onClick={testConnection} className="btn-primary">
          Test Again
        </button>
      </div>
    </div>
  );
}
