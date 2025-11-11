'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Trash2, Package, Warehouse, Calendar, TruckIcon, Save } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { goodsReceiptsExtendedAPI } from '../../../../services/procurement-api';

interface POForSelection {
  id: number;
  po_number: string;
  vendor_name: string;
  total_amount: string;
  status: string;
  delivery_status: string;
}

interface POLine {
  id: number;
  line_number: number;
  item_description: string;
  quantity: number;
  received_quantity?: number;
  unit_price: string;
  unit_of_measure: number;
  uom_name?: string;
}

interface ReceiptLine {
  po_line_id: number;
  line_number: number;
  item_description: string;
  ordered_quantity: number;
  received_quantity: number;
  uom_name: string;
  lot_number: string;
  location: string;
  condition: 'GOOD' | 'DAMAGED' | 'DEFECTIVE';
  notes: string;
}

export default function NewGoodsReceiptPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [pos, setPOs] = useState<POForSelection[]>([]);
  const [selectedPO, setSelectedPO] = useState<number | null>(null);
  const [poLines, setPOLines] = useState<POLine[]>([]);
  
  // Form data
  const [receiptDate, setReceiptDate] = useState(new Date().toISOString().split('T')[0]);
  const [deliveryNote, setDeliveryNote] = useState('');
  const [carrier, setCarrier] = useState('');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [warehouse, setWarehouse] = useState('1'); // Default warehouse
  const [notes, setNotes] = useState('');
  const [receiptLines, setReceiptLines] = useState<ReceiptLine[]>([]);

  useEffect(() => {
    fetchConfirmedPOs();
  }, []);

  const fetchConfirmedPOs = async () => {
    try {
      // Fetch POs that are ready to receive (CONFIRMED or PARTIALLY_RECEIVED with outstanding items)
      const response = await fetch('http://127.0.0.1:8007/api/procurement/purchase-orders/receivable/');
      const data = await response.json();
      setPOs(Array.isArray(data) ? data : []);
      
      if (data.length === 0) {
        console.log('No purchase orders available for receiving. POs must be confirmed and have outstanding items.');
      }
    } catch (error) {
      console.error('Error fetching receivable POs:', error);
      toast.error('Failed to load receivable purchase orders');
    }
  };

  const handlePOSelect = async (poId: number) => {
    setSelectedPO(poId);
    try {
      // Fetch PO details to get lines with received quantities
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${poId}/`);
      const data = await response.json();
      
      if (data.lines && data.lines.length > 0) {
        setPOLines(data.lines);
        
        // Initialize receipt lines - only show items with outstanding quantities
        const initialLines: ReceiptLine[] = data.lines
          .filter((line: POLine) => {
            const outstanding = line.quantity - (line.received_quantity || 0);
            return outstanding > 0; // Only include lines with items to receive
          })
          .map((line: POLine) => {
            const outstanding = line.quantity - (line.received_quantity || 0);
            return {
              po_line_id: line.id,
              line_number: line.line_number,
              item_description: line.item_description,
              ordered_quantity: line.quantity,
              received_quantity: outstanding, // Default to outstanding quantity
              uom_name: line.uom_name || 'EA',
              lot_number: '',
              location: '',
              condition: 'GOOD' as const,
              notes: ''
            };
          });
        
        if (initialLines.length === 0) {
          toast('All items in this PO have been fully received', {
            icon: '⚠️',
          });
        }
        
        setReceiptLines(initialLines);
      }
    } catch (error) {
      console.error('Error fetching PO details:', error);
      toast.error('Failed to load PO details');
    }
  };

  const updateReceiptLine = (index: number, field: keyof ReceiptLine, value: any) => {
    const updated = [...receiptLines];
    updated[index] = { ...updated[index], [field]: value };
    setReceiptLines(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPO) {
      toast.error('Please select a Purchase Order');
      return;
    }

    if (receiptLines.length === 0) {
      toast.error('No items to receive');
      return;
    }

    // Validate that at least one item has quantity > 0
    const hasItems = receiptLines.some(line => line.received_quantity > 0);
    if (!hasItems) {
      toast.error('Please enter received quantities');
      return;
    }

    try {
      setLoading(true);

      const receiptData = {
        po_header: selectedPO,
        receipt_date: receiptDate,
        delivery_note_number: deliveryNote,
        carrier: carrier,
        tracking_number: trackingNumber,
        warehouse: parseInt(warehouse),
        notes: notes,
        lines: receiptLines.map(line => ({
          po_line: line.po_line_id,
          quantity_received: line.received_quantity,
          lot_number: line.lot_number || null,
          location: line.location || null,
          condition: line.condition,
          notes: line.notes || null
        }))
      } as any; // Type assertion since API accepts different format than GoodsReceipt interface

      // DEBUG: Log what we're sending
      console.log('='.repeat(70));
      console.log('DEBUG: Sending receipt data to API:');
      console.log('Receipt data:', JSON.stringify(receiptData, null, 2));
      console.log('Lines:', receiptData.lines);
      receiptData.lines.forEach((line: any, i: number) => {
        console.log(`Line ${i+1}:`, line);
        console.log(`  quantity_received: ${line.quantity_received} (type: ${typeof line.quantity_received})`);
      });
      console.log('='.repeat(70));

      await goodsReceiptsExtendedAPI.create(receiptData);
      
      toast.success('Goods Receipt created successfully!');
      router.push('/procurement/receiving');
    } catch (error: any) {
      console.error('Error creating receipt:', error);
      toast.error(error.response?.data?.error || 'Failed to create goods receipt');
    } finally {
      setLoading(false);
    }
  };

  const getTotalReceived = () => {
    return receiptLines.reduce((sum, line) => sum + line.received_quantity, 0);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/procurement/receiving"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Receiving
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Create Goods Receipt</h1>
          <p className="text-gray-600 mt-2">Record the receipt of goods from a confirmed purchase order</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* PO Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Package className="h-5 w-5 mr-2 text-gray-600" />
              Purchase Order Selection
            </h2>
            
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Purchase Order *
                </label>
                <select
                  value={selectedPO || ''}
                  onChange={(e) => handlePOSelect(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">-- Select a PO --</option>
                  {pos.map(po => {
                    const status = po.status === 'CONFIRMED' ? '🟢 New' : '🟡 Partial';
                    return (
                      <option key={po.id} value={po.id}>
                        {status} - {po.po_number} - {po.vendor_name} (${po.total_amount})
                      </option>
                    );
                  })}
                </select>
                {pos.length === 0 && (
                  <p className="text-sm text-gray-500 mt-2">
                    No confirmed purchase orders available. POs must be confirmed before receiving goods.
                  </p>
                )}
              </div>
            </div>
          </div>

          {selectedPO && (
            <>
              {/* Receipt Information */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <TruckIcon className="h-5 w-5 mr-2 text-gray-600" />
                  Receipt Information
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Receipt Date *
                    </label>
                    <input
                      type="date"
                      value={receiptDate}
                      onChange={(e) => setReceiptDate(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Delivery Note Number
                    </label>
                    <input
                      type="text"
                      value={deliveryNote}
                      onChange={(e) => setDeliveryNote(e.target.value)}
                      placeholder="Vendor's packing slip number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Carrier
                    </label>
                    <input
                      type="text"
                      value={carrier}
                      onChange={(e) => setCarrier(e.target.value)}
                      placeholder="FedEx, UPS, DHL, etc."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tracking Number
                    </label>
                    <input
                      type="text"
                      value={trackingNumber}
                      onChange={(e) => setTrackingNumber(e.target.value)}
                      placeholder="Package tracking number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Warehouse *
                    </label>
                    <select
                      value={warehouse}
                      onChange={(e) => setWarehouse(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    >
                      <option value="1">Main Warehouse</option>
                      <option value="2">Branch Warehouse</option>
                      <option value="3">Quality Control Area</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Receipt Notes
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Any special notes about this receipt..."
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Receipt Lines */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Warehouse className="h-5 w-5 mr-2 text-gray-600" />
                  Items to Receive
                </h2>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Line</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Item Description</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Ordered</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Received *</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Lot/Batch</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Location</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Condition</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {receiptLines.map((line, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-900">{line.line_number}</td>
                          <td className="py-3 px-4 text-sm text-gray-900">{line.item_description}</td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {line.ordered_quantity} {line.uom_name}
                          </td>
                          <td className="py-3 px-4">
                            <input
                              type="number"
                              min="0"
                              max={line.ordered_quantity}
                              step="0.01"
                              value={line.received_quantity}
                              onChange={(e) => updateReceiptLine(index, 'received_quantity', parseFloat(e.target.value) || 0)}
                              className="w-24 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              required
                            />
                          </td>
                          <td className="py-3 px-4">
                            <input
                              type="text"
                              value={line.lot_number}
                              onChange={(e) => updateReceiptLine(index, 'lot_number', e.target.value)}
                              placeholder="LOT-001"
                              className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </td>
                          <td className="py-3 px-4">
                            <input
                              type="text"
                              value={line.location}
                              onChange={(e) => updateReceiptLine(index, 'location', e.target.value)}
                              placeholder="Shelf A-12"
                              className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </td>
                          <td className="py-3 px-4">
                            <select
                              value={line.condition}
                              onChange={(e) => updateReceiptLine(index, 'condition', e.target.value)}
                              className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="GOOD">Good</option>
                              <option value="DAMAGED">Damaged</option>
                              <option value="DEFECTIVE">Defective</option>
                            </select>
                          </td>
                          <td className="py-3 px-4">
                            <input
                              type="text"
                              value={line.notes}
                              onChange={(e) => updateReceiptLine(index, 'notes', e.target.value)}
                              placeholder="Optional notes"
                              className="w-48 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-blue-800">
                      <strong>Total Items:</strong> {receiptLines.length} line(s)
                    </div>
                    <div className="text-sm text-blue-800">
                      <strong>Total Received:</strong> {getTotalReceived()} units
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4 justify-end">
                <Link
                  href="/procurement/receiving"
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </Link>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save size={20} />
                  {loading ? 'Creating...' : 'Create Goods Receipt'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
