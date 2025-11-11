'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import segmentService from '@/services/segmentService';

export default function NewSegmentTypePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.segment_id.trim()) {
        throw new Error('Segment ID is required');
      }
      if (!formData.segment_name.trim()) {
        throw new Error('Segment Name is required');
      }
      if (!formData.segment_type.trim()) {
        throw new Error('Segment Type is required');
      }
      // Prepare data
      const submitData: any = {
        segment_id: parseInt(formData.segment_id),
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

      await segmentService.createSegmentType(submitData);
      
      // Redirect back to setup page
      router.push('/setup');
    } catch (err: any) {
      setError(err.message || 'Failed to create segment type');
      console.error('Error creating segment type:', err);
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
        <h1 className="text-3xl font-bold text-gray-900">Create New Segment Type</h1>
        <p className="text-gray-600 mt-1">Define a new segment type for your GL structure</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
        {/* Segment ID */}
        <div>
          <label htmlFor="segment_id" className="block text-sm font-medium text-gray-700 mb-2">
            Segment ID <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="segment_id"
            name="segment_id"
            value={formData.segment_id}
            onChange={handleChange}
            required
            min="1"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter unique segment ID (e.g., 1, 2, 3)"
          />
          <p className="mt-1 text-sm text-gray-500">
            Unique identifier for this segment type
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
            placeholder="Enter display name (e.g., 'Account', 'Cost Center', 'Project')"
          />
          <p className="mt-1 text-sm text-gray-500">
            Display name shown in the UI
          </p>
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
            placeholder="Enter technical type (e.g., 'account', 'cost_center', 'project')"
          />
          <p className="mt-1 text-sm text-gray-500">
            Technical identifier (lowercase, underscores allowed)
          </p>
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
          <p className="mt-1 text-sm text-gray-500">
            Fixed length for segment codes (default: 50)
          </p>
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
          <p className="mt-1 text-sm text-gray-500">
            Order for displaying in UI (lower numbers appear first)
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
            placeholder="Optional description of what this segment represents"
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
              <span className="text-gray-500 ml-1">- Currently available for use</span>
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
            {loading ? 'Creating...' : 'Create Segment Type'}
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

