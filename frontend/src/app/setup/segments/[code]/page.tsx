'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType, Segment } from '@/types/segment';

export default function ViewSegmentPage() {
  const router = useRouter();
  const params = useParams();
  const code = params?.code as string;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [segment, setSegment] = useState<Segment | null>(null);
  const [segmentType, setSegmentType] = useState<SegmentType | null>(null);
  const [parent, setParent] = useState<Segment | null>(null);
  const [children, setChildren] = useState<Segment[]>([]);

  useEffect(() => {
    if (code) {
      loadData();
    }
  }, [code]);

  const loadData = async () => {
    try {
      setLoading(true);
      const segmentData = await segmentService.getSegment(code);
      setSegment(segmentData);
      
      // Load segment type
      const typeId = typeof segmentData.segment_type === 'object' 
        ? segmentData.segment_type.segment_id 
        : segmentData.segment_type;
      const typesData = await segmentService.getSegmentTypes();
      const type = typesData.find(t => t.segment_id === typeId);
      if (type) {
        setSegmentType(type);
      }
      
      // Load parent if exists
      if (segmentData.parent_code) {
        try {
          const parentData = await segmentService.getSegment(segmentData.parent_code);
          setParent(parentData);
        } catch (err) {
          console.error('Failed to load parent:', err);
        }
      }
      
      // Load children
      const allSegments = await segmentService.getSegments();
      const childSegments = allSegments.filter(s => s.parent_code === code);
      setChildren(childSegments);
      
      setError(null);
    } catch (err: any) {
      setError('Failed to load segment: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete segment "${code}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await segmentService.deleteSegment(code);
      router.push('/setup');
    } catch (err: any) {
      setError('Failed to delete segment: ' + (err.message || 'Unknown error'));
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

  if (error || !segment) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error || 'Segment not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
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
            <h1 className="text-3xl font-bold text-gray-900">{segment.alias}</h1>
            <p className="text-gray-600 mt-1">Code: {segment.code}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            segment.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {segment.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => router.push(`/setup/segments/${code}/edit`)}
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
      </div>

      {/* Details Card */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Details</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Code</label>
            <p className="mt-1 text-gray-900 font-mono">{segment.code}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Name/Alias</label>
            <p className="mt-1 text-gray-900">{segment.alias}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Segment Type</label>
            <p className="mt-1">
              {segmentType ? (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                  {segmentType.segment_name}
                </span>
              ) : (
                <span className="text-gray-500">-</span>
              )}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Level</label>
            <p className="mt-1 text-gray-900">{segment.level}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Node Type</label>
            <p className="mt-1">
              <span className={`px-2 py-1 rounded text-sm ${
                segment.node_type === 'parent' ? 'bg-purple-100 text-purple-800' :
                segment.node_type === 'sub_parent' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {segment.node_type === 'parent' ? 'Parent' :
                 segment.node_type === 'sub_parent' ? 'Sub-Parent' :
                 'Child'}
              </span>
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Parent Code</label>
            <p className="mt-1">
              {parent ? (
                <button
                  onClick={() => router.push(`/setup/segments/${parent.code}`)}
                  className="text-blue-600 hover:text-blue-800 font-mono"
                >
                  {parent.code} - {parent.alias}
                </button>
              ) : (
                <span className="text-gray-500">None (Root)</span>
              )}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Envelope Amount</label>
            <p className="mt-1 text-gray-900">{segment.envelope_amount || '-'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Status</label>
            <p className="mt-1">
              <span className={`px-2 py-1 rounded text-sm ${
                segment.is_active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {segment.is_active ? 'Active' : 'Inactive'}
              </span>
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Created At</label>
            <p className="mt-1 text-gray-900 text-sm">
              {new Date(segment.created_at).toLocaleString()}
            </p>
          </div>
          
          {segment.updated_at && (
            <div>
              <label className="block text-sm font-medium text-gray-500">Updated At</label>
              <p className="mt-1 text-gray-900 text-sm">
                {new Date(segment.updated_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>
        
        {segment.description && (
          <div className="mt-4 pt-4 border-t">
            <label className="block text-sm font-medium text-gray-500">Description</label>
            <p className="mt-1 text-gray-900">{segment.description}</p>
          </div>
        )}
      </div>

      {/* Children Section */}
      {segmentType?.has_hierarchy && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Child Segments ({children.length})
          </h2>
          {children.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
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
                  {children.map((child) => (
                    <tr key={child.code} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-mono font-medium text-gray-900">{child.code}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{child.alias}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {child.level}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded text-xs ${
                          child.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {child.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => router.push(`/setup/segments/${child.code}`)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No child segments found.</p>
          )}
        </div>
      )}
    </div>
  );
}
