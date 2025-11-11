'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface APInvoice {
  id: number;
  invoice_number: string;
  number?: string;
  supplier_name: string;
  date: string;
  invoice_date?: string;
  total?: string;
  total_amount?: number;
  currency_code: string;
  status?: string;
  is_posted?: boolean;
  items?: APInvoiceLine[];
}

interface APInvoiceLine {
  id?: number;
  line_number: number;
  description: string;
  item_description?: string;
  quantity: number;
  unit_price: number;
  amount?: number;
  total_amount?: number;
  account_name?: string;
}

interface Category {
  id: number;
  name: string;
  depreciation_rate: number;
  useful_life_years: number;
  depreciation_method: string;
  asset_account: number;
  depreciation_account: number;
  accumulated_depreciation_account: number;
}

interface Location {
  id: number;
  name: string;
  code: string;
}

export default function CreateAssetFromInvoice() {
  const router = useRouter();
  const [invoices, setInvoices] = useState<APInvoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<APInvoice | null>(null);
  const [invoiceLines, setInvoiceLines] = useState<APInvoiceLine[]>([]);
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [checkingConversion, setCheckingConversion] = useState(false);
  const [conversionStatus, setConversionStatus] = useState<any>(null);

  // Form data
  const [formData, setFormData] = useState({
    asset_number: '',
    name: '',
    category: '',
    location: '',
    acquisition_date: new Date().toISOString().split('T')[0],
    serial_number: '',
    description: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [invoicesRes, categoriesRes, locationsRes] = await Promise.all([
        fetch('http://localhost:8007/api/ap/invoices/'),
        fetch('http://localhost:8007/api/fixed-assets/categories/'),
        fetch('http://localhost:8007/api/fixed-assets/locations/'),
      ]);

      if (invoicesRes.ok) {
        const invoicesData = await invoicesRes.json();
        setInvoices(invoicesData);
      }
      if (categoriesRes.ok) {
        const categoriesData = await categoriesRes.json();
        setCategories(categoriesData);
      }
      if (locationsRes.ok) {
        const locationsData = await locationsRes.json();
        setLocations(locationsData);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleInvoiceSelect = async (invoice: APInvoice) => {
    setSelectedInvoice(invoice);
    setSelectedLine(null);
    setConversionStatus(null);
    setError('');

    try {
      const response = await fetch(`http://localhost:8007/api/ap/invoices/${invoice.id}/`);
      if (response.ok) {
        const data = await response.json();
        // API returns 'items' not 'lines'
        const items = data.items || data.lines || [];
        // Map items to expected format with line_number
        const mappedLines = items.map((item: any, index: number) => ({
          ...item,
          line_number: item.line_number || (index + 1),
          item_description: item.description || item.item_description || '',
        }));
        setInvoiceLines(mappedLines);
      }
    } catch (err) {
      console.error('Error fetching invoice lines:', err);
      setError('Failed to load invoice lines');
    }
  };

  const checkConversion = async (lineNumber: number) => {
    if (!selectedInvoice) return;

    setCheckingConversion(true);
    setConversionStatus(null);

    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/assets/check_source_conversion/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: 'AP_INVOICE',
          ap_invoice_id: selectedInvoice.id,
          ap_invoice_line: lineNumber,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setConversionStatus(data);
        
        if (data.already_converted) {
          setError(data.message);
        }
      }
    } catch (err) {
      console.error('Error checking conversion:', err);
      setError('Failed to check conversion status');
    } finally {
      setCheckingConversion(false);
    }
  };

  const handleLineSelect = (lineNumber: number) => {
    setSelectedLine(lineNumber);
    setError('');
    checkConversion(lineNumber);

    // Auto-populate name from line description
    const line = invoiceLines.find(l => l.line_number === lineNumber);
    if (line) {
      const description = line.description || line.item_description || '';
      setFormData(prev => ({
        ...prev,
        name: description,
        description: description,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedInvoice || selectedLine === null) {
      setError('Please select an invoice and line item');
      return;
    }

    if (conversionStatus?.already_converted) {
      setError('This invoice line has already been converted to an asset');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/assets/create_from_ap_invoice/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ap_invoice_id: selectedInvoice.id,
          line_number: selectedLine,
          asset_data: {
            ...formData,
            category: parseInt(formData.category),
            location: parseInt(formData.location),
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Asset created successfully: ${data.asset.asset_number}`);
        router.push('/fixed-assets');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create asset');
      }
    } catch (err) {
      console.error('Error creating asset:', err);
      setError('Failed to create asset from invoice');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Create Asset from AP Invoice</h1>
        <button
          onClick={() => router.push('/fixed-assets')}
          className="px-4 py-2 text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Invoice Selection */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">1. Select AP Invoice</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {invoices.map((invoice) => (
              <div
                key={invoice.id}
                onClick={() => handleInvoiceSelect(invoice)}
                className={`p-4 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedInvoice?.id === invoice.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{invoice.invoice_number || invoice.number}</div>
                    <div className="text-sm text-gray-600">{invoice.supplier_name}</div>
                    <div className="text-sm text-gray-500">{invoice.date || invoice.invoice_date}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {invoice.currency_code} {invoice.total_amount ? Number(invoice.total_amount).toFixed(2) : (invoice.total || '0.00')}
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      (invoice.status === 'posted' || invoice.is_posted) ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {invoice.is_posted ? 'posted' : (invoice.status || 'draft')}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Invoice Lines */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">2. Select Line Item</h2>
          {selectedInvoice ? (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {invoiceLines.map((line) => (
                <div
                  key={line.line_number}
                  onClick={() => handleLineSelect(line.line_number)}
                  className={`p-4 border rounded cursor-pointer hover:bg-gray-50 ${
                    selectedLine === line.line_number ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold">Line {line.line_number}</div>
                      <div className="text-sm text-gray-700">{line.description || line.item_description}</div>
                      <div className="text-sm text-gray-500">
                        Qty: {line.quantity || 0} × {selectedInvoice.currency_code} {line.unit_price ? Number(line.unit_price).toFixed(2) : '0.00'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {selectedInvoice.currency_code} {
                          line.amount ? Number(line.amount).toFixed(2) : 
                          line.total_amount ? Number(line.total_amount).toFixed(2) :
                          (line.quantity && line.unit_price) ? (Number(line.quantity) * Number(line.unit_price)).toFixed(2) : '0.00'
                        }
                      </div>
                    </div>
                  </div>
                  {selectedLine === line.line_number && checkingConversion && (
                    <div className="mt-2 text-sm text-gray-500">Checking conversion status...</div>
                  )}
                  {selectedLine === line.line_number && conversionStatus?.already_converted && (
                    <div className="mt-2 text-sm text-red-600">
                      ⚠️ Already converted to asset: {conversionStatus.asset_number}
                    </div>
                  )}
                  {selectedLine === line.line_number && conversionStatus?.can_convert && (
                    <div className="mt-2 text-sm text-green-600">
                      ✓ Available for conversion
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Select an invoice to view line items
            </div>
          )}
        </div>
      </div>

      {/* Asset Creation Form */}
      {selectedLine !== null && conversionStatus?.can_convert && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">3. Asset Details</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Asset Number *
              </label>
              <input
                type="text"
                required
                value={formData.asset_number}
                onChange={(e) => setFormData({ ...formData, asset_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Asset Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                required
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select Category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location *
              </label>
              <select
                required
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Acquisition Date *
              </label>
              <input
                type="date"
                required
                value={formData.acquisition_date}
                onChange={(e) => setFormData({ ...formData, acquisition_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Serial Number
              </label>
              <input
                type="text"
                value={formData.serial_number}
                onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div className="md:col-span-2 flex gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {submitting ? 'Creating Asset...' : 'Create Asset'}
              </button>
              <button
                type="button"
                onClick={() => router.push('/fixed-assets')}
                className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
