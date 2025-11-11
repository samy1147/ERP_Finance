'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { prHeadersAPI } from '../../../../../services/procurement-api';
import { ArrowLeft, Package, ShoppingCart, CheckCircle2, AlertCircle, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface PRLine {
  pr_line_id: number;
  pr_number: string;
  pr_line_number: number;
  item_description: string;
  specifications: string;
  quantity_requested: string;
  quantity_converted: string;
  quantity_remaining: string;
  unit_of_measure: string;
  estimated_unit_price: string;
  need_by_date: string;
  suggested_supplier: string | null;
  conversion_status: string;
  catalog_item: string | null;
}

interface ConvertibleLinesResponse {
  count: number;
  lines: PRLine[];
}

interface LineSelection {
  pr_line_id: number;
  quantity: number;
  unit_price: number;
  notes: string;
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ConvertToPOPage({ params }: PageProps) {
  const router = useRouter();
  const [prId, setPrId] = React.useState<string | null>(null);
  const [prHeader, setPRHeader] = useState<any>(null);
  const [availableLines, setAvailableLines] = useState<PRLine[]>([]);
  const [selectedLines, setSelectedLines] = useState<Map<number, LineSelection>>(new Map());
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);

  // PO Form fields
  const [vendorName, setVendorName] = useState('');
  const [vendorEmail, setVendorEmail] = useState('');
  const [vendorPhone, setVendorPhone] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [paymentTerms, setPaymentTerms] = useState('NET_30');

  useEffect(() => {
    const initializeParams = async () => {
      const resolvedParams = await params;
      setPrId(resolvedParams.id);
    };
    initializeParams();
  }, [params]);

  useEffect(() => {
    if (prId) {
      fetchPRDetails();
      fetchConvertibleLines();
    }
  }, [prId]);

  const fetchPRDetails = async () => {
    if (!prId) return;
    try {
      const response = await prHeadersAPI.retrieve(parseInt(prId));
      setPRHeader(response.data);
      
      // Pre-fill vendor if suggested supplier exists
      if (response.data.lines?.[0]?.suggested_supplier) {
        setVendorName(response.data.lines[0].suggested_supplier);
      }
    } catch (error) {
      toast.error('Failed to load PR details');
      console.error(error);
    }
  };

  const fetchConvertibleLines = async () => {
    if (!prId) return;
    try {
      setLoading(true);
      const response = await prHeadersAPI.getConvertibleLines([parseInt(prId)]);
      const data: ConvertibleLinesResponse = response.data;
      setAvailableLines(data.lines || []);
    } catch (error) {
      toast.error('Failed to load convertible lines');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleLineToggle = (line: PRLine) => {
    const newSelected = new Map(selectedLines);
    
    if (newSelected.has(line.pr_line_id)) {
      newSelected.delete(line.pr_line_id);
    } else {
      newSelected.set(line.pr_line_id, {
        pr_line_id: line.pr_line_id,
        quantity: parseFloat(line.quantity_remaining),
        unit_price: parseFloat(line.estimated_unit_price),
        notes: ''
      });
    }
    
    setSelectedLines(newSelected);
  };

  const handleQuantityChange = (lineId: number, quantity: number) => {
    const newSelected = new Map(selectedLines);
    const selection = newSelected.get(lineId);
    if (selection) {
      selection.quantity = quantity;
      newSelected.set(lineId, selection);
      setSelectedLines(newSelected);
    }
  };

  const handlePriceChange = (lineId: number, price: number) => {
    const newSelected = new Map(selectedLines);
    const selection = newSelected.get(lineId);
    if (selection) {
      selection.unit_price = price;
      newSelected.set(lineId, selection);
      setSelectedLines(newSelected);
    }
  };

  const handleNotesChange = (lineId: number, notes: string) => {
    const newSelected = new Map(selectedLines);
    const selection = newSelected.get(lineId);
    if (selection) {
      selection.notes = notes;
      newSelected.set(lineId, selection);
      setSelectedLines(newSelected);
    }
  };

  const calculateTotal = () => {
    let total = 0;
    selectedLines.forEach((selection) => {
      total += selection.quantity * selection.unit_price;
    });
    return total;
  };

  const handleConvert = async () => {
    if (selectedLines.size === 0) {
      toast.error('Please select at least one line to convert');
      return;
    }

    if (!vendorName.trim()) {
      toast.error('Vendor name is required');
      return;
    }

    try {
      setConverting(true);
      
      const conversionData = {
        pr_line_selections: Array.from(selectedLines.values()),
        vendor_name: vendorName,
        vendor_email: vendorEmail,
        vendor_phone: vendorPhone,
        delivery_date: deliveryDate || null,
        delivery_address: deliveryAddress,
        special_instructions: specialInstructions,
        payment_terms: paymentTerms
      };

      const response = await prHeadersAPI.convertLinesToPO(conversionData);
      
      toast.success(`Successfully created PO: ${response.data.po.po_number}`);
      
      // Redirect to the new PO or back to PR detail
      setTimeout(() => {
        if (prId) {
          router.push(`/procurement/requisitions/${prId}`);
        }
      }, 1500);
      
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to convert to PO';
      toast.error(errorMsg);
      console.error(error);
    } finally {
      setConverting(false);
    }
  };

  const getConversionStatusBadge = (status: string) => {
    const styles = {
      NOT_CONVERTED: 'bg-gray-100 text-gray-800',
      PARTIALLY_CONVERTED: 'bg-orange-100 text-orange-800',
      FULLY_CONVERTED: 'bg-green-100 text-green-800'
    };
    
    const labels = {
      NOT_CONVERTED: 'Not Converted',
      PARTIALLY_CONVERTED: 'Partially Converted',
      FULLY_CONVERTED: 'Fully Converted'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading convertible lines...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Link 
          href={prId ? `/procurement/requisitions/${prId}` : '/procurement/requisitions'}
          className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to PR Details
        </Link>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Convert PR to Purchase Order</h1>
            <p className="text-gray-600 mt-1">
              PR: {prHeader?.pr_number} - {prHeader?.title}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Package className="w-8 h-8 text-blue-600" />
            <ShoppingCart className="w-8 h-8 text-green-600" />
          </div>
        </div>
      </div>

      {availableLines.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">No Convertible Lines</h3>
          <p className="text-yellow-700">
            All lines from this PR have already been fully converted to POs.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Side - Line Selection */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Select PR Lines to Convert ({selectedLines.size} of {availableLines.length} selected)
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Choose the lines you want to include in the Purchase Order
                </p>
              </div>

              <div className="p-6 space-y-4">
                {availableLines.map((line) => {
                  const isSelected = selectedLines.has(line.pr_line_id);
                  const selection = selectedLines.get(line.pr_line_id);
                  const maxQuantity = parseFloat(line.quantity_remaining);

                  return (
                    <div
                      key={line.pr_line_id}
                      className={`border rounded-lg p-4 transition-all ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleLineToggle(line)}
                          className="mt-1 h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
                        />
                        
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="font-semibold text-gray-900">
                                Line {line.pr_line_number}: {line.item_description}
                              </h3>
                              {line.specifications && (
                                <p className="text-sm text-gray-600 mt-1">{line.specifications}</p>
                              )}
                            </div>
                            {getConversionStatusBadge(line.conversion_status)}
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                            <div>
                              <span className="text-gray-600">Total Qty:</span>
                              <span className="ml-2 font-medium">{line.quantity_requested} {line.unit_of_measure}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Converted:</span>
                              <span className="ml-2 font-medium">{line.quantity_converted}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Remaining:</span>
                              <span className="ml-2 font-medium text-green-600">{line.quantity_remaining}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Est. Price:</span>
                              <span className="ml-2 font-medium">${line.estimated_unit_price}</span>
                            </div>
                          </div>

                          {isSelected && selection && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 pt-3 border-t border-blue-200">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Quantity to Convert
                                </label>
                                <input
                                  type="number"
                                  min="0.01"
                                  max={maxQuantity}
                                  step="0.01"
                                  value={selection.quantity}
                                  onChange={(e) => handleQuantityChange(line.pr_line_id, parseFloat(e.target.value))}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">Max: {maxQuantity}</p>
                              </div>
                              
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Unit Price
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  step="0.01"
                                  value={selection.unit_price}
                                  onChange={(e) => handlePriceChange(line.pr_line_id, parseFloat(e.target.value))}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                              </div>

                              <div className="md:col-span-1">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Line Total
                                </label>
                                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-md font-semibold">
                                  ${(selection.quantity * selection.unit_price).toFixed(2)}
                                </div>
                              </div>

                              <div className="md:col-span-3">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Notes (Optional)
                                </label>
                                <input
                                  type="text"
                                  value={selection.notes}
                                  onChange={(e) => handleNotesChange(line.pr_line_id, e.target.value)}
                                  placeholder="Add notes about this conversion..."
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Side - PO Details Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 sticky top-4">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Purchase Order Details</h2>
              </div>

              <div className="p-6 space-y-4">
                {/* Vendor Information */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Vendor Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={vendorName}
                    onChange={(e) => setVendorName(e.target.value)}
                    placeholder="Enter vendor name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Vendor Email
                  </label>
                  <input
                    type="email"
                    value={vendorEmail}
                    onChange={(e) => setVendorEmail(e.target.value)}
                    placeholder="vendor@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Vendor Phone
                  </label>
                  <input
                    type="tel"
                    value={vendorPhone}
                    onChange={(e) => setVendorPhone(e.target.value)}
                    placeholder="+1-555-0100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Delivery Details */}
                <div className="pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Delivery Details</h3>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Delivery Date
                      </label>
                      <input
                        type="date"
                        value={deliveryDate}
                        onChange={(e) => setDeliveryDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Delivery Address
                      </label>
                      <textarea
                        value={deliveryAddress}
                        onChange={(e) => setDeliveryAddress(e.target.value)}
                        placeholder="Enter delivery address"
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Payment Terms */}
                <div className="pt-4 border-t border-gray-200">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payment Terms
                  </label>
                  <select
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="NET_30">Net 30</option>
                    <option value="NET_60">Net 60</option>
                    <option value="NET_90">Net 90</option>
                    <option value="COD">Cash on Delivery</option>
                    <option value="CIA">Cash in Advance</option>
                    <option value="DUE_ON_RECEIPT">Due on Receipt</option>
                  </select>
                </div>

                {/* Special Instructions */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Special Instructions
                  </label>
                  <textarea
                    value={specialInstructions}
                    onChange={(e) => setSpecialInstructions(e.target.value)}
                    placeholder="Any special instructions for the vendor..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Summary */}
                <div className="pt-4 border-t border-gray-200">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Selected Lines:</span>
                      <span className="font-semibold">{selectedLines.size}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold">
                      <span className="text-gray-900">Total Amount:</span>
                      <span className="text-blue-600">${calculateTotal().toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-4 space-y-2">
                  <button
                    onClick={handleConvert}
                    disabled={converting || selectedLines.size === 0 || !vendorName.trim()}
                    className="w-full bg-blue-600 text-white px-4 py-3 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold flex items-center justify-center gap-2"
                  >
                    {converting ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Converting...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-5 h-5" />
                        Create Purchase Order
                      </>
                    )}
                  </button>

                  <Link
                    href={prId ? `/procurement/requisitions/${prId}` : '/procurement/requisitions'}
                    className="w-full bg-gray-100 text-gray-700 px-4 py-3 rounded-md hover:bg-gray-200 font-semibold flex items-center justify-center gap-2"
                  >
                    Cancel
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
