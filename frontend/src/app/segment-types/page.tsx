'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType } from '@/types/segment';

export default function SegmentTypesPage() {
  const router = useRouter();
  const [segmentTypes, setSegmentTypes] = useState<SegmentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSegmentTypes();
  }, []);

  const loadSegmentTypes = async () => {
    try {
      setLoading(true);
      const data = await segmentService.getSegmentTypes();
      setSegmentTypes(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load segment types');
      console.error('Error loading segment types:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this segment type?')) return;
    
    try {
      await segmentService.deleteSegmentType(id);
      await loadSegmentTypes();
    } catch (err: any) {
      alert('Error deleting segment type: ' + (err.message || 'Unknown error'));
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Segment Types</h1>
        <button
          onClick={() => router.push('/segment-types/new')}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          + New Segment Type
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Order
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Segment Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Properties
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {segmentTypes.map((st) => (
              <tr key={st.segment_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {st.display_order}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{st.segment_name}</div>
                  {st.description && (
                    <div className="text-sm text-gray-500">{st.description}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                    {st.segment_type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex gap-2">
                    {st.is_required && (
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">
                        Required
                      </span>
                    )}
                    {st.has_hierarchy && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                        Hierarchical
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded text-xs ${st.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {st.is_active ? '✓ Active' : '✗ Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => router.push(`/segments?type=${st.segment_id}`)}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                  >
                    View Values
                  </button>
                  <button
                    onClick={() => router.push(`/segment-types/${st.segment_id}/edit`)}
                    className="text-indigo-600 hover:text-indigo-900 mr-4"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(st.segment_id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {segmentTypes.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No segment types found. Create one to get started.
          </div>
        )}
      </div>
    </div>
  );
}
