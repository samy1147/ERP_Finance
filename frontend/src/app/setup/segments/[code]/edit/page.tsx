'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType, Segment } from '@/types/segment';

export default function EditSegmentPage() {
  const router = useRouter();
  const params = useParams();
  const code = params?.code as string;
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [segmentTypes, setSegmentTypes] = useState<SegmentType[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [originalSegment, setOriginalSegment] = useState<Segment | null>(null);

  const [formData, setFormData] = useState({
    code: '',
    alias: '',
    segment_type: '',
    parent_code: '',
    node_type: 'child' as 'parent' | 'sub_parent' | 'child',
    level: 0,
    envelope_amount: '',
    is_active: true,
    description: ''
  });

  useEffect(() => {
    if (code) {
      loadData();
    }
  }, [code]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      const [typesData, segmentsData, segmentData] = await Promise.all([
        segmentService.getSegmentTypes(),
        segmentService.getSegments(),
        segmentService.getSegment(code)
      ]);
      
      setSegmentTypes(typesData);
      setSegments(segmentsData.filter(s => s.code !== code)); // Exclude current segment from parent options
      setOriginalSegment(segmentData);
      
      // Populate form
      const segType = typeof segmentData.segment_type === 'object' 
        ? segmentData.segment_type.segment_id 
        : segmentData.segment_type;
      
      setFormData({
        code: segmentData.code,
        alias: segmentData.alias,
        segment_type: String(segType),
        parent_code: segmentData.parent_code || '',
        node_type: segmentData.node_type || 'child',
        level: segmentData.level,
        envelope_amount: segmentData.envelope_amount || '',
        is_active: segmentData.is_active,
        description: segmentData.description || ''
      });
      
      setError(null);
    } catch (err: any) {
      setError('Failed to load segment: ' + (err.message || 'Unknown error'));
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.alias.trim()) {
        throw new Error('Alias/Name is required');
      }
      if (!formData.segment_type) {
        throw new Error('Segment Type is required');
      }

      // Prepare data
      const submitData: any = {
        alias: formData.alias.trim(),
        segment_type: parseInt(formData.segment_type),
        node_type: formData.node_type,
        level: parseInt(String(formData.level)),
        is_active: formData.is_active
      };

      if (formData.parent_code) {
        submitData.parent_code = formData.parent_code;
      } else {
        submitData.parent_code = null;
      }

      if (formData.envelope_amount) {
        submitData.envelope_amount = formData.envelope_amount;
      }

      if (formData.description) {
        submitData.description = formData.description;
      }

      await segmentService.updateSegment(code, submitData);
      
      // Redirect back to setup page with the type selected
      router.push(`/setup?type=${formData.segment_type}`);
    } catch (err: any) {
      setError(err.message || 'Failed to update segment');
      console.error('Error updating segment:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete segment "${formData.code}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await segmentService.deleteSegment(code);
      router.push('/setup');
    } catch (err: any) {
      setError('Failed to delete segment: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };

  // Get available parent segments for selected type
  const getAvailableParents = () => {
    if (!formData.segment_type) return [];
    
    return segments.filter(s => {
      const segType = typeof s.segment_type === 'object' ? s.segment_type.segment_id : s.segment_type;
      return segType === parseInt(formData.segment_type);
    });
  };

  const selectedType = segmentTypes.find(t => t.segment_id === parseInt(formData.segment_type));

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!originalSegment) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">Segment not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-2">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">Edit Segment</h1>
        <p className="text-gray-600 mt-1">Update segment: {code}</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
        {/* Code (Read-only) */}
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
            Code
          </label>
          <input
            type="text"
            id="code"
            name="code"
            value={formData.code}
            readOnly
            disabled
            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
          />
          <p className="mt-1 text-sm text-gray-500">
            Code cannot be changed after creation
          </p>
        </div>

        {/* Segment Type (Read-only) */}
        <div>
          <label htmlFor="segment_type" className="block text-sm font-medium text-gray-700 mb-2">
            Segment Type
          </label>
          <select
            id="segment_type"
            name="segment_type"
            value={formData.segment_type}
            disabled
            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
          >
            {segmentTypes.map(type => (
              <option key={type.segment_id} value={type.segment_id}>
                {type.segment_name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-sm text-gray-500">
            Segment type cannot be changed after creation
          </p>
        </div>

        {/* Alias/Name */}
        <div>
          <label htmlFor="alias" className="block text-sm font-medium text-gray-700 mb-2">
            Name/Alias <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="alias"
            name="alias"
            value={formData.alias}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter descriptive name"
          />
        </div>

        {/* Parent (if hierarchical) */}
        {selectedType?.has_hierarchy && (
          <div>
            <label htmlFor="parent_code" className="block text-sm font-medium text-gray-700 mb-2">
              Parent Segment
            </label>
            <select
              id="parent_code"
              name="parent_code"
              value={formData.parent_code}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">None (Root Level)</option>
              {getAvailableParents().map(segment => (
                <option key={segment.code} value={segment.code}>
                  {segment.code} - {segment.alias}
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Select a parent segment to create a hierarchical structure
            </p>
          </div>
        )}

        {/* Node Type */}
        <div>
          <label htmlFor="node_type" className="block text-sm font-medium text-gray-700 mb-2">
            Node Type <span className="text-red-500">*</span>
          </label>
          <select
            id="node_type"
            name="node_type"
            value={formData.node_type}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="parent">Parent (Root Level)</option>
            <option value="sub_parent">Sub-Parent (Intermediate)</option>
            <option value="child">Child (Leaf Node)</option>
          </select>
          <p className="mt-1 text-sm text-gray-500">
            Parent: can have children • Sub-Parent: has parent and children • Child: has parent only
          </p>
        </div>

        {/* Level */}
        <div>
          <label htmlFor="level" className="block text-sm font-medium text-gray-700 mb-2">
            Level
          </label>
          <input
            type="number"
            id="level"
            name="level"
            value={formData.level}
            onChange={handleChange}
            min="0"
            max="9"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-sm text-gray-500">
            Hierarchy level (0 = root, higher numbers = deeper levels)
          </p>
        </div>

        {/* Envelope Amount */}
        <div>
          <label htmlFor="envelope_amount" className="block text-sm font-medium text-gray-700 mb-2">
            Envelope Amount
          </label>
          <input
            type="text"
            id="envelope_amount"
            name="envelope_amount"
            value={formData.envelope_amount}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
          <p className="mt-1 text-sm text-gray-500">
            Optional budget/envelope amount for this segment
          </p>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Optional description"
          />
        </div>

        {/* Active Status */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            name="is_active"
            checked={formData.is_active}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
            Active
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-4 border-t">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={loading}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Delete
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            disabled={loading}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
