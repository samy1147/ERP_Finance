'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Save, Send, CheckCircle, XCircle, Package, Edit, Calendar, DollarSign, User, Building, Clock } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import FileAttachment from '@/components/FileAttachment';
import TempFileAttachment from '@/components/TempFileAttachment';
import { attachmentsAPI } from '@/services/api';

interface POLine {
  id: number;
  line_number: number;
  description: string;
  quantity: number;
  unit_price: string;
  uom: string;
  line_total: string;
  base_currency_unit_price?: string;
  base_currency_line_total?: string;
  pr_line?: number;
}

interface Supplier {
  id: number;
  code: string;
  name: string;
  email: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  payment_terms_days: number;
  is_active: boolean;
  can_transact: boolean;
}

interface POHeader {
  id: number;
  po_number: string;
  po_date: string;
  po_type?: 'CATEGORIZED_GOODS' | 'UNCATEGORIZED_GOODS' | 'SERVICES';
  status: string;
  vendor_name: string;
  vendor_email: string;
  vendor_phone: string;
  title: string;
  description: string;
  currency: number;  // Currency ID
  currency_code?: string;
  currency_symbol?: string;
  currency_details?: {
    id: number;
    code: string;
    name: string;
    symbol: string;
  };
  total_amount: string;
  exchange_rate?: string;
  base_currency_total?: string;
  delivery_address: string;
  delivery_date: string;
  payment_terms: string;
  lines: POLine[];
  pr_number?: string;
  created_by_name: string;
  created_at: string;
  submitted_at?: string;
  approved_at?: string;
  confirmed_at?: string;
}

const STATUS_COLORS = {
  DRAFT: 'bg-gray-100 text-gray-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  CONFIRMED: 'bg-purple-100 text-purple-800',
  PARTIALLY_RECEIVED: 'bg-yellow-100 text-yellow-800',
  RECEIVED: 'bg-teal-100 text-teal-800',
  CLOSED: 'bg-gray-100 text-gray-600',
  CANCELLED: 'bg-red-100 text-red-800',
};

