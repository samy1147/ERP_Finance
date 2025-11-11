'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { prHeadersAPI, prLinesAPI, catalogItemsAPI } from '../../../../services/procurement-api';
import { attachmentsAPI } from '../../../../services/api';
import { ArrowLeft, Plus, Trash2, Search, DollarSign, Calendar, Building2, FolderOpen, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import TempFileAttachment from '@/components/TempFileAttachment';

interface PRLine {
  id?: string;
  item_id?: number;
  item_code?: string;
  item_name?: string;
  item_description: string;
  specifications?: string;
  quantity: string;
  estimated_unit_price: string;
  unit_of_measure: number; // UOM ID, not string
  need_by_date: string;
  catalog_item_id?: number;
  line_total?: string;
  item_type?: 'CATEGORIZED' | 'NON_CATEGORIZED'; // New field
}

interface CostCenter {
  id: number;
  code: string;
  name: string;
  annual_budget: string;
  available_budget?: string;
}

interface Project {
  id: number;
  code: string;
  name: string;
  status: string;
}

interface UnitOfMeasure {
  id: number;
  code: string;
  name: string;
}

interface CatalogItem {
  id: number;
  item_code: string;
  name: string;
  short_description?: string;
  list_price: string;
  uom_code?: string;
  supplier_name?: string;
  unit_of_measure: number;
}

export default function NewRequisitionPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [unitsOfMeasure, setUnitsOfMeasure] = useState<UnitOfMeasure[]>([]);
  const [checkingBudget, setCheckingBudget] = useState(false);
  const [budgetAvailable, setBudgetAvailable] = useState<boolean | null>(null);
  const [availableAmount, setAvailableAmount] = useState<string>('0.00');
  
  // Catalog search state
  const [catalogItems, setCatalogItems] = useState<CatalogItem[]>([]);
  const [searchingCatalog, setSearchingCatalog] = useState(false);
  const [showCatalogModal, setShowCatalogModal] = useState(false);
  const [selectedLineForCatalog, setSelectedLineForCatalog] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    cost_center_id: '',
    project_id: '',
    priority: 'NORMAL',
    pr_type: 'UNCATEGORIZED_GOODS', // Updated default
    justification: '',
    notes: '',
  });

  const [lines, setLines] = useState<PRLine[]>([
    {
      id: Math.random().toString(36).substr(2, 9),
      item_description: '',
      quantity: '1',
      estimated_unit_price: '0.00',
      unit_of_measure: 1, // Default to 'PCS' (ID: 1)
      need_by_date: new Date().toISOString().split('T')[0],
      specifications: '',
      line_total: '0.00',
      item_type: 'NON_CATEGORIZED', // Default to non-categorized
    },
  ]);

  // Generate unique session ID for temporary file uploads
  const [tempSession] = useState(() => `pr_temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    fetchCostCenters();
    fetchProjects();
    fetchUnitsOfMeasure();
  }, []);

  const fetchCostCenters = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/procurement/requisitions/cost-centers/');
      const data = await response.json();
      setCostCenters(data.results || data);
    } catch (error) {
      console.error('Failed to load cost centers', error);
      toast.error('Failed to load cost centers');
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/procurement/requisitions/projects/');
      const data = await response.json();
      setProjects(data.results || data);
    } catch (error) {
      console.error('Failed to load projects', error);
    }
  };

  const fetchUnitsOfMeasure = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8007/api/procurement/catalog/units-of-measure/');
      const data = await response.json();
      setUnitsOfMeasure(data.results || data);
    } catch (error) {
      console.error('Failed to load units of measure', error);
      // Set default if API fails
      setUnitsOfMeasure([
        { id: 1, code: 'PCS', name: 'Pieces' },
        { id: 2, code: 'EA', name: 'Each' }
      ]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLineChange = (id: string, field: keyof PRLine, value: string) => {
    setLines(prev => prev.map(line => {
      if (line.id === id) {
        // Convert value to appropriate type
        let fieldValue: any = value;
        if (field === 'unit_of_measure') {
          fieldValue = parseInt(value);
        }
        
        const updatedLine = { ...line, [field]: fieldValue };
        
        // Auto-calculate line total
        if (field === 'quantity' || field === 'estimated_unit_price') {
          const qty = parseFloat(field === 'quantity' ? value : updatedLine.quantity) || 0;
          const price = parseFloat(field === 'estimated_unit_price' ? value : updatedLine.estimated_unit_price) || 0;
          updatedLine.line_total = (qty * price).toFixed(2);
        }
        
        return updatedLine;
      }
      return line;
    }));
  };

  const addLine = () => {
    setLines(prev => [...prev, {
      id: Math.random().toString(36).substr(2, 9),
      item_description: '',
      quantity: '1',
      estimated_unit_price: '0.00',
      unit_of_measure: 1, // Default to 'PCS' (ID: 1)
      need_by_date: new Date().toISOString().split('T')[0],
      specifications: '',
      line_total: '0.00',
      item_type: 'NON_CATEGORIZED', // Default to non-categorized
    }]);
  };

  const removeLine = (id: string) => {
    if (lines.length === 1) {
      toast.error('At least one line item is required');
      return;
    }
    setLines(prev => prev.filter(line => line.id !== id));
  };

  const searchCatalog = async (searchTerm: string = '') => {
    setSearchingCatalog(true);
    try {
      // If search term is empty or too short, fetch all items
      const params = searchTerm && searchTerm.length >= 2 ? { search: searchTerm } : {};
      const response = await catalogItemsAPI.list(params);
      const items = Array.isArray(response.data) ? response.data : response.data.results || [];
      setCatalogItems(items);
    } catch (error) {
      console.error('Failed to search catalog', error);
      toast.error('Failed to search catalog items');
      setCatalogItems([]);
    } finally {
      setSearchingCatalog(false);
    }
  };

  const openCatalogBrowser = (lineId: string) => {
    setSelectedLineForCatalog(lineId);
    setShowCatalogModal(true);
    searchCatalog(); // Load all items initially
  };

  const selectCatalogItem = (item: CatalogItem) => {
    if (!selectedLineForCatalog) return;

    setLines(prev => prev.map(line => {
      if (line.id === selectedLineForCatalog) {
        const updatedLine = {
          ...line,
          catalog_item_id: item.id,
          item_code: item.item_code,
          item_name: item.name,
          // Prefer short_description when available, otherwise use the name
          item_description: item.short_description || item.name,
          estimated_unit_price: item.list_price,
          unit_of_measure: item.unit_of_measure,
          item_type: 'CATEGORIZED' as const,
        };
        
        // Recalculate line total
        const qty = parseFloat(updatedLine.quantity) || 0;
        const price = parseFloat(updatedLine.estimated_unit_price) || 0;
        updatedLine.line_total = (qty * price).toFixed(2);
        
        return updatedLine;
      }
      return line;
    }));

    setShowCatalogModal(false);
    setSelectedLineForCatalog(null);
    toast.success(`Selected: ${item.name}`);
  };

  const calculateTotal = () => {
    return lines.reduce((sum, line) => sum + (parseFloat(line.line_total || '0') || 0), 0).toFixed(2);
  };

  const handleCheckBudget = async () => {
    if (!formData.cost_center_id) {
      toast('Budget check is only available when a cost center is selected', {
        icon: 'ℹ️',
      });
      return;
    }

    setCheckingBudget(true);
    try {
      const costCenter = costCenters.find(cc => cc.id === parseInt(formData.cost_center_id));
      if (costCenter) {
        const total = parseFloat(calculateTotal());
        const response = await fetch(`http://127.0.0.1:8007/api/procurement/requisitions/cost-centers/${costCenter.id}/utilization/`);
        const data = await response.json();
        
        const available = parseFloat(data.available_amount || '0');
        setAvailableAmount(available.toFixed(2));
        
        if (available >= total) {
          setBudgetAvailable(true);
          toast.success(`Budget available: $${available.toFixed(2)}`);
        } else {
          setBudgetAvailable(false);
          toast.error(`Insufficient budget. Need: $${total.toFixed(2)}, Available: $${available.toFixed(2)}`);
        }
      }
    } catch (error) {
      console.error('Budget check failed', error);
      toast.error('Failed to check budget');
    } finally {
      setCheckingBudget(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title.trim()) {
      toast.error('Title is required');
      return;
    }

    if (lines.length === 0 || !lines.some(line => line.item_description.trim())) {
      toast.error('At least one line item with description is required');
      return;
    }

    const invalidLines = lines.filter(line => 
      !line.item_description.trim() || 
      parseFloat(line.quantity) <= 0 || 
      parseFloat(line.estimated_unit_price) <= 0
    );

    if (invalidLines.length > 0) {
      toast.error('Please fill all required fields in line items (description, quantity > 0, price > 0)');
      return;
    }

    setLoading(true);

    try {
      // Get current user ID (you may need to fetch this from auth context)
      // Using user ID 2 (admin) - exists in database
      const userId = 2; // TODO: Get from auth context
      
      // Get default currency ID - 1 = USD
      const currencyId = 1; // USD
      
      const prData = {
        title: formData.title,
        description: formData.description,
        requestor: userId,
        cost_center: formData.cost_center_id ? parseInt(formData.cost_center_id) : null,
        project: formData.project_id ? parseInt(formData.project_id) : null,
        priority: formData.priority,
        pr_type: formData.pr_type, // Include PR type
        business_justification: formData.justification,
        internal_notes: formData.notes,
        currency: currencyId,
        required_date: new Date(new Date().setDate(new Date().getDate() + 30)).toISOString().split('T')[0], // 30 days from now
        lines: lines.map((line, index) => ({
          line_number: index + 1,
          item_description: line.item_description,
          specifications: line.specifications || '',
          quantity: parseFloat(line.quantity),
          unit_of_measure: parseInt(line.unit_of_measure.toString()), // Ensure it's an integer ID
          estimated_unit_price: parseFloat(line.estimated_unit_price),
          need_by_date: line.need_by_date,
        })),
      };

      const response = await prHeadersAPI.create(prData);
      
      // Link temporary attachments to the newly created PR
      try {
        await attachmentsAPI.linkToPR(tempSession, response.data.id);
      } catch (attachError) {
        console.error('Failed to link attachments:', attachError);
        // Don't fail the whole operation if attachment linking fails
      }
      
      toast.success(`Purchase Requisition ${response.data.pr_number} created successfully!`);
      
      // Redirect to PR detail or list
      router.push('/procurement/requisitions');
    } catch (error: any) {
      console.error('Failed to create PR', error);
      console.error('Error details:', error.response?.data);
      const errorMsg = error.response?.data?.error || error.response?.data?.message || JSON.stringify(error.response?.data) || 'Failed to create purchase requisition';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/procurement/requisitions"
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft size={20} />
          <span>Back to Requisitions</span>
        </Link>
        
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">New Purchase Requisition</h1>
            <p className="text-gray-600">Create a new purchase request</p>
          </div>
          
          {budgetAvailable !== null && (
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              budgetAvailable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <DollarSign size={20} />
              <span className="font-semibold">
                {budgetAvailable ? 'Budget Available' : 'Insufficient Budget'}
              </span>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Main Form Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FolderOpen size={20} />
            Requisition Details
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Title */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Office Supplies Q4 2025"
                required
              />
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Additional details about this requisition..."
              />
            </div>

            {/* Cost Center */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cost Center (Optional)
              </label>
              <select
                name="cost_center_id"
                value={formData.cost_center_id}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">None / Select Cost Center</option>
                {costCenters.map(cc => (
                  <option key={cc.id} value={cc.id}>
                    {cc.code} - {cc.name} (Budget: ${parseFloat(cc.annual_budget).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>

            {/* Project */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project (Optional)
              </label>
              <select
                name="project_id"
                value={formData.project_id}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">None</option>
                {projects.filter(p => p.status === 'ACTIVE').map(project => (
                  <option key={project.id} value={project.id}>
                    {project.code} - {project.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>

            {/* PR Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                PR Type <span className="text-red-500">*</span>
              </label>
              <select
                name="pr_type"
                value={formData.pr_type}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="CATEGORIZED_GOODS">📋 Categorized Goods</option>
                <option value="UNCATEGORIZED_GOODS">✏️ Uncategorized Goods</option>
                <option value="SERVICES">🔧 Services</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {formData.pr_type === 'CATEGORIZED_GOODS' && '• Catalog items - posts to inventory (trackable assets)'}
                {formData.pr_type === 'UNCATEGORIZED_GOODS' && '• Consumables/supplies - posts to expenses (not tracked in inventory)'}
                {formData.pr_type === 'SERVICES' && '• Services - posts to expenses (no physical inventory)'}
              </p>
            </div>

            {/* (page-level default item type removed; per-line selection remains) */}

            {/* Budget Check Button */}
            <div className="flex items-end">
              <button
                type="button"
                onClick={handleCheckBudget}
                disabled={!formData.cost_center_id || checkingBudget}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <DollarSign size={20} />
                {checkingBudget ? 'Checking...' : 'Check Budget'}
              </button>
            </div>

            {/* Justification */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Justification
              </label>
              <textarea
                name="justification"
                value={formData.justification}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Explain the business need for this requisition..."
              />
            </div>

            {/* Notes */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes
              </label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Any additional information..."
              />
            </div>
          </div>
        </div>

        {/* Line Items Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Building2 size={20} />
              Line Items
            </h2>
            <button
              type="button"
              onClick={addLine}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              Add Line
            </button>
          </div>

          <div className="space-y-4">
            {lines.map((line, index) => (
              <div key={line.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-700">Line {index + 1}</h3>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      line.item_type === 'CATEGORIZED' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-200 text-gray-700'
                    }`}>
                      {line.item_type === 'CATEGORIZED' ? '📦 Catalog' : '✏️ Custom'}
                    </span>
                  </div>
                  {lines.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeLine(line.id!)}
                      className="text-red-600 hover:text-red-700 p-1"
                    >
                      <Trash2 size={20} />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Item Type Selection */}
                  <div className="lg:col-span-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Item Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={line.item_type || 'NON_CATEGORIZED'}
                      onChange={(e) => handleLineChange(line.id!, 'item_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                    >
                      <option value="NON_CATEGORIZED">Non-Categorized (Custom Item)</option>
                      <option value="CATEGORIZED">Categorized (From Catalog)</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      {line.item_type === 'CATEGORIZED' 
                        ? '✓ This item will be linked to the catalog for tracking and pricing'
                        : '⚠ This is a custom item not in the catalog'}
                    </p>
                  </div>

                  {/* When categorized, show catalog code and name (read-only) */}
                  {line.item_type === 'CATEGORIZED' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Item Code</label>
                        <input
                          type="text"
                          value={line.item_code || ''}
                          readOnly
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
                        <input
                          type="text"
                          value={line.item_name || ''}
                          readOnly
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100"
                        />
                      </div>
                    </>
                  )}

                  {/* Description with Browse Catalog Button */}
                  <div className="lg:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description <span className="text-red-500">*</span>
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={line.item_description}
                        onChange={(e) => handleLineChange(line.id!, 'item_description', e.target.value)}
                        readOnly={line.item_type === 'CATEGORIZED'}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder={line.item_type === 'CATEGORIZED' ? 'Select from catalog or use Browse' : 'Item description'}
                        required
                      />
                      {line.item_type === 'CATEGORIZED' && (
                        <button
                          type="button"
                          onClick={() => openCatalogBrowser(line.id!)}
                          className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1"
                          title="Browse Catalog"
                        >
                          <Package size={16} />
                          Browse
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Quantity */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={line.quantity}
                      onChange={(e) => handleLineChange(line.id!, 'quantity', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>

                  {/* UoM */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      UoM
                    </label>
                    <select
                      value={line.unit_of_measure}
                      onChange={(e) => handleLineChange(line.id!, 'unit_of_measure', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {unitsOfMeasure.map(uom => (
                        <option key={uom.id} value={uom.id}>
                          {uom.name} ({uom.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Unit Price */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Est. Unit Price <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={line.estimated_unit_price}
                      onChange={(e) => handleLineChange(line.id!, 'estimated_unit_price', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>

                  {/* Need By Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Need By Date
                    </label>
                    <input
                      type="date"
                      value={line.need_by_date}
                      onChange={(e) => handleLineChange(line.id!, 'need_by_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>

                  {/* Line Total */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Line Total
                    </label>
                    <input
                      type="text"
                      value={`$${line.line_total}`}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 font-semibold"
                    />
                  </div>

                  {/* Specification */}
                  <div className="lg:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Specification
                    </label>
                    <input
                      type="text"
                      value={line.specifications || ''}
                      onChange={(e) => handleLineChange(line.id!, 'specifications', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Technical specifications, brand preferences, etc."
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Total */}
          <div className="mt-6 flex justify-end">
            <div className="bg-blue-50 px-6 py-4 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Total Estimated Amount</div>
              <div className="text-3xl font-bold text-blue-600">${calculateTotal()}</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        {/* File Attachments Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <TempFileAttachment tempSession={tempSession} />
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4">
          <Link
            href="/procurement/requisitions"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating...' : 'Create Requisition'}
          </button>
        </div>
      </form>

      {/* Catalog Browser Modal */}
      {showCatalogModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <Package size={24} />
                  Browse Catalog
                </h2>
                <button
                  onClick={() => {
                    setShowCatalogModal(false);
                    setSelectedLineForCatalog(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <span className="text-2xl">&times;</span>
                </button>
              </div>
              
              {/* Search Bar */}
              <div className="mt-4 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search catalog items by name or code..."
                  onChange={(e) => searchCatalog(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Modal Body - Catalog Items List */}
            <div className="flex-1 overflow-y-auto p-6">
              {searchingCatalog ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : catalogItems.length === 0 ? (
                <div className="text-center py-12">
                  <Package size={48} className="mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600">No catalog items found. Try a different search term.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {catalogItems.map((item) => (
                    <div
                      key={item.id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
                      onClick={() => selectCatalogItem(item)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900">{item.name}</h3>
                          <p className="text-sm text-gray-500">Code: {item.item_code}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-blue-600">
                            ${parseFloat(item.list_price).toFixed(2)}
                          </div>
                          <div className="text-xs text-gray-500">{item.uom_code}</div>
                        </div>
                      </div>
                      {item.short_description && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">{item.short_description}</p>
                      )}
                      {item.supplier_name && (
                        <p className="text-xs text-gray-500">Supplier: {item.supplier_name}</p>
                      )}
                      <button
                        type="button"
                        className="mt-3 w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold"
                      >
                        Select This Item
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  {catalogItems.length} items found
                </p>
                <button
                  onClick={() => {
                    setShowCatalogModal(false);
                    setSelectedLineForCatalog(null);
                  }}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
