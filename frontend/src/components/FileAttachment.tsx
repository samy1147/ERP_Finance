"use client";

import React, { useState, useRef, useCallback } from 'react';
import { attachmentsAPI } from '@/services/api';
import { Attachment } from '@/types';

interface FileAttachmentProps {
  documentType: 'PO' | 'PR';
  documentId: number;
  onAttachmentsChange?: () => void;
}

type DocumentTypeValue = 'PO' | 'PR' | 'QUOTE' | 'CONTRACT' | 'SPEC' | 'OTHER';

const DOCUMENT_TYPE_OPTIONS = [
  { value: 'PO', label: 'Purchase Order' },
  { value: 'PR', label: 'Purchase Requisition' },
  { value: 'QUOTE', label: 'Vendor Quote' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'SPEC', label: 'Specification' },
  { value: 'OTHER', label: 'Other' },
];

const ALLOWED_EXTENSIONS = [
  'pdf', 'doc', 'docx', 'xls', 'xlsx',
  'txt', 'csv', 'jpg', 'jpeg', 'png',
  'gif', 'zip', 'rar'
];

export default function FileAttachment({ documentType, documentId, onAttachmentsChange }: FileAttachmentProps) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadForm, setUploadForm] = useState<{
    file: File | null;
    documentType: string;
    description: string;
  }>({
    file: null,
    documentType: documentType,
    description: '',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load attachments
  const loadAttachments = useCallback(async () => {
    setLoading(true);
    try {
      const params = documentType === 'PO' 
        ? { po_header: documentId }
        : { pr_header: documentId };
      
      const response = await attachmentsAPI.list(params);
      setAttachments(response.data);
    } catch (error) {
      console.error('Failed to load attachments:', error);
    } finally {
      setLoading(false);
    }
  }, [documentType, documentId]);

  // Load attachments on mount
  React.useEffect(() => {
    loadAttachments();
  }, [loadAttachments]);

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  // Validate file
  const validateAndSetFile = (file: File) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const extension = file.name.split('.').pop()?.toLowerCase();

    if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
      alert(`Invalid file type. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }

    if (file.size > maxSize) {
      alert('File size must not exceed 10MB');
      return;
    }

    setUploadForm({ ...uploadForm, file });
    setShowUploadForm(true);
  };

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Handle drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  // Upload file
  const handleUpload = async () => {
    if (!uploadForm.file) return;

    setUploadProgress(0);
    try {
      if (documentType === 'PO') {
        await attachmentsAPI.uploadPO(
          documentId,
          uploadForm.file,
          uploadForm.documentType,
          uploadForm.description
        );
      } else {
        await attachmentsAPI.uploadPR(
          documentId,
          uploadForm.file,
          uploadForm.documentType,
          uploadForm.description
        );
      }

      // Reset form
      setUploadForm({
        file: null,
        documentType: documentType,
        description: '',
      });
      setShowUploadForm(false);
      setUploadProgress(null);

      // Reload attachments
      await loadAttachments();
      
      if (onAttachmentsChange) {
        onAttachmentsChange();
      }

      alert('File uploaded successfully!');
    } catch (error: any) {
      console.error('Upload failed:', error);
      alert(error?.response?.data?.error || 'Failed to upload file');
    } finally {
      setUploadProgress(null);
    }
  };

  // Delete attachment
  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this attachment?')) {
      return;
    }

    try {
      await attachmentsAPI.delete(id);
      await loadAttachments();
      
      if (onAttachmentsChange) {
        onAttachmentsChange();
      }

      alert('Attachment deleted successfully');
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete attachment');
    }
  };

  // Download attachment
  const handleDownload = (attachment: Attachment) => {
    const url = attachmentsAPI.getDownloadUrl(attachment.file_url);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium flex items-center gap-2">
          📎 Attachments ({attachments.length})
        </h3>
        {!showUploadForm && (
          <button
            onClick={() => setShowUploadForm(true)}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
          >
            Upload File
          </button>
        )}
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-medium">Upload New File</h4>
            <button
              onClick={() => {
                setShowUploadForm(false);
                setUploadForm({ file: null, documentType: documentType, description: '' });
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* File Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileSelect}
              accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
            />
            
            {uploadForm.file ? (
              <div className="flex items-center justify-center gap-2">
                <span className="text-4xl">📄</span>
                <div className="text-left">
                  <p className="font-medium">{uploadForm.file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(uploadForm.file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={() => setUploadForm({ ...uploadForm, file: null })}
                  className="ml-4 text-red-600 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            ) : (
              <>
                <div className="text-6xl text-gray-400 mb-2">☁️</div>
                <p className="mt-2 text-sm text-gray-600">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Click to upload
                  </button>
                  {' '}or drag and drop
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  PDF, DOC, XLS, Images, ZIP (max 10MB)
                </p>
              </>
            )}
          </div>

          {uploadForm.file && (
            <div className="mt-4 space-y-3">
              {/* Document Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type
                </label>
                <select
                  value={uploadForm.documentType}
                  onChange={(e) => setUploadForm({ ...uploadForm, documentType: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  {DOCUMENT_TYPE_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <input
                  type="text"
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="Brief description of the file"
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  maxLength={500}
                />
              </div>

              {/* Upload Button */}
              <div className="flex gap-2">
                <button
                  onClick={handleUpload}
                  disabled={uploadProgress !== null}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {uploadProgress !== null ? `Uploading... ${uploadProgress}%` : 'Upload File'}
                </button>
                <button
                  onClick={() => {
                    setShowUploadForm(false);
                    setUploadForm({ file: null, documentType: documentType, description: '' });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attachments List */}
      {loading ? (
        <div className="text-center py-4 text-gray-500">Loading attachments...</div>
      ) : attachments.length === 0 ? (
        <div className="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
          <div className="text-5xl text-gray-300 mb-2">📎</div>
          <p className="mt-2">No attachments yet</p>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg divide-y">
          {attachments.map((attachment) => (
            <div key={attachment.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
              <div className="flex items-center gap-3 flex-1">
                <span className="text-3xl">📄</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {attachment.original_filename}
                  </p>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                      {attachment.document_type}
                    </span>
                    <span>{attachment.file_size_display}</span>
                    <span>Uploaded by {attachment.uploaded_by_name}</span>
                    <span>{new Date(attachment.uploaded_at).toLocaleDateString()}</span>
                  </div>
                  {attachment.description && (
                    <p className="text-sm text-gray-600 mt-1">{attachment.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <button
                  onClick={() => handleDownload(attachment)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                  title="Download"
                >
                  ⬇️
                </button>
                <button
                  onClick={() => handleDelete(attachment.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