export default function PODetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [po, setPO] = useState<POHeader | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tempSession] = useState(() => `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    if (id === 'new') {
      // Initialize empty PO for creation
      const newPO: POHeader = {
        id: 0,
        po_number: 'NEW',
        po_date: new Date().toISOString().split('T')[0],
        status: 'DRAFT',
        vendor_name: '',
        vendor_email: '',
        vendor_phone: '',
        title: '',
        description: '',
        currency: 1, // Default currency ID
        total_amount: '0.00',
        delivery_address: '',
        delivery_date: '',
        payment_terms: '',
        lines: [],
        created_by_name: '',
        created_at: new Date().toISOString(),
      };
      setPO(newPO);
      setLoading(false);
      setEditing(true);
    } else {
      fetchPO();
    }
    fetchSuppliers();
  }, [id]);

  const fetchSuppliers = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/ap/vendors/?is_active=true');
      const data = await response.json();
      setSuppliers(data.results || data);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      toast.error('Failed to load suppliers');
    }
  };

  const fetchPO = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/`);
      const data = await response.json();
      setPO(data);
      // Auto-enable editing for DRAFT status
      if (data.status === 'DRAFT') {
        setEditing(true);
      }
    } catch (error) {
      console.error('Error fetching PO:', error);
      toast.error('Failed to load Purchase Order');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!po) return;
    
    const wasApproved = po.status === 'APPROVED';
    const isNewPO = id === 'new' || po.id === 0;
    
    try {
      setSaving(true);
      
      if (isNewPO) {
        // Create new PO (POST request)
        const response = await fetch('http://127.0.0.1:8007/api/procurement/purchase-orders/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vendor_name: po.vendor_name,
            vendor_email: po.vendor_email,
            vendor_phone: po.vendor_phone,
            delivery_address: po.delivery_address,
            delivery_date: po.delivery_date,
            payment_terms: po.payment_terms,
            description: po.description,
            title: po.title,
            po_date: po.po_date,
            currency: po.currency,
            lines: po.lines,
          }),
        });
        
        if (response.ok) {
          const newPO = await response.json();
          
          // Link temporary attachments to the new PO
          try {
            await attachmentsAPI.linkToPO(tempSession, newPO.id);
          } catch (attachError) {
            console.error('Failed to link attachments:', attachError);
            // Don't fail the whole operation if attachments fail
          }
          
          toast.success('Purchase Order created successfully');
          router.push(`/procurement/purchase-orders/${newPO.id}`);
        } else {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to create PO');
        }
      } else {
        // Update existing PO (PATCH request)
        const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vendor_name: po.vendor_name,
            vendor_email: po.vendor_email,
            vendor_phone: po.vendor_phone,
            delivery_address: po.delivery_address,
            delivery_date: po.delivery_date,
            payment_terms: po.payment_terms,
            description: po.description,
          }),
        });
        
        if (response.ok) {
          if (wasApproved) {
            toast.success('Purchase Order saved. Status reset to SUBMITTED for re-approval.');
          } else {
            toast.success('Purchase Order saved successfully');
          }
          setEditing(false);
          fetchPO();
        } else {
          throw new Error('Failed to save');
        }
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to save Purchase Order');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!po) return;
    if (!confirm('Submit this PO for approval?')) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/submit/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        toast.success('Purchase Order submitted for approval');
        fetchPO();
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to submit');
      }
    } catch (error) {
      toast.error('Failed to submit Purchase Order');
      console.error(error);
    }
  };

  const handleApprove = async () => {
    if (!po) return;
    if (!confirm('Approve this Purchase Order?')) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/approve/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        toast.success('Purchase Order approved');
        fetchPO();
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to approve');
      }
    } catch (error) {
      toast.error('Failed to approve Purchase Order');
      console.error(error);
    }
  };

  const handleConfirm = async () => {
    if (!po) return;
    if (!confirm('Confirm and send this PO to vendor?')) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/confirm/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        toast.success('Purchase Order confirmed and sent to vendor');
        fetchPO();
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to confirm');
      }
    } catch (error) {
      toast.error('Failed to confirm Purchase Order');
      console.error(error);
    }
  };

  const handleCancelDelivery = async () => {
    if (!po) return;
    const reason = prompt('Reason for cancelling delivery (optional):');
    if (reason === null) return; // User clicked cancel
    
    if (!confirm('Cancel delivery and revert to APPROVED status? You can re-confirm later.')) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${id}/cancel_delivery/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      
      if (response.ok) {
        toast.success('Delivery cancelled. PO reverted to APPROVED status.');
        fetchPO();
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to cancel delivery');
      }
    } catch (error) {
      toast.error('Failed to cancel delivery');
      console.error(error);
    }
  };

  const handleEnableEdit = () => {
    if (!po) return;
    
    // If PO is submitted or approved, warn user about resetting approval
    if (po.status === 'SUBMITTED' || po.status === 'APPROVED') {
      const message = po.status === 'APPROVED' 
        ? 'This PO is approved. Editing it will reset the approval status to SUBMITTED, and it will need to be approved again. Continue?'
        : 'This PO is submitted for approval. Editing it will require re-approval after saving. Continue?';
      
      if (confirm(message)) {
        setEditing(true);
      }
    } else {
      setEditing(true);
    }
  };

  const handleVendorSelect = (supplierId: string) => {
    if (!po) return;
    
    const selectedSupplier = suppliers.find(s => s.id === parseInt(supplierId));
    if (selectedSupplier) {
      // Build full address
      const addressParts = [
        selectedSupplier.address_line1,
        selectedSupplier.address_line2,
        selectedSupplier.city,
        selectedSupplier.state,
        selectedSupplier.postal_code,
        selectedSupplier.country
      ].filter(Boolean);
      
      const fullAddress = addressParts.join(', ');
      
      // Map payment terms days to payment terms option
      let paymentTerms = 'NET_30';
      if (selectedSupplier.payment_terms_days === 60) paymentTerms = 'NET_60';
      else if (selectedSupplier.payment_terms_days === 90) paymentTerms = 'NET_90';
      else if (selectedSupplier.payment_terms_days === 0) paymentTerms = 'COD';
      
      setPO({
        ...po,
        vendor_name: selectedSupplier.name,
        vendor_email: selectedSupplier.email,
        vendor_phone: selectedSupplier.phone,
        delivery_address: po.delivery_address || fullAddress,
        payment_terms: paymentTerms
      });
      
      toast.success(`Vendor "${selectedSupplier.name}" selected and details populated`);
    }
  };

  const handleUpdateLine = (lineIndex: number, field: string, value: string) => {
    if (!po) return;
    
    const updatedLines = [...po.lines];
    updatedLines[lineIndex] = {
      ...updatedLines[lineIndex],
      [field]: value,
    };
    
    // Recalculate line total
    if (field === 'quantity' || field === 'unit_price') {
      const quantity = parseFloat(field === 'quantity' ? value : updatedLines[lineIndex].quantity.toString());
      const unitPrice = parseFloat(field === 'unit_price' ? value : updatedLines[lineIndex].unit_price);
      updatedLines[lineIndex].line_total = (quantity * unitPrice).toFixed(2);
    }
    
    setPO({ ...po, lines: updatedLines });
  };

  // Helper function to get currency symbol
  const getCurrencySymbol = () => {
    if (!po) return '$';
    return po.currency_symbol || po.currency_details?.symbol || '$';
  };

  // Helper function to get currency code
  const getCurrencyCode = () => {
    if (!po) return 'USD';
    return po.currency_code || po.currency_details?.code || 'USD';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!po) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Purchase Order Not Found</h3>
          <Link href="/procurement/purchase-orders" className="text-blue-600 hover:underline">
            Back to Purchase Orders
          </Link>
        </div>
      </div>
    );
  }

  const canEdit = po.status === 'DRAFT' || po.status === 'SUBMITTED' || po.status === 'APPROVED';
  const canSubmit = po.status === 'DRAFT';
  const canConfirm = po.status === 'APPROVED';
  const canCancelDelivery = po.status === 'CONFIRMED';
  const needsReapproval = po.status === 'SUBMITTED' || po.status === 'APPROVED';

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <Link
            href="/procurement/purchase-orders"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Purchase Orders
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{po.po_number}</h1>
            {po.status && (
              <span className={`px-3 py-1 text-sm font-semibold rounded-full ${STATUS_COLORS[po.status as keyof typeof STATUS_COLORS]}`}>
                {po.status.replace('_', ' ')}
              </span>
            )}
            {po.po_type && (
              <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                po.po_type === 'SERVICES' 
                  ? 'bg-purple-100 text-purple-800' 
                  : po.po_type === 'CATEGORIZED_GOODS'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {po.po_type === 'SERVICES' ? '� Services' : 
                 po.po_type === 'CATEGORIZED_GOODS' ? '� Cataloged' : '✏️ Free Text'}
              </span>
            )}
          </div>
          <p className="text-gray-600 mt-1">{po.title}</p>
          {po.pr_number && (
            <p className="text-sm text-gray-500 mt-1">Converted from PR: {po.pr_number}</p>
          )}
        </div>
        
        <div className="flex gap-2">
          {canEdit && editing && (
            <>
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                <Save className="h-5 w-5 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          )}
          
          {canEdit && !editing && (
            <button
              onClick={handleEnableEdit}
              className="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              <Edit className="h-5 w-5 mr-2" />
              Edit
            </button>
          )}
          
          {canSubmit && !editing && (
            <button
              onClick={handleSubmit}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Send className="h-5 w-5 mr-2" />
              Submit for Approval
            </button>
          )}
          
          {/* Approve button removed - PO approval should go through approval workflow page */}
          
          {canConfirm && (
            <button
              onClick={handleConfirm}
              className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Send className="h-5 w-5 mr-2" />
              Confirm & Send to Vendor
            </button>
          )}
          
          {canCancelDelivery && (
            <button
              onClick={handleCancelDelivery}
              className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <XCircle className="h-5 w-5 mr-2" />
              Cancel Delivery
            </button>
          )}
        </div>
      </div>

      {/* Info Banner for Submitted Status */}
      {po.status === 'SUBMITTED' && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <Clock className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-yellow-900">Pending Approval</h3>
              <p className="text-sm text-yellow-800 mt-1">
                This PO has been submitted and is waiting for approval. Check the Approvals page to approve this request.
                {canEdit && ' You can still edit this PO, and it will remain in SUBMITTED status for re-approval.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner for Approved Status */}
      {po.status === 'APPROVED' && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-green-900">Approved</h3>
              <p className="text-sm text-green-800 mt-1">
                This PO has been approved. You can now confirm and send it to the vendor.
                {canEdit && ' If you edit this PO, it will be reset to SUBMITTED status and require re-approval.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner for Confirmed Status */}
      {po.status === 'CONFIRMED' && (
        <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="flex items-start">
            <Send className="h-5 w-5 text-purple-600 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-purple-900">Confirmed & Sent to Vendor</h3>
              <p className="text-sm text-purple-800 mt-1">
                This PO has been confirmed and sent to the vendor. Waiting for goods to be received.
                If the delivery needs to be cancelled or rescheduled, you can cancel the delivery to revert back to APPROVED status.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner for Draft Status */}
      {po.status === 'DRAFT' && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <Edit className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900">Draft Purchase Order</h3>
              <p className="text-sm text-blue-800 mt-1">
                This PO was created from an approved PR with estimated prices. Update the vendor details,
                adjust prices to actual negotiated amounts, and set delivery terms before submitting for approval.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Left Side */}
        <div className="lg:col-span-2 space-y-6">
          {/* Vendor Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Building className="h-5 w-5 mr-2 text-gray-600" />
              Vendor Information
            </h2>
            {editing && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Tip:</strong> Select a vendor from the dropdown to automatically populate email, phone, address, and payment terms.
                  You can also enter vendor details manually.
                </p>
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {editing ? 'Select Vendor from Database' : 'Vendor Name *'}
                </label>
                {editing ? (
                  <div className="space-y-2">
                    <select
                      value={suppliers.find(s => s.name === po.vendor_name)?.id || ''}
                      onChange={(e) => handleVendorSelect(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option value="">-- Select a vendor to auto-fill details --</option>
                      {suppliers.filter(s => s.can_transact).map(supplier => (
                        <option key={supplier.id} value={supplier.id}>
                          {supplier.code ? `${supplier.code} - ${supplier.name}` : supplier.name}
                        </option>
                      ))}
                    </select>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Or Enter Vendor Name Manually</label>
                      <input
                        type="text"
                        value={po.vendor_name}
                        onChange={(e) => setPO({ ...po, vendor_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter vendor name"
                      />
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-900 font-medium text-lg">{po.vendor_name || 'Not specified'}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Vendor Email</label>
                {editing ? (
                  <input
                    type="email"
                    value={po.vendor_email}
                    onChange={(e) => setPO({ ...po, vendor_email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="vendor@example.com"
                  />
                ) : (
                  <p className="text-gray-900">{po.vendor_email || 'Not specified'}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Vendor Phone</label>
                {editing ? (
                  <input
                    type="tel"
                    value={po.vendor_phone}
                    onChange={(e) => setPO({ ...po, vendor_phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="+1-234-567-8900"
                  />
                ) : (
                  <p className="text-gray-900">{po.vendor_phone || 'Not specified'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Delivery Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-600" />
              Delivery & Payment Terms
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Date</label>
                {editing ? (
                  <input
                    type="date"
                    value={po.delivery_date}
                    onChange={(e) => setPO({ ...po, delivery_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : 'Not specified'}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Terms</label>
                {editing ? (
                  <select
                    value={po.payment_terms}
                    onChange={(e) => setPO({ ...po, payment_terms: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select terms</option>
                    <option value="NET_30">Net 30</option>
                    <option value="NET_60">Net 60</option>
                    <option value="NET_90">Net 90</option>
                    <option value="COD">Cash on Delivery</option>
                    <option value="ADVANCE">Advance Payment</option>
                  </select>
                ) : (
                  <p className="text-gray-900">{po.payment_terms || 'Not specified'}</p>
                )}
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Address</label>
                {editing ? (
                  <textarea
                    value={po.delivery_address}
                    onChange={(e) => setPO({ ...po, delivery_address: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter delivery address"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">{po.delivery_address || 'Not specified'}</p>
                )}
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description / Notes</label>
                {editing ? (
                  <textarea
                    value={po.description}
                    onChange={(e) => setPO({ ...po, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Additional notes or instructions"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">{po.description || 'No description'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Package className="h-5 w-5 mr-2 text-gray-600" />
              Line Items
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">UOM</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unit Price ({getCurrencyCode()})</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Line Total ({getCurrencyCode()})</th>
                    {po.exchange_rate && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total (AED)</th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {po.lines.map((line, index) => (
                    <tr key={line.id}>
                      <td className="px-4 py-3 text-sm text-gray-900">{line.line_number}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{line.description}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {editing ? (
                          <input
                            type="number"
                            value={line.quantity}
                            onChange={(e) => handleUpdateLine(index, 'quantity', e.target.value)}
                            className="w-20 px-2 py-1 border border-gray-300 rounded"
                            step="0.01"
                          />
                        ) : (
                          line.quantity
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{line.uom}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {editing ? (
                          <input
                            type="number"
                            value={line.unit_price}
                            onChange={(e) => handleUpdateLine(index, 'unit_price', e.target.value)}
                            className="w-24 px-2 py-1 border border-gray-300 rounded"
                            step="0.01"
                          />
                        ) : (
                          `${getCurrencySymbol()}${parseFloat(line.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                        {getCurrencySymbol()}{parseFloat(line.line_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      {po.exchange_rate && line.base_currency_line_total && (
                        <td className="px-4 py-3 text-sm font-medium text-blue-600">
                          AED {parseFloat(line.base_currency_line_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50">
                  <tr>
                    <td colSpan={po.exchange_rate ? 6 : 5} className="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                      Total Amount ({getCurrencyCode()}):
                    </td>
                    <td className="px-4 py-3 text-sm font-bold text-gray-900">
                      {getCurrencySymbol()}{parseFloat(po.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                  {po.exchange_rate && po.base_currency_total && (
                    <tr>
                      <td colSpan={6} className="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                        Total Amount (AED):
                      </td>
                      <td className="px-4 py-3 text-sm font-bold text-blue-600">
                        AED {parseFloat(po.base_currency_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  )}
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar - Right Side */}
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">PO Number:</span>
                <span className="font-medium">{po.po_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">PO Date:</span>
                <span className="font-medium">{new Date(po.po_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Currency:</span>
                <span className="font-medium">{getCurrencyCode()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Line Items:</span>
                <span className="font-medium">{po.lines.length}</span>
              </div>
              <div className="flex justify-between pt-3 border-t border-gray-200">
                <span className="text-gray-900 font-semibold">Total Amount:</span>
                <span className="text-xl font-bold text-blue-600">
                  {getCurrencySymbol()}{parseFloat(po.total_amount).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Multi-Currency Information */}
          {po.exchange_rate && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <DollarSign className="h-5 w-5 mr-2 text-gray-600" />
                Currency Details
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Transaction Currency:</span>
                  <span className="font-medium">{getCurrencySymbol()} {getCurrencyCode()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Exchange Rate:</span>
                  <span className="font-medium">{parseFloat(po.exchange_rate).toFixed(6)}</span>
                </div>
                <div className="flex justify-between pt-3 border-t border-gray-200">
                  <span className="text-gray-600">Transaction Amount:</span>
                  <span className="font-semibold text-gray-900">
                    {getCurrencySymbol()}{parseFloat(po.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                {po.base_currency_total && (
                  <div className="flex justify-between pb-3 border-b border-gray-200">
                    <span className="text-gray-600">Base Currency (AED):</span>
                    <span className="font-semibold text-blue-600">
                      AED {parseFloat(po.base_currency_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                )}
                <div className="text-xs text-gray-500 pt-2">
                  <p>Exchange rate automatically fetched from system</p>
                  <p>Base currency: AED (United Arab Emirates Dirham)</p>
                </div>
              </div>
            </div>
          )}

          {/* Workflow Timeline */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow</h3>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">Created</p>
                  <p className="text-sm text-gray-600">{new Date(po.created_at).toLocaleString()}</p>
                  <p className="text-xs text-gray-500">By: {po.created_by_name}</p>
                </div>
              </div>
              
              {po.submitted_at && (
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <Send className="h-5 w-5 text-blue-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Submitted</p>
                    <p className="text-sm text-gray-600">{new Date(po.submitted_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
              
              {po.approved_at && (
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Approved</p>
                    <p className="text-sm text-gray-600">{new Date(po.approved_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
              
              {po.confirmed_at && (
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center">
                      <Send className="h-5 w-5 text-purple-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Confirmed & Sent</p>
                    <p className="text-sm text-gray-600">{new Date(po.confirmed_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* File Attachments Section */}
        {po.id > 0 ? (
          // Existing PO - show permanent attachments
          <div className="bg-white shadow-sm rounded-lg p-6 mt-6">
            <FileAttachment
              documentType="PO"
              documentId={po.id}
            />
          </div>
        ) : (
          // New PO - show temporary attachments
          <div className="bg-white shadow-sm rounded-lg p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">Attachments</h3>
            <p className="text-sm text-gray-600 mb-4">
              Upload files here. They will be attached to the PO once it's saved.
            </p>
            <TempFileAttachment tempSession={tempSession} />
          </div>
        )}
      </div>
    </div>
  );
}
