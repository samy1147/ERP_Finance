'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Package, CheckCircle, XCircle, Calendar, User, Warehouse, TruckIcon } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { goodsReceiptsExtendedAPI } from '../../../../services/procurement-api';
import { GoodsReceipt } from '../../../../types/procurement';

export default function GoodsReceiptDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  
  const [receipt, setReceipt] = useState<GoodsReceipt | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReceipt();
  }, [id]);

  const fetchReceipt = async () => {
    try {
      setLoading(true);
      const response = await goodsReceiptsExtendedAPI.get(parseInt(id));
      setReceipt(response.data);
    } catch (error: any) {
      console.error('Error fetching receipt:', error);
      toast.error('Failed to load goods receipt');
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async () => {
    if (!confirm('Post this receipt to inventory? This action cannot be undone.')) return;
    
    try {
      await goodsReceiptsExtendedAPI.post(parseInt(id));
      toast.success('Receipt posted to inventory successfully');
      fetchReceipt();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to post receipt');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      QUALITY_HOLD: 'bg-yellow-100 text-yellow-800',
      REJECTED: 'bg-red-100 text-red-800',
      CANCELLED: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading receipt...</p>
        </div>
      </div>
    );
  }

  if (!receipt) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Receipt Not Found</h2>
            <p className="text-gray-600 mb-6">The goods receipt you're looking for doesn't exist.</p>
            <Link
              href="/procurement/receiving"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft size={20} />
              Back to Receiving
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/procurement/receiving"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Receiving
          </Link>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{receipt.grn_number}</h1>
              <p className="text-gray-600 mt-1">Goods Receipt Details</p>
              {receipt.grn_type && (
                <div className="mt-2">
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                    receipt.grn_type === 'SERVICES' 
                      ? 'bg-purple-100 text-purple-800' 
                      : receipt.grn_type === 'CATEGORIZED_GOODS'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {receipt.grn_type === 'SERVICES' ? '🔧 Services' : 
                     receipt.grn_type === 'CATEGORIZED_GOODS' ? '📋 Cataloged Goods' : '✏️ Free Text Goods'}
                  </span>
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(receipt.status)}`}>
                {receipt.status}
              </span>
              {receipt.status === 'DRAFT' && (
                <button
                  onClick={handlePost}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <CheckCircle size={18} />
                  {receipt.grn_type === 'CATEGORIZED_GOODS' ? 'Post to Inventory' : 'Post to Expenses'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Receipt Information */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Purchase Order Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Package className="h-5 w-5 mr-2 text-gray-600" />
              Purchase Order Information
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">PO Number</label>
                <p className="font-medium text-gray-900">{receipt.po_number || receipt.po_reference}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Vendor</label>
                <p className="font-medium text-gray-900">{receipt.vendor_name}</p>
              </div>
            </div>
          </div>

          {/* Receipt Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-600" />
              Receipt Details
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Receipt Date</label>
                <p className="font-medium text-gray-900">{new Date(receipt.receipt_date).toLocaleDateString()}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Delivery Note</label>
                <p className="font-medium text-gray-900">{receipt.delivery_note_number || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Delivery Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TruckIcon className="h-5 w-5 mr-2 text-gray-600" />
              Delivery Information
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Carrier</label>
                <p className="font-medium text-gray-900">{receipt.carrier || receipt.driver_name || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Vehicle Number</label>
                <p className="font-medium text-gray-900">{receipt.vehicle_number || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Tracking Number</label>
                <p className="font-medium text-gray-900">{receipt.tracking_number || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Warehouse Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Warehouse className="h-5 w-5 mr-2 text-gray-600" />
              Warehouse Information
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Warehouse</label>
                <p className="font-medium text-gray-900">{receipt.warehouse_name}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Receipt Lines */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Receipt Lines</h2>
          {receipt.lines && receipt.lines.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Line</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Item Description</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Quantity</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Condition</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Lot Number</th>
                  </tr>
                </thead>
                <tbody>
                  {receipt.lines.map((line: any, index: number) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-3 px-4 text-sm text-gray-900">{line.line_number || index + 1}</td>
                      <td className="py-3 px-4 text-sm text-gray-900">{line.item_description}</td>
                      <td className="py-3 px-4 text-sm text-gray-900">{line.received_quantity}</td>
                      <td className="py-3 px-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          line.condition === 'GOOD' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {line.condition}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900">{line.lot_number || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-3 text-gray-400" />
              <p>No receipt lines recorded</p>
            </div>
          )}
        </div>

        {/* Remarks */}
        {receipt.remarks && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Remarks</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{receipt.remarks}</p>
          </div>
        )}
      </div>
    </div>
  );
}
