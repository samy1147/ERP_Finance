'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType } from '@/types/segment';

export default function EditSegmentTypePage() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id ? parseInt(params.id as string) : null;
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [originalType, setOriginalType] = useState<SegmentType | null>(null);

  const [formData, setFormData] = useState({
    segment_id: '',
    segment_name: '',
    segment_type: '',
        is_required: false,
    has_hierarchy: false,
    length: '50',
    display_order: '0',
    description: '',
    is_active: true
  });

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      const types = await segmentService.getSegmentTypes();
      const type = types.find(t => t.segment_id === id);
      
      if (!type) {
        throw new Error('Segment type not found');
      }
      
      setOriginalType(type);
      
      // Populate form
      setFormData({
        segment_id: String(type.segment_id),
        segment_name: type.segment_name,
        segment_type: type.segment_type,
        is_required: type.is_required,
        has_hierarchy: type.has_hierarchy,
        length: String(type.length),
        display_order: String(type.display_order),
        description: type.description || '',
        is_active: type.is_active
      });
      
      setError(null);
    } catch (err: any) {
      setError('Failed to load segment type: ' + (err.message || 'Unknown error'));
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!id) {
        throw new Error('Invalid segment type ID');
      }

      // Validate required fields
      if (!formData.segment_name.trim()) {
        throw new Error('Segment Name is required');
      }
      if (!formData.segment_type.trim()) {
        throw new Error('Segment Type is required');
      }
      // Prepare data
      const submitData: any = {
        segment_name: formData.segment_name.trim(),
        segment_type: formData.segment_type.trim(),
        is_required: formData.is_required,
        has_hierarchy: formData.has_hierarchy,
        length: parseInt(formData.length),
        display_order: parseInt(formData.display_order),
        is_active: formData.is_active
      };

      if (formData.description.trim()) {
        submitData.description = formData.description.trim();
      }

      await segmentService.updateSegmentType(id, submitData);
      
      // Redirect back to setup page
      router.push('/setup');
    } catch (err: any) {
      setError(err.message || 'Failed to update segment type');
      console.error('Error updating segment type:', err);
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
    if (!id) return;
    
    if (!confirm(`Are you sure you want to delete segment type "${formData.segment_name}"? All associated segments will also be deleted. This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await segmentService.deleteSegmentType(id);
      router.push('/setup');
    } catch (err: any) {
      setError('Failed to delete segment type: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };

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

  if (!originalType) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">Segment type not found</p>
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
        <h1 className="text-3xl font-bold text-gray-900">Edit Segment Type</h1>
        <p className="text-gray-600 mt-1">Update segment type: {originalType.segment_name}</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
        {/* Segment ID (Read-only) */}
        <div>
          <label htmlFor="segment_id" className="block text-sm font-medium text-gray-700 mb-2">
            Segment ID
          </label>
          <input
            type="text"
            id="segment_id"
            name="segment_id"
            value={formData.segment_id}
            readOnly
            disabled
            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
          />
          <p className="mt-1 text-sm text-gray-500">
            Segment ID cannot be changed after creation
          </p>
        </div>

        {/* Segment Name */}
        <div>
          <label htmlFor="segment_name" className="block text-sm font-medium text-gray-700 mb-2">
            Segment Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="segment_name"
            name="segment_name"
            value={formData.segment_name}
            onChange={handleChange}
            required
            maxLength={50}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter display name"
          />
        </div>

        {/* Segment Type (Technical) */}
        <div>
          <label htmlFor="segment_type" className="block text-sm font-medium text-gray-700 mb-2">
            Technical Type <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="segment_type"
            name="segment_type"
            value={formData.segment_type}
            onChange={handleChange}
            required
            maxLength={50}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter technical type"
          />
        </div>

        {/* Oracle Segment Number */}
        {/* Max Length */}
        <div>
          <label htmlFor="length" className="block text-sm font-medium text-gray-700 mb-2">
            Fixed Code Length
          </label>
          <input
            type="number"
            id="length"
            name="length"
            value={formData.length}
            onChange={handleChange}
            min="1"
            max="150"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Display Order */}
        <div>
          <label htmlFor="display_order" className="block text-sm font-medium text-gray-700 mb-2">
            Display Order
          </label>
          <input
            type="number"
            id="display_order"
            name="display_order"
            value={formData.display_order}
            onChange={handleChange}
            min="0"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
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

        {/* Checkboxes */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_required"
              name="is_required"
              checked={formData.is_required}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_required" className="ml-2 block text-sm text-gray-700">
              <span className="font-medium">Required</span>
              <span className="text-gray-500 ml-1">- Must be provided in all transactions</span>
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="has_hierarchy"
              name="has_hierarchy"
              checked={formData.has_hierarchy}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="has_hierarchy" className="ml-2 block text-sm text-gray-700">
              <span className="font-medium">Hierarchical</span>
              <span className="text-gray-500 ml-1">- Supports parent-child relationships</span>
            </label>
          </div>

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
              <span className="font-medium">Active</span>
            </label>
          </div>
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
