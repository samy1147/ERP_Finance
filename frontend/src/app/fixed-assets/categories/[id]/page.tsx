'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface AssetCategory {
  id: number;
  code: string;
  name: string;
  description: string;
  major: string;
  minor: string;
  depreciation_method: string;
  useful_life_years: number;
  min_value: string;
  asset_account: number;
  asset_account_code: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_name: string;
}

export default function ViewCategoryPage() {
  const params = useParams();
  const router = useRouter();
  const [category, setCategory] = useState<AssetCategory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategory();
  }, []);

  const fetchCategory = async () => {
    try {
      const response = await fetch(`http://localhost:8007/api/fixed-assets/categories/${params.id}/`);
      if (response.ok) {
        const data = await response.json();
        setCategory(data);
      }
    } catch (error) {
      console.error('Error fetching category:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMethodLabel = (method: string) => {
    const methods: Record<string, string> = {
      'STRAIGHT_LINE': 'Straight Line',
      'DECLINING_BALANCE': 'Declining Balance',
      'SUM_OF_YEARS': 'Sum of Years Digits',
      'UNITS_OF_PRODUCTION': 'Units of Production'
    };
    return methods[method] || method;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!category) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Category Not Found</h1>
          <Link href="/fixed-assets/categories" className="text-blue-600 hover:underline">
            Back to Categories
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Asset Category Details</h1>
        <div className="flex gap-2">
          <Link
            href={`/fixed-assets/categories/${category.id}/edit`}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Edit
          </Link>
          <button
            onClick={() => router.push('/fixed-assets/categories')}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Back
          </button>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="grid grid-cols-2 gap-6">
          {/* Code */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Code</label>
            <p className="text-lg font-semibold">{category.code}</p>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Name</label>
            <p className="text-lg font-semibold">{category.name}</p>
          </div>

          {/* Description */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-500 mb-1">Description</label>
            <p className="text-gray-900">{category.description || '-'}</p>
          </div>

          {/* Major */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Major Category</label>
            <p className="text-gray-900">{category.major || '-'}</p>
          </div>

          {/* Minor */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Minor Category</label>
            <p className="text-gray-900">{category.minor || '-'}</p>
          </div>

          {/* Depreciation Method */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Depreciation Method</label>
            <p className="text-gray-900">{getMethodLabel(category.depreciation_method)}</p>
          </div>

          {/* Useful Life */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Useful Life</label>
            <p className="text-gray-900">{category.useful_life_years} years</p>
          </div>

          {/* Min Value */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Minimum Value</label>
            <p className="text-gray-900">{category.min_value ? Number(category.min_value).toFixed(2) : '0.00'}</p>
          </div>

          {/* Asset Account */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Asset Account</label>
            <p className="text-gray-900">{category.asset_account_code || '-'}</p>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Status</label>
            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
              category.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {category.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          {/* Created By */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Created By</label>
            <p className="text-gray-900">{category.created_by_name || '-'}</p>
          </div>

          {/* Created At */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Created At</label>
            <p className="text-gray-900">{new Date(category.created_at).toLocaleString()}</p>
          </div>

          {/* Updated At */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Updated At</label>
            <p className="text-gray-900">{new Date(category.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
