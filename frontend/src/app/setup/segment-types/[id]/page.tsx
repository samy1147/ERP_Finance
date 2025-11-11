'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType, Segment } from '@/types/segment';

export default function ViewSegmentTypePage() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id ? parseInt(params.id as string) : null;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [segmentType, setSegmentType] = useState<SegmentType | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load segment type
      const types = await segmentService.getSegmentTypes();
      const type = types.find(t => t.segment_id === id);
      
      if (!type) {
        throw new Error('Segment type not found');
      }
      
      setSegmentType(type);
      
      // Load all segments for this type
      const allSegments = await segmentService.getSegments();
      const typeSegments = allSegments.filter(s => {
        const segType = typeof s.segment_type === 'object' ? s.segment_type.segment_id : s.segment_type;
        return segType === id;
      });
      setSegments(typeSegments);
      
      setError(null);
    } catch (err: any) {
      setError('Failed to load segment type: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !segmentType) return;
    
    if (!confirm(`Are you sure you want to delete segment type "${segmentType.segment_name}"? All ${segments.length} associated segments will also be deleted. This action cannot be undone.`)) {
      return;
    }

    try {
      await segmentService.deleteSegmentType(id);
      router.push('/setup');
    } catch (err: any) {
      setError('Failed to delete segment type: ' + (err.message || 'Unknown error'));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !segmentType) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error || 'Segment type not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-2">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
        </div>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{segmentType.segment_name}</h1>
            <p className="text-gray-600 mt-1">
              Type: {segmentType.segment_type}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            segmentType.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {segmentType.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => router.push(`/setup/segment-types/${id}/edit`)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Edit
        </button>
        <button
          onClick={handleDelete}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
        >
          Delete
        </button>
        <button
          onClick={() => router.push(`/setup/segments/new?type=${id}`)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
        >
          + Add Segment Value
        </button>
      </div>

      {/* Details Card */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Details</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Segment ID</label>
            <p className="mt-1 text-gray-900 font-mono">{segmentType.segment_id}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Segment Name</label>
            <p className="mt-1 text-gray-900">{segmentType.segment_name}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Technical Type</label>
            <p className="mt-1 text-gray-900 font-mono">{segmentType.segment_type}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Fixed Code Length</label>
            <p className="mt-1 text-gray-900">{segmentType.length}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Display Order</label>
            <p className="mt-1 text-gray-900">{segmentType.display_order}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Properties</label>
            <div className="mt-1 flex gap-2">
              {segmentType.is_required && (
                <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Required</span>
              )}
              {segmentType.has_hierarchy && (
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Hierarchical</span>
              )}
              {!segmentType.is_required && !segmentType.has_hierarchy && (
                <span className="text-gray-500">None</span>
              )}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Created At</label>
            <p className="mt-1 text-gray-900 text-sm">
              {new Date(segmentType.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        
        {segmentType.description && (
          <div className="mt-4 pt-4 border-t">
            <label className="block text-sm font-medium text-gray-500">Description</label>
            <p className="mt-1 text-gray-900">{segmentType.description}</p>
          </div>
        )}
      </div>

      {/* Segment Values Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Segment Values ({segments.length})
          </h2>
          <button
            onClick={() => router.push(`/setup/segments/new?type=${id}`)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
          >
            + Add Value
          </button>
        </div>
        
        {segments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name/Alias
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Level
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
                {segments.map((segment) => (
                  <tr key={segment.code} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono font-medium text-gray-900">{segment.code}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{segment.alias}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {segment.parent_code || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {segment.level}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs ${
                        segment.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {segment.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/setup/segments/${segment.code}`)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        View
                      </button>
                      <button
                        onClick={() => router.push(`/setup/segments/${segment.code}/edit`)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            No segment values found. Click "Add Value" to create one.
          </p>
        )}
      </div>
    </div>
  );
}
