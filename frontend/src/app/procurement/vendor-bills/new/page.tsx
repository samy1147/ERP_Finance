'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { vendorBillsAPI, goodsReceiptsAPI } from '../../../../services/procurement-api';
import { ArrowLeft, Plus, Trash2, FileText, Calendar, DollarSign, Building2, Package, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface Supplier {
  id: number;
  name: string;
  code: string;
  payment_terms?: string;
}

interface Currency {
  id: number;
  code: string;
  name: string;
}

interface GRNForSelection {
  id: number;
  grn_number: string;
  po_number: string;
  vendor_name: string;
  receipt_date: string;
  status: string;
}

interface POLine {
  id: number;
  line_number: number;
  item_description: string;
  quantity: number;
  unit_price: string;
  received_quantity?: number;
}

interface BillLine {
  id?: string;
  po_line?: number;
  grn_line?: number;
  description: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  tax_amount: string;
  line_total: string;
}

export default function NewVendorBillPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [grns, setGRNs] = useState<GRNForSelection[]>([]);
  const [selectedGRN, setSelectedGRN] = useState<number | null>(null);
  const [grnLines, setGRNLines] = useState<any[]>([]);

  // Form state
  const [formData, setFormData] = useState({
    supplier: '',
    supplier_invoice_number: '',
    supplier_invoice_date: new Date().toISOString().split('T')[0],
    bill_date: new Date().toISOString().split('T')[0],
    due_date: '',
    currency: '1', // Default to USD or primary currency
    exchange_rate: '1.00',
    bill_type: 'STANDARD',
    payment_terms: '',
    notes: '',
    internal_notes: '',
  });

  const [lines, setLines] = useState<BillLine[]>([
    {
      id: Math.random().toString(36).substr(2, 9),
      description: '',
      quantity: '1',
      unit_price: '0.00',
      tax_rate: '0.00',
      tax_amount: '0.00',
      line_total: '0.00',
    },
  ]);

  useEffect(() => {
    fetchSuppliers();
    fetchCurrencies();
    fetchPostedGRNs();
  }, []);

  useEffect(() => {
    // Calculate due date based on payment terms (default 30 days)
    if (formData.bill_date) {
      const billDate = new Date(formData.bill_date);
      const daysToAdd = 30; // Default, could be based on supplier payment terms
      billDate.setDate(billDate.getDate() + daysToAdd);
      setFormData(prev => ({ ...prev, due_date: billDate.toISOString().split('T')[0] }));
    }
  }, [formData.bill_date]);

  const fetchSuppliers = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/ap/vendors/');
      const data = await response.json();
      setSuppliers(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load suppliers', error);
      toast.error('Failed to load suppliers');
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/currencies/');
      const data = await response.json();
      setCurrencies(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load currencies', error);
      toast.error('Failed to load currencies');
    }
  };

  const fetchPostedGRNs = async () => {
    try {
      // Fetch GRNs that need invoicing (completed and no existing invoice)
      const response = await fetch('http://127.0.0.1:8007/api/procurement/vendor-bills/bills/grns-needing-invoice/');
      const data = await response.json();
      const receipts = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : []);
      setGRNs(receipts);
      
      console.log(`Found ${receipts.length} GRNs needing invoices`);
      
      // If no GRNs need invoicing, optionally show all completed GRNs
      if (receipts.length === 0) {
        console.log('No GRNs need invoicing. Loading all completed GRNs...');
        const allResponse = await fetch('http://127.0.0.1:8007/api/procurement/receiving/receipts/?status=COMPLETED');
        const allData = await allResponse.json();
        const allReceipts = Array.isArray(allData) ? allData : allData.results || [];
        setGRNs(allReceipts);
      }
    } catch (error) {
      console.error('Failed to load GRNs needing invoice', error);
      toast.error('Failed to load goods receipts');
    }
  };

  const handleGRNSelect = async (grnId: number) => {
    if (!grnId) {
      setSelectedGRN(null);
      setGRNLines([]);
      // Reset to default line
      setLines([{
        id: Math.random().toString(36).substr(2, 9),
        description: '',
        quantity: '1',
        unit_price: '0.00',
        tax_rate: '0.00',
        tax_amount: '0.00',
        line_total: '0.00',
      }]);
      return;
    }
    
    setSelectedGRN(grnId);
    try {
      // Fetch GRN details to get lines
      const grnResponse = await fetch(`http://127.0.0.1:8007/api/procurement/receiving/receipts/${grnId}/`);
      const grnData = await grnResponse.json();
      
      console.log('GRN Data:', grnData);
      
      if (!grnData.lines || grnData.lines.length === 0) {
        toast.error('This GRN has no line items');
        return;
      }
      
      setGRNLines(grnData.lines);
      
      // Store PO header ID for linking
      if (grnData.po_header) {
        // Store po_header ID on each line for later use
        grnData.lines.forEach((line: any) => {
          line.po_header = grnData.po_header;
        });
      }
      
      // Auto-populate supplier if available
      if (grnData.supplier) {
        setFormData(prev => ({ ...prev, supplier: grnData.supplier.toString() }));
      }
      
      // Fetch PO details to get unit prices and quantities
      let poData = null;
      if (grnData.po_header) {
        const poResponse = await fetch(`http://127.0.0.1:8007/api/procurement/purchase-orders/${grnData.po_header}/`);
        poData = await poResponse.json();
        console.log('PO Data:', poData);
      }
      
      // Initialize bill lines from GRN lines with PO data
      const initialLines: BillLine[] = grnData.lines.map((grnLine: any) => {
        // Use received_quantity from GRN, if 0 then use ordered_quantity
        let quantity = parseFloat(grnLine.received_quantity || '0');
        if (quantity === 0) {
          quantity = parseFloat(grnLine.ordered_quantity || '0');
        }
        
        let unitPrice = '0.00';
        let description = grnLine.item_description || '';
        
        // Try to match with PO line
        if (poData && poData.lines && poData.lines.length > 0) {
          // Try multiple matching strategies
          const matchingPoLine = poData.lines.find((poLine: any) => 
            // Match by line number
            poLine.line_number === grnLine.line_number ||
            // Match by catalog item
            (grnLine.catalog_item && poLine.catalog_item === grnLine.catalog_item) ||
            // Match by description (partial match)
            (grnLine.item_description && poLine.item_description && 
             poLine.item_description.toLowerCase().includes(grnLine.item_description.toLowerCase()))
          );
          
          if (matchingPoLine) {
            console.log('Matched GRN line', grnLine.line_number, 'with PO line', matchingPoLine.line_number);
            unitPrice = matchingPoLine.unit_price || '0.00';
            description = matchingPoLine.item_description || description;
            
            // If GRN quantity is 0, use PO quantity as fallback
            if (quantity === 0) {
              quantity = parseFloat(matchingPoLine.quantity || '0');
            }
          } else {
            // No match found, use first PO line as fallback if only one line
            if (poData.lines.length === 1) {
              console.log('Using single PO line as fallback');
              unitPrice = poData.lines[0].unit_price || '0.00';
              if (quantity === 0) {
                quantity = parseFloat(poData.lines[0].quantity || '0');
              }
            }
          }
        }
        
        // If still no quantity, default to 1
        if (quantity === 0) {
          quantity = 1;
          console.warn('No quantity found for line, defaulting to 1');
        }
        
        const priceNum = parseFloat(unitPrice);
        const lineTotal = (quantity * priceNum).toFixed(2);
        
        return {
          id: Math.random().toString(36).substr(2, 9),
          grn_line: grnLine.id,
          po_line: null, // Will be set if matched
          description: description,
          quantity: quantity.toString(),
          unit_price: unitPrice,
          tax_rate: '0.00',
          tax_amount: '0.00',
          line_total: lineTotal,
        };
      });
      
      setLines(initialLines);
      toast.success(`Loaded ${initialLines.length} line(s) from GRN`);
    } catch (error) {
      console.error('Error fetching GRN details:', error);
      toast.error('Failed to load GRN details');
    }
  };

  const addLine = () => {
    setLines([
      ...lines,
      {
        id: Math.random().toString(36).substr(2, 9),
        description: '',
        quantity: '1',
        unit_price: '0.00',
        tax_rate: '0.00',
        tax_amount: '0.00',
        line_total: '0.00',
      },
    ]);
  };

  const removeLine = (id: string) => {
    if (lines.length === 1) {
      toast.error('At least one line is required');
      return;
    }
    setLines(lines.filter(line => line.id !== id));
  };

  const updateLine = (id: string, field: keyof BillLine, value: string) => {
    setLines(lines.map(line => {
      if (line.id === id) {
        const updated = { ...line, [field]: value };
        
        // Recalculate amounts
        if (field === 'quantity' || field === 'unit_price' || field === 'tax_rate') {
          const qty = parseFloat(updated.quantity) || 0;
          const price = parseFloat(updated.unit_price) || 0;
          const taxRate = parseFloat(updated.tax_rate) || 0;
          
          const subtotal = qty * price;
          const taxAmount = subtotal * (taxRate / 100);
          const lineTotal = subtotal + taxAmount;
          
          updated.tax_amount = taxAmount.toFixed(2);
          updated.line_total = lineTotal.toFixed(2);
        }
        
        return updated;
      }
      return line;
    }));
  };

  const calculateTotals = () => {
    const subtotal = lines.reduce((sum, line) => {
      const lineSubtotal = parseFloat(line.quantity) * parseFloat(line.unit_price);
      return sum + lineSubtotal;
    }, 0);
    
    const taxAmount = lines.reduce((sum, line) => sum + parseFloat(line.tax_amount || '0'), 0);
    const total = subtotal + taxAmount;
    
    return {
      subtotal: subtotal.toFixed(2),
      taxAmount: taxAmount.toFixed(2),
      total: total.toFixed(2),
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.supplier) {
      toast.error('Please select a supplier');
      return;
    }

    if (!formData.supplier_invoice_number) {
      toast.error('Please enter supplier invoice number');
      return;
    }

    if (lines.length === 0 || lines.every(line => !line.description)) {
      toast.error('Please add at least one line item');
      return;
    }

    try {
      setLoading(true);

      const totals = calculateTotals();
      
      const billData = {
        supplier: parseInt(formData.supplier),
        supplier_invoice_number: formData.supplier_invoice_number,
        supplier_invoice_date: formData.supplier_invoice_date,
        bill_date: formData.bill_date,
        due_date: formData.due_date,
        bill_type: formData.bill_type,
        currency: parseInt(formData.currency),
        exchange_rate: formData.exchange_rate,
        subtotal: totals.subtotal,
        tax_amount: totals.taxAmount,
        total_amount: totals.total,
        notes: formData.notes || '',
        internal_notes: formData.internal_notes || '',
        // Link to GRN and PO for 3-way match
        grn_header: selectedGRN || null,
        po_header: selectedGRN && grnLines.length > 0 && grnLines[0].po_header ? grnLines[0].po_header : null,
        lines: lines.map((line, index) => ({
          line_number: index + 1,
          description: line.description,
          quantity: parseFloat(line.quantity),
          unit_price: parseFloat(line.unit_price),
          tax_rate: parseFloat(line.tax_rate) || 0,
          tax_amount: parseFloat(line.tax_amount),
          line_total: parseFloat(line.line_total),
          po_number: line.po_line ? `PO-${line.po_line}` : '',
          po_line_number: line.po_line || null,
          grn_number: line.grn_line ? `GRN-${line.grn_line}` : '',
          notes: '',
        })),
      };

      await vendorBillsAPI.create(billData as any);
      
      toast.success('Vendor bill created successfully!');
      router.push('/procurement/vendor-bills');
    } catch (error: any) {
      console.error('Error creating vendor bill:', error);
      const errorMessage = error.response?.data?.error 
        || error.response?.data?.detail
        || error.message 
        || 'Failed to create vendor bill';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/procurement/vendor-bills"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Vendor Bills
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Create Vendor Bill</h1>
          <p className="text-gray-600 mt-2">Record a vendor invoice for goods received or services rendered</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* GRN Selection (Optional) */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Package className="h-5 w-5 mr-2 text-blue-600" />
              Link to Goods Receipt (Optional)
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Goods Receipt Needing Invoice
              </label>
              <select
                value={selectedGRN || ''}
                onChange={(e) => handleGRNSelect(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Manual Entry (No GRN Link) --</option>
                {grns.length === 0 && (
                  <option value="" disabled>No receipts needing invoices found</option>
                )}
                {grns.map(grn => (
                  <option key={grn.id} value={grn.id}>
                    {grn.grn_number} - {grn.vendor_name} - PO: {grn.po_number} - {grn.receipt_date}
                  </option>
                ))}
              </select>
              {grns.length > 0 ? (
                <p className="text-sm text-green-600 mt-2 flex items-center">
                  <Package className="h-4 w-4 mr-1" />
                  Found {grns.length} receipt{grns.length !== 1 ? 's' : ''} needing invoice{grns.length !== 1 ? 's' : ''}. Select one to auto-populate bill details.
                </p>
              ) : (
                <p className="text-sm text-gray-500 mt-2">
                  ℹ️ No goods receipts need invoicing. All completed receipts already have bills, or you can create a manual bill without a GRN link.
                </p>
              )}
              {selectedGRN && (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800 font-medium">
                    ✓ Bill will be linked to selected GRN for 3-way matching
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Bill Header */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2 text-gray-600" />
              Bill Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Supplier *
                </label>
                <select
                  value={formData.supplier}
                  onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select Supplier</option>
                  {suppliers.map(supplier => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name} ({supplier.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Supplier Invoice Number *
                </label>
                <input
                  type="text"
                  value={formData.supplier_invoice_number}
                  onChange={(e) => setFormData({ ...formData, supplier_invoice_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="INV-2025-001"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Invoice Date *
                </label>
                <input
                  type="date"
                  value={formData.supplier_invoice_date}
                  onChange={(e) => setFormData({ ...formData, supplier_invoice_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bill Date *
                </label>
                <input
                  type="date"
                  value={formData.bill_date}
                  onChange={(e) => setFormData({ ...formData, bill_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Due Date *
                </label>
                <input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bill Type
                </label>
                <select
                  value={formData.bill_type}
                  onChange={(e) => setFormData({ ...formData, bill_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="STANDARD">Standard</option>
                  <option value="CREDIT_MEMO">Credit Memo</option>
                  <option value="DEBIT_MEMO">Debit Memo</option>
                  <option value="PREPAYMENT">Prepayment</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Currency *
                </label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {currencies.map(currency => (
                    <option key={currency.id} value={currency.id}>
                      {currency.code} - {currency.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exchange Rate
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.exchange_rate}
                  onChange={(e) => setFormData({ ...formData, exchange_rate: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.000000"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="External notes visible to supplier"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Internal Notes
                </label>
                <textarea
                  value={formData.internal_notes}
                  onChange={(e) => setFormData({ ...formData, internal_notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="Internal notes for accounting team"
                />
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <DollarSign className="h-5 w-5 mr-2 text-gray-600" />
                Line Items
              </h2>
              <button
                type="button"
                onClick={addLine}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Line
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tax %</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tax Amount</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Line Total</th>
                    <th className="px-3 py-3"></th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {lines.map((line, index) => (
                    <tr key={line.id}>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={line.description}
                          onChange={(e) => updateLine(line.id!, 'description', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Item description"
                          required
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          step="0.01"
                          value={line.quantity}
                          onChange={(e) => updateLine(line.id!, 'quantity', e.target.value)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          step="0.01"
                          value={line.unit_price}
                          onChange={(e) => updateLine(line.id!, 'unit_price', e.target.value)}
                          className="w-24 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          step="0.01"
                          value={line.tax_rate}
                          onChange={(e) => updateLine(line.id!, 'tax_rate', e.target.value)}
                          className="w-16 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </td>
                      <td className="px-3 py-2 text-right text-sm text-gray-900">
                        ${line.tax_amount}
                      </td>
                      <td className="px-3 py-2 text-right text-sm font-semibold text-gray-900">
                        ${line.line_total}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => removeLine(line.id!)}
                          className="text-red-600 hover:text-red-800"
                          disabled={lines.length === 1}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="mt-6 border-t pt-4">
              <div className="flex justify-end">
                <div className="w-64 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Subtotal:</span>
                    <span className="font-medium">${totals.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tax Amount:</span>
                    <span className="font-medium">${totals.taxAmount}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2">
                    <span>Total:</span>
                    <span>${totals.total}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Link
              href="/procurement/vendor-bills"
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Vendor Bill'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
