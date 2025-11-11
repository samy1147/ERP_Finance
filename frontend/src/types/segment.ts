// Segment Types & Values Management interfaces
export interface SegmentType {
  segment_id: number;
  segment_name: string;
  segment_type: string;
  is_required: boolean;
  has_hierarchy: boolean;
  length: number; // Fixed length for segment codes
  display_order: number;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Segment {
  id: number; // Required - primary key for detail operations
  code: string;
  alias: string;
  segment_type: number | SegmentType;
  parent_code?: string | null;
  node_type: 'parent' | 'sub_parent' | 'child'; // Node type in hierarchy
  level: number;
  envelope_amount?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  
  // Computed properties for backward compatibility
  name?: string; // Alias for 'alias' field
  hierarchy_level?: number;
  full_path?: string;
}

export interface SegmentHierarchy extends Segment {
  children?: SegmentHierarchy[];
}

// Helper type for account segments (segments where segment_type.segment_name = 'Account')
export type AccountSegment = Segment;
