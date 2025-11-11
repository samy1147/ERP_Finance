// Segment API Service
import api from '../lib/api';
import { SegmentType, Segment, SegmentHierarchy } from '../types/segment';
import { Account } from '../types';

export const segmentService = {
  // Segment Types
  getSegmentTypes: async (): Promise<SegmentType[]> => {
    const response = await api.get('/segment/types/');
    return response.data;
  },

  getSegmentType: async (id: number): Promise<SegmentType> => {
    const response = await api.get(`/segment/types/${id}/`);
    return response.data;
  },

  createSegmentType: async (data: Partial<SegmentType>): Promise<SegmentType> => {
    const response = await api.post('/segment/types/', data);
    return response.data;
  },

  updateSegmentType: async (id: number, data: Partial<SegmentType>): Promise<SegmentType> => {
    const response = await api.patch(`/segment/types/${id}/`, data);
    return response.data;
  },

  deleteSegmentType: async (id: number): Promise<void> => {
    await api.delete(`/segment/types/${id}/`);
  },

  getSegmentTypeValues: async (id: number): Promise<Segment[]> => {
    const response = await api.get(`/segment/types/${id}/values/`);
    return response.data;
  },

  // Segment Values
  getSegments: async (params?: any): Promise<Segment[]> => {
    const response = await api.get('/segment/values/', { params });
    return response.data;
  },

  getSegment: async (id: number): Promise<Segment> => {
    const response = await api.get(`/segment/values/${id}/`);
    return response.data;
  },
  
  getSegmentByCode: async (code: string, segmentTypeId?: number): Promise<Segment | null> => {
    const params: any = { code };
    if (segmentTypeId) params.segment_type = segmentTypeId;
    const response = await api.get('/segment/values/', { params });
    const results = response.data;
    return results.length > 0 ? results[0] : null;
  },

  createSegment: async (data: Partial<Segment>): Promise<Segment> => {
    const response = await api.post('/segment/values/', data);
    return response.data;
  },

  updateSegment: async (id: number, data: Partial<Segment>): Promise<Segment> => {
    const response = await api.patch(`/segment/values/${id}/`, data);
    return response.data;
  },

  deleteSegment: async (id: number): Promise<void> => {
    await api.delete(`/segment/values/${id}/`);
  },

  getSegmentChildren: async (id: number): Promise<Segment[]> => {
    const response = await api.get(`/segment/values/${id}/children/`);
    return response.data;
  },

  getSegmentDescendants: async (id: number): Promise<Segment[]> => {
    const response = await api.get(`/segment/values/${id}/descendants/`);
    return response.data;
  },

  getSegmentHierarchy: async (code: string): Promise<SegmentHierarchy> => {
    const response = await api.get(`/segment/values/${code}/hierarchy/`);
    return response.data;
  },

  // Get only child segments for a specific segment type (for GL distribution)
  getChildSegments: async (segmentTypeId: number, isActive: boolean = true): Promise<Segment[]> => {
    const params: any = { segment_type: segmentTypeId };
    if (isActive !== undefined) params.is_active = isActive;
    const response = await api.get('/segment/values/child_segments/', { params });
    return response.data;
  },

  // Get required segment types (for GL distribution validation)
  getRequiredSegmentTypes: async (): Promise<SegmentType[]> => {
    const response = await api.get('/segment/types/', { params: { is_required: true } });
    return response.data;
  },

  // Accounts (Proxy for Account segment type)
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get('/segment/accounts/');
    return response.data;
  },

  getAccount: async (id: number): Promise<Account> => {
    const response = await api.get(`/segment/accounts/${id}/`);
    return response.data;
  },
  
  getAccountByCode: async (code: string): Promise<Account | null> => {
    const response = await api.get('/segment/accounts/', { params: { code } });
    const results = response.data;
    return results.length > 0 ? results[0] : null;
  },

  createAccount: async (data: Partial<Account>): Promise<Account> => {
    const response = await api.post('/segment/accounts/', data);
    return response.data;
  },

  updateAccount: async (id: number, data: Partial<Account>): Promise<Account> => {
    const response = await api.patch(`/segment/accounts/${id}/`, data);
    return response.data;
  },

  deleteAccount: async (id: number): Promise<void> => {
    await api.delete(`/segment/accounts/${id}/`);
  },

  getAccountHierarchy: async (): Promise<Account[]> => {
    const response = await api.get('/segment/accounts/hierarchy/');
    return response.data;
  },
};

export default segmentService;
