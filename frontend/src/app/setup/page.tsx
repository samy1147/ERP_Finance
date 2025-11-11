'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { SegmentType, Segment } from '@/types/segment';

export default function SetupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [segmentTypes, setSegmentTypes] = useState<SegmentType[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [filteredSegments, setFilteredSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Selected filters
  const [selectedType, setSelectedType] = useState<number | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showInactiveOnly, setShowInactiveOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [segments, selectedType, selectedLevel, searchTerm, showInactiveOnly]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [typesData, segmentsData] = await Promise.all([
        segmentService.getSegmentTypes(),
        segmentService.getSegments()
      ]);
      setSegmentTypes(typesData);
      setSegments(segmentsData);
      
      // Set default type from URL if present
      const typeFromUrl = searchParams?.get('type');
      if (typeFromUrl) {
        setSelectedType(parseInt(typeFromUrl));
      }
      
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...segments];

    // Filter by segment type
    if (selectedType !== null) {
      filtered = filtered.filter(s => {
        const typeId = typeof s.segment_type === 'object' ? s.segment_type.segment_id : s.segment_type;
        return typeId === selectedType;
      });
    }

    // Filter by level
    if (selectedLevel !== null) {
      filtered = filtered.filter(s => s.level === selectedLevel);
    }

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.code.toLowerCase().includes(term) ||
        (s.alias && s.alias.toLowerCase().includes(term))
      );
    }

    // Filter by active status
    if (showInactiveOnly) {
      filtered = filtered.filter(s => !s.is_active);
    }

    setFilteredSegments(filtered);
  };

  const handleDeleteType = async (id: number) => {
    if (!confirm('Are you sure you want to delete this segment type? All associated segments will also be deleted.')) return;
    
    try {
      await segmentService.deleteSegmentType(id);
      await loadData();
    } catch (err: any) {
      alert('Error deleting segment type: ' + (err.message || 'Unknown error'));
    }
  };

  const handleDeleteSegment = async (code: string) => {
    if (!confirm('Are you sure you want to delete this segment?')) return;
    
    try {
      await segmentService.deleteSegment(code);
      await loadData();
    } catch (err: any) {
      alert('Error deleting segment: ' + (err.message || 'Unknown error'));
    }
  };

  const clearFilters = () => {
    setSelectedType(null);
    setSelectedLevel(null);
    setSearchTerm('');
    setShowInactiveOnly(false);
  };

  const getSegmentTypeName = (typeId: number | SegmentType): string => {
    if (typeof typeId === 'object') return typeId.segment_name;
    const type = segmentTypes.find(t => t.segment_id === typeId);
    return type ? type.segment_name : `Type ${typeId}`;
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
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Segment Setup</h1>
        <p className="text-gray-600">Manage segment types and segment values for your GL structure</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Segment Types Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold text-gray-800">Segment Types</h2>
          <button
            onClick={() => router.push('/setup/segment-types/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            + New Segment Type
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {segmentTypes.map((type) => (
            <div
              key={type.segment_id}
              className={`p-4 border-2 rounded-lg cursor-pointer transition ${
                selectedType === type.segment_id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-blue-300'
              }`}
              onClick={() => setSelectedType(type.segment_id)}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">{type.segment_name}</h3>
                  <p className="text-sm text-gray-600">{type.segment_type}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded ${type.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                  {type.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="flex gap-2 mb-3">
                {type.is_required && (
                  <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Required</span>
                )}
                {type.has_hierarchy && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Hierarchical</span>
                )}
              </div>

              {type.description && (
                <p className="text-sm text-gray-600 mb-3">{type.description}</p>
              )}

              <div className="flex gap-2 pt-3 border-t">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(`/setup/segment-types/${type.segment_id}/edit`);
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Edit
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteType(type.segment_id);
                  }}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

        {segmentTypes.length === 0 && (
          <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
            No segment types found. Create one to get started.
          </div>
        )}
      </div>

      {/* Segment Values Section */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold text-gray-800">Segment Values</h2>
          <button
            onClick={() => router.push('/setup/segments/new')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            + New Segment Value
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by code or name..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">Segment Type</label>
              <select
                value={selectedType || ''}
                onChange={(e) => setSelectedType(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                {segmentTypes.map((type) => (
                  <option key={type.segment_id} value={type.segment_id}>
                    {type.segment_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="w-32">
              <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
              <select
                value={selectedLevel !== null ? selectedLevel : ''}
                onChange={(e) => setSelectedLevel(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Levels</option>
                <option value="0">Level 0 (Root)</option>
                <option value="1">Level 1</option>
                <option value="2">Level 2</option>
                <option value="3">Level 3</option>
                <option value="4">Level 4</option>
              </select>
            </div>

            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={showInactiveOnly}
                  onChange={(e) => setShowInactiveOnly(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Inactive only</span>
              </label>
            </div>

            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
            >
              Clear Filters
            </button>
          </div>

          <div className="mt-3 text-sm text-gray-600">
            Showing {filteredSegments.length} of {segments.length} segments
          </div>
        </div>

        {/* Segments Table */}
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
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
                  Segment Type
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
              {filteredSegments.map((segment) => (
                <tr key={segment.code} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-mono font-medium text-gray-900">{segment.code}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{segment.alias || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {getSegmentTypeName(segment.segment_type)}
                    </span>
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
                      onClick={() => router.push(`/setup/segments/${segment.id}`)}
                      className="text-indigo-600 hover:text-indigo-900 mr-4"
                    >
                      View
                    </button>
                    <button
                      onClick={() => router.push(`/setup/segments/${segment.id}/edit`)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteSegment(segment.code)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSegments.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No segments found matching your filters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
