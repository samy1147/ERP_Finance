'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { prHeadersAPI } from '../../../services/procurement-api';
import { suppliersAPI } from '../../../services/api';
import { Package, ShoppingCart, CheckCircle2, AlertCircle, Filter, Search } from 'lucide-react';
import toast from 'react-hot-toast';

interface PRLine {
  pr_line_id: number;
  pr_number: string;
  pr_header_id: number;
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
  requester_name: string;
  cost_center: string;
}

interface LineSelection {
  pr_line_id: number;
  quantity: number;
  unit_price: number;
  notes: string;
}

interface SupplierData {
  id: number;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  country?: string;
  is_active: boolean;
}

export default function PRToPOPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [allLines, setAllLines] = useState<PRLine[]>([]);
  const [filteredLines, setFilteredLines] = useState<PRLine[]>([]);
  const [selectedLines, setSelectedLines] = useState<Map<number, LineSelection>>(new Map());

  // Suppliers
  const [suppliers, setSuppliers] = useState<SupplierData[]>([]);
  const [selectedSupplier, setSelectedSupplier] = useState<number | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBySupplier, setFilterBySupplier] = useState('');
  const [filterByPR, setFilterByPR] = useState('');
  const [showOnlyPartial, setShowOnlyPartial] = useState(false);

  // PO Form fields
  const [poTitle, setPoTitle] = useState('');
  const [vendorName, setVendorName] = useState('');
  const [vendorEmail, setVendorEmail] = useState('');
  const [vendorPhone, setVendorPhone] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [paymentTerms, setPaymentTerms] = useState('NET_30');

  useEffect(() => {
    fetchAllConvertibleLines();
    fetchSuppliers();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, filterBySupplier, filterByPR, showOnlyPartial, allLines]);

  const fetchSuppliers = async () => {
    try {
      const response = await suppliersAPI.list();
      // Filter only active suppliers
      const activeSuppliers = response.data.filter((s: SupplierData) => s.is_active);
      setSuppliers(activeSuppliers);
    } catch (error) {
      console.error('Failed to load suppliers:', error);
      toast.error('Failed to load suppliers');
    }
  };

  const handleSupplierChange = (supplierId: string) => {
    if (!supplierId) {
      setSelectedSupplier(null);
      setVendorName('');
      setVendorEmail('');
      setVendorPhone('');
      return;
    }

    const supplier = suppliers.find(s => s.id === parseInt(supplierId));
    if (supplier) {
      setSelectedSupplier(supplier.id);
      setVendorName(supplier.name);
      setVendorEmail(supplier.email || '');
      setVendorPhone(supplier.phone || '');
      
      // Auto-fill delivery address if available
      const address = [
        supplier.address_line1,
        supplier.address_line2,
        supplier.city,
        supplier.country
      ].filter(Boolean).join(', ');
      
      if (address && !deliveryAddress) {
        setDeliveryAddress(address);
      }
    }
  };

  const fetchAllConvertibleLines = async () => {
    try {
      setLoading(true);
      // Get all convertible lines from all PRs
      const response = await prHeadersAPI.getConvertibleLines([]);
      const data = response.data;
      setAllLines(data.lines || []);
      setFilteredLines(data.lines || []);
    } catch (error) {
      toast.error('Failed to load PR lines');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allLines];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(line =>
        line.item_description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        line.pr_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        line.specifications?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Supplier filter
    if (filterBySupplier) {
      filtered = filtered.filter(line =>
        line.suggested_supplier?.toLowerCase().includes(filterBySupplier.toLowerCase())
      );
    }

    // PR filter
    if (filterByPR) {
      filtered = filtered.filter(line =>
        line.pr_number.toLowerCase().includes(filterByPR.toLowerCase())
      );
    }

    // Show only partially converted
    if (showOnlyPartial) {
      filtered = filtered.filter(line =>
        line.conversion_status === 'PARTIALLY_CONVERTED'
      );
    }

    setFilteredLines(filtered);
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

  const handleSelectAll = () => {
    const newSelected = new Map(selectedLines);
    filteredLines.forEach(line => {
      if (!newSelected.has(line.pr_line_id)) {
        newSelected.set(line.pr_line_id, {
          pr_line_id: line.pr_line_id,
          quantity: parseFloat(line.quantity_remaining),
          unit_price: parseFloat(line.estimated_unit_price),
          notes: ''
        });
      }
    });
    setSelectedLines(newSelected);
  };

  const handleDeselectAll = () => {
    setSelectedLines(new Map());
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

  const getUniquePRs = () => {
    const prMap = new Map<number, string>();
    allLines.forEach(line => {
      prMap.set(line.pr_header_id, line.pr_number);
    });
    return Array.from(prMap.entries());
  };

  const getUniqueSuppliers = () => {
    const suppliers = new Set<string>();
    allLines.forEach(line => {
      if (line.suggested_supplier) {
        suppliers.add(line.suggested_supplier);
      }
    });
    return Array.from(suppliers);
  };

  const handleConvert = async () => {
    if (selectedLines.size === 0) {
      toast.error('Please select at least one line to convert');
      return;
    }

    if (!poTitle.trim()) {
      toast.error('PO Title is required');
      return;
    }

    try {
      setConverting(true);
      
      const conversionData = {
        pr_line_selections: Array.from(selectedLines.values()),
        title: poTitle,
      };

      const response = await prHeadersAPI.convertLinesToPO(conversionData);
      
      toast.success(
        `Successfully created PO Draft: ${response.data.po.po_number}`,
        { duration: 4000 }
      );
      
      // Show message about next steps
      toast.success(
        'You can now view and finalize the PO in the Purchase Orders page',
        { duration: 6000 }
      );
      
      // Clear selections and refresh lines
      setSelectedLines(new Map());
      await fetchAllConvertibleLines();
      
      // Reset form
      setPoTitle('');
      
      // Optionally redirect to PO page after 2 seconds
      setTimeout(() => {
        if (window.confirm('Would you like to view the created PO now?')) {
          router.push(`/procurement/purchase-orders/${response.data.po.id}`);
        }
      }, 2000);
      
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
          <p className="mt-4 text-gray-600">Loading approved PR lines...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-[1800px]">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Convert PR Lines to Purchase Order Draft</h1>
            <p className="text-gray-600 mt-1">
              Select lines from approved PRs and convert them to a PO Draft. You can finalize the PO in the Purchase Orders page.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Package className="w-8 h-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-400">→</span>
            <ShoppingCart className="w-8 h-8 text-green-600" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Items
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search description, PR..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by PR
            </label>
            <select
              value={filterByPR}
              onChange={(e) => setFilterByPR(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All PRs</option>
              {getUniquePRs().map(([id, prNumber]) => (
                <option key={id} value={prNumber}>{prNumber}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Supplier
            </label>
            <select
              value={filterBySupplier}
              onChange={(e) => setFilterBySupplier(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Suppliers</option>
              {getUniqueSuppliers().map(supplier => (
                <option key={supplier} value={supplier}>{supplier}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={showOnlyPartial}
                onChange={(e) => setShowOnlyPartial(e.target.checked)}
                className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                Show only partially converted
              </span>
            </label>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing <span className="font-semibold">{filteredLines.length}</span> of <span className="font-semibold">{allLines.length}</span> lines
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              Select All Filtered
            </button>
            <button
              onClick={handleDeselectAll}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              Deselect All
            </button>
          </div>
        </div>
      </div>

      {filteredLines.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">No Lines Available</h3>
          <p className="text-yellow-700">
            {allLines.length === 0 
              ? "No approved PR lines available for conversion. Create and approve some PRs first."
              : "No lines match your current filters. Try adjusting the filters."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Side - Line Selection */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Available PR Lines ({selectedLines.size} selected)
                </h2>
                <div className="text-sm text-gray-600">
                  Select lines from any PR to create a PO
                </div>
              </div>

              <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto">
                {filteredLines.map((line) => {
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
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                  {line.pr_number}
                                </span>
                                <span className="text-xs text-gray-600">
                                  Line {line.pr_line_number}
                                </span>
                              </div>
                              <h3 className="font-semibold text-gray-900">
                                {line.item_description}
                              </h3>
                              {line.specifications && (
                                <p className="text-sm text-gray-600 mt-1">{line.specifications}</p>
                              )}
                            </div>
                            {getConversionStatusBadge(line.conversion_status)}
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm mb-3">
                            <div>
                              <span className="text-gray-600">Requester:</span>
                              <span className="ml-2 font-medium block">{line.requester_name}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Total Qty:</span>
                              <span className="ml-2 font-medium block">{line.quantity_requested} {line.unit_of_measure}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Converted:</span>
                              <span className="ml-2 font-medium block">{line.quantity_converted}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Remaining:</span>
                              <span className="ml-2 font-medium text-green-600 block">{line.quantity_remaining}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Est. Price:</span>
                              <span className="ml-2 font-medium block">${line.estimated_unit_price}</span>
                            </div>
                          </div>

                          {line.suggested_supplier && (
                            <div className="text-sm mb-3">
                              <span className="text-gray-600">Suggested Supplier:</span>
                              <span className="ml-2 font-medium">{line.suggested_supplier}</span>
                            </div>
                          )}

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
                <h2 className="text-lg font-semibold text-gray-900">Create PO Draft</h2>
              </div>

              <div className="p-6 space-y-4">
                {/* PO Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    PO Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={poTitle}
                    onChange={(e) => setPoTitle(e.target.value)}
                    placeholder="e.g., Office Supplies Order - Q4 2024"
                    className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Give your PO a descriptive title to identify it easily
                  </p>
                </div>

                {/* Summary */}
                <div className="pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Conversion Summary</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Selected Lines:</span>
                      <span className="font-semibold text-gray-900">{selectedLines.size}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">From PRs:</span>
                      <span className="font-semibold text-gray-900">
                        {new Set(Array.from(selectedLines.keys()).map(id => {
                          const line = allLines.find(l => l.pr_line_id === id);
                          return line?.pr_number;
                        })).size}
                      </span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-gray-200">
                      <span className="text-gray-900 font-medium">Estimated Total:</span>
                      <span className="text-xl font-bold text-blue-600">${calculateTotal().toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800">
                      <p className="font-semibold mb-1">What happens next?</p>
                      <ul className="space-y-1 text-xs">
                        <li>• PO will be created in <strong>DRAFT</strong> status</li>
                        <li>• You can add vendor details in the PO page</li>
                        <li>• Review and finalize before submitting</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                <div className="pt-4 space-y-2">
                  <button
                    onClick={handleConvert}
                    disabled={converting || selectedLines.size === 0 || !poTitle.trim()}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed font-semibold flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all"
                  >
                    {converting ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Converting to PO Draft...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-5 h-5" />
                        Convert to PO Draft
                      </>
                    )}
                  </button>
                  
                  {(!poTitle.trim() && selectedLines.size > 0) && (
                    <p className="text-xs text-red-600 text-center">
                      Please enter a PO title to continue
                    </p>
                  )}
                  
                  {(selectedLines.size === 0) && (
                    <p className="text-xs text-gray-500 text-center">
                      Select at least one PR line to convert
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
