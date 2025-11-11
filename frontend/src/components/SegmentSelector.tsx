'use client';

import React, { useEffect, useState } from 'react';
import { segmentService } from '../services/segmentService';
import { SegmentType, Segment } from '../types/segment';
import { JournalLineSegment } from '../types';

interface SegmentSelectorProps {
  value: JournalLineSegment[];
  onChange: (segments: JournalLineSegment[]) => void;
  disabled?: boolean;
}

export default function SegmentSelector({ value, onChange, disabled = false }: SegmentSelectorProps) {
  const [segmentTypes, setSegmentTypes] = useState<SegmentType[]>([]);
  const [segmentOptions, setSegmentOptions] = useState<Record<number, Segment[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSegmentTypes();
  }, []);

  const loadSegmentTypes = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all required segment types
      const types = await segmentService.getRequiredSegmentTypes();
      setSegmentTypes(types);
      
      // Load child segments for each type
      const optionsPromises = types.map(async (type) => {
        const children = await segmentService.getChildSegments(type.segment_id, true);
        // Filter to ensure only child node_type segments are included
        const childOnly = children.filter(seg => seg.node_type === 'child');
        console.log(`Segment Type ${type.segment_name}: Loaded ${childOnly.length} child segments`, childOnly);
        return { typeId: type.segment_id, children: childOnly };
      });
      
      const results = await Promise.all(optionsPromises);
      const optionsMap: Record<number, Segment[]> = {};
      results.forEach(({ typeId, children }) => {
        optionsMap[typeId] = children;
      });
      
      setSegmentOptions(optionsMap);
      
      // Initialize segments if empty
      if (value.length === 0 && types.length > 0) {
        const initialSegments = types.map(type => ({
          segment_type: type.segment_id,
          segment: 0,
        }));
        onChange(initialSegments);
      }
    } catch (err: any) {
      console.error('Failed to load segment types:', err);
      setError(err.message || 'Failed to load segment configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSegmentChange = (segmentTypeId: number, segmentId: number) => {
    const newSegments = [...value];
    const index = newSegments.findIndex(s => s.segment_type === segmentTypeId);
    
    if (index >= 0) {
      newSegments[index] = {
        ...newSegments[index],
        segment: segmentId,
      };
    } else {
      newSegments.push({
        segment_type: segmentTypeId,
        segment: segmentId,
      });
    }
    
    onChange(newSegments);
  };

  const getSegmentValue = (segmentTypeId: number): number => {
    const segment = value.find(s => s.segment_type === segmentTypeId);
    return segment?.segment || 0;
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500 py-2">
        Loading segment types...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600 py-2 bg-red-50 px-3 rounded border border-red-200">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (segmentTypes.length === 0) {
    return (
      <div className="text-sm text-gray-500 py-2 bg-gray-50 px-3 rounded">
        No required segment types configured
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-xs font-medium text-gray-700 uppercase tracking-wider mb-2">
        Required Segments
      </div>
      
      {segmentTypes.map((type) => {
        const options = segmentOptions[type.segment_id] || [];
        const selectedValue = getSegmentValue(type.segment_id);
        const hasNoOptions = options.length === 0;
        
        return (
          <div key={type.segment_id} className="grid grid-cols-12 gap-2 items-center">
            <div className="col-span-4 text-sm font-medium text-gray-700">
              {type.segment_name}
              {type.is_required && <span className="text-red-500 ml-1">*</span>}
            </div>
            
            <div className="col-span-8">
              <select
                className={`input-field w-full text-sm ${hasNoOptions ? 'bg-gray-100' : ''}`}
                value={selectedValue}
                onChange={(e) => handleSegmentChange(type.segment_id, parseInt(e.target.value))}
                disabled={disabled || hasNoOptions}
                required={type.is_required}
              >
                <option value="">
                  {hasNoOptions ? 'No child segments available' : `Select ${type.segment_name}`}
                </option>
                {options.map((segment) => (
                  <option key={segment.id} value={segment.id}>
                    {segment.code} - {segment.alias}
                  </option>
                ))}
              </select>
            </div>
          </div>
        );
      })}
      
      {segmentTypes.length > 0 && (
        <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">
          Note: Only child-level segments are shown. All required segment types must have a value selected.
        </div>
      )}
    </div>
  );
}
