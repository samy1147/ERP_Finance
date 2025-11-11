'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface GRN {
  id: number;
  grn_number: string;
  supplier_name?: string;
  vendor_name?: string;
  receipt_date: string;
  status: string;
  po_number?: string;
}

interface GRNLine {
  id: number;
  line_number: number;
  item_description: string;
  received_quantity: number;
  ordered_quantity?: number;
  unit_price?: number;
  unit_of_measure?: string;
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

export default function CreateAssetFromGRN() {
  const router = useRouter();
  const [grns, setGrns] = useState<GRN[]>([]);
  const [selectedGRN, setSelectedGRN] = useState<GRN | null>(null);
  const [grnLines, setGrnLines] = useState<GRNLine[]>([]);
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
      const [grnsRes, categoriesRes, locationsRes] = await Promise.all([
        fetch('http://localhost:8007/api/procurement/receiving/receipts/'),
        fetch('http://localhost:8007/api/fixed-assets/categories/'),
        fetch('http://localhost:8007/api/fixed-assets/locations/'),
      ]);

      if (grnsRes.ok) {
        const grnsData = await grnsRes.json();
        setGrns(grnsData);
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

  const handleGRNSelect = async (grn: GRN) => {
    setSelectedGRN(grn);
    setSelectedLine(null);
    setConversionStatus(null);
    setError('');

    try {
      const response = await fetch(`http://localhost:8007/api/procurement/receiving/receipts/${grn.id}/`);
      if (response.ok) {
        const data = await response.json();
        setGrnLines(data.lines || []);
      }
    } catch (err) {
      console.error('Error fetching GRN lines:', err);
      setError('Failed to load GRN lines');
    }
  };

  const checkConversion = async (lineId: number) => {
    setCheckingConversion(true);
    setConversionStatus(null);

    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/assets/check_source_conversion/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: 'GRN',
          grn_line_id: lineId,
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

  const handleLineSelect = (line: GRNLine) => {
    setSelectedLine(line.id);
    setError('');
    checkConversion(line.id);

    // Auto-populate name from line description
    setFormData(prev => ({
      ...prev,
      name: line.item_description,
      description: line.item_description,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedGRN || selectedLine === null) {
      setError('Please select a GRN and line item');
      return;
    }

    if (conversionStatus?.already_converted) {
      setError('This GRN line has already been converted to an asset');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/assets/create_from_grn/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grn_line_id: selectedLine,
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
      setError('Failed to create asset from GRN');
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
        <h1 className="text-2xl font-bold">Create Asset from GRN</h1>
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
        {/* GRN Selection */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">1. Select GRN</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {grns.map((grn) => (
              <div
                key={grn.id}
                onClick={() => handleGRNSelect(grn)}
                className={`p-4 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedGRN?.id === grn.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{grn.grn_number}</div>
                    <div className="text-sm text-gray-600">{grn.supplier_name || grn.vendor_name || 'N/A'}</div>
                    <div className="text-sm text-gray-500">{grn.receipt_date}</div>
                    {grn.po_number && (
                      <div className="text-sm text-gray-500">PO: {grn.po_number}</div>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={`text-xs px-2 py-1 rounded ${
                      grn.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {grn.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* GRN Lines */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">2. Select Line Item</h2>
          {selectedGRN ? (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {grnLines.map((line) => (
                <div
                  key={line.id}
                  onClick={() => handleLineSelect(line)}
                  className={`p-4 border rounded cursor-pointer hover:bg-gray-50 ${
                    selectedLine === line.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold">Line {line.line_number}</div>
                      <div className="text-sm text-gray-700">{line.item_description}</div>
                      <div className="text-sm text-gray-500">
                        Qty Received: {line.received_quantity || 0}
                        {line.unit_of_measure && ` ${line.unit_of_measure}`}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {line.unit_price ? `${Number(line.unit_price).toFixed(2)}` : 'N/A'}
                      </div>
                      {line.ordered_quantity && (
                        <div className="text-xs text-gray-500">
                          Ordered: {line.ordered_quantity}
                        </div>
                      )}
                    </div>
                  </div>
                  {selectedLine === line.id && checkingConversion && (
                    <div className="mt-2 text-sm text-gray-500">Checking conversion status...</div>
                  )}
                  {selectedLine === line.id && conversionStatus?.already_converted && (
                    <div className="mt-2 text-sm text-red-600">
                      ⚠️ Already converted to asset: {conversionStatus.asset_number}
                    </div>
                  )}
                  {selectedLine === line.id && conversionStatus?.can_convert && (
                    <div className="mt-2 text-sm text-green-600">
                      ✓ Available for conversion
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Select a GRN to view line items
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
