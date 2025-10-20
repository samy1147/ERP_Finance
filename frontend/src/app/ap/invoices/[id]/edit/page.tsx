'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apInvoicesAPI, suppliersAPI, currenciesAPI, taxRatesAPI } from '../../../../../services/api';
import { APInvoiceItem, Supplier, Currency, TaxRate } from '../../../../../types';
import { Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function EditAPInvoicePage() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [formData, setFormData] = useState({
    supplier: '',
    number: '',
    date: '',
    due_date: '',
    currency: '1',
    country: 'AE',
  });
  const [items, setItems] = useState<Partial<APInvoiceItem>[]>([
    { description: '', quantity: '1', unit_price: '0', tax_rate: undefined },
  ]);

  useEffect(() => {
    fetchInitialData();
  }, [invoiceId]);

  useEffect(() => {
    if (formData.country) {
      fetchTaxRates(formData.country);
    }
  }, [formData.country]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      
      // Fetch suppliers, currencies, and invoice data in parallel
      const [suppliersRes, currenciesRes, invoiceRes] = await Promise.all([
        suppliersAPI.list(),
        currenciesAPI.list(),
        apInvoicesAPI.get(parseInt(invoiceId))
      ]);

      setSuppliers(suppliersRes.data);
      setCurrencies(currenciesRes.data);

      const invoice = invoiceRes.data;
      
      // Check if invoice can be edited
      if (invoice.is_posted) {
        toast.error('Cannot edit posted invoices');
        router.push('/ap/invoices');
        return;
      }

      if (invoice.is_cancelled) {
        toast.error('Cannot edit cancelled invoices');
        router.push('/ap/invoices');
        return;
      }

      // Populate form with invoice data
      setFormData({
        supplier: invoice.supplier.toString(),
        number: invoice.invoice_number,
        date: invoice.date,
        due_date: invoice.due_date,
        currency: invoice.currency.toString(),
        country: invoice.country || 'AE',
      });

      // Populate items
      if (invoice.items && invoice.items.length > 0) {
        setItems(invoice.items.map((item: any) => ({
          id: item.id,
          description: item.description,
          quantity: item.quantity.toString(),
          unit_price: item.unit_price.toString(),
          tax_rate: item.tax_rate || undefined,
        })));
      }

      // Fetch tax rates for the invoice country
      await fetchTaxRates(invoice.country || 'AE');

    } catch (error: any) {
      console.error('Failed to load invoice:', error);
      toast.error(error.response?.data?.error || 'Failed to load invoice');
      router.push('/ap/invoices');
    } finally {
      setLoading(false);
    }
  };

  const fetchTaxRates = async (country?: string) => {
    try {
      const response = await taxRatesAPI.list(country);
      console.log(`📊 Tax rates loaded for ${country || 'all countries'}:`, response.data);
      setTaxRates(response.data);
    } catch (error) {
      console.error('❌ Failed to load tax rates:', error);
      toast.error('Failed to load tax rates');
    }
  };

  const handleSupplierChange = async (supplierId: string) => {
    setFormData({ ...formData, supplier: supplierId });
    
    if (supplierId) {
      const supplier = suppliers.find(s => s.id === parseInt(supplierId));
      if (supplier && supplier.country) {
        setFormData(prev => ({ ...prev, supplier: supplierId, country: supplier.country || 'AE' }));
      }
    }
  };

  const handleAddItem = () => {
    setItems([...items, { description: '', quantity: '1', unit_price: '0', tax_rate: undefined }]);
  };

  const handleRemoveItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  const handleItemChange = (index: number, field: keyof APInvoiceItem, value: string) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    setItems(newItems);
  };

  const calculateLineTotal = (item: Partial<APInvoiceItem>) => {
    const qty = parseFloat(item.quantity || '0');
    const price = parseFloat(item.unit_price || '0');
    const subtotal = qty * price;
    
    let taxRate = 0;
    if (item.tax_rate) {
      const selectedTaxRate = taxRates.find(tr => tr.id === parseInt(item.tax_rate as any));
      if (selectedTaxRate) {
        taxRate = parseFloat(selectedTaxRate.rate.toString());
      }
    }
    
    const tax = subtotal * (taxRate / 100);
    return {
      subtotal,
      tax,
      total: subtotal + tax
    };
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let tax = 0;
    
    items.forEach(item => {
      const lineCalc = calculateLineTotal(item);
      subtotal += lineCalc.subtotal;
      tax += lineCalc.tax;
    });
    
    return {
      subtotal: subtotal,
      tax: tax,
      total: subtotal + tax
    };
  };

  const calculateTotal = () => {
    return calculateTotals().total;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const invoiceData = {
        supplier: parseInt(formData.supplier),
        number: formData.number,
        date: formData.date,
        due_date: formData.due_date,
        currency: parseInt(formData.currency),
        country: formData.country,
        items: items.map(item => ({
          description: item.description || '',
          quantity: item.quantity || '0',
          unit_price: item.unit_price || '0',
          tax_rate: item.tax_rate ? parseInt(item.tax_rate as any) : null
        }))
      };

      await apInvoicesAPI.update(parseInt(invoiceId), invoiceData as any);
      toast.success('Invoice updated successfully');
      router.push('/ap/invoices');
    } catch (error: any) {
      const errorMessage = error.response?.data?.error 
        || error.response?.data?.detail 
        || JSON.stringify(error.response?.data) 
        || 'Failed to update invoice';
      toast.error(errorMessage);
      console.error('Update error:', error.response?.data || error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading invoice...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Edit AP Invoice</h1>
        <p className="mt-2 text-gray-600">Update invoice details (Draft only)</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Invoice Header */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Invoice Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Supplier *
              </label>
              <select
                className="input-field"
                value={formData.supplier}
                onChange={(e) => handleSupplierChange(e.target.value)}
                required
              >
                <option value="">Select supplier</option>
                {suppliers.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Invoice Number *
              </label>
              <input
                type="text"
                className="input-field"
                value={formData.number}
                onChange={(e) => setFormData({ ...formData, number: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date *
              </label>
              <input
                type="date"
                className="input-field"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Due Date *
              </label>
              <input
                type="date"
                className="input-field"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency *
              </label>
              <select
                className="input-field"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                required
              >
                {currencies.map((currency) => (
                  <option key={currency.id} value={currency.id}>
                    {currency.code} - {currency.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tax Country *
              </label>
              <select
                className="input-field"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                required
              >
                <option value="AE">UAE</option>
                <option value="SA">Saudi Arabia (KSA)</option>
                <option value="EG">Egypt</option>
                <option value="IN">India</option>
              </select>
            </div>
          </div>
        </div>

        {/* Invoice Items */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Line Items</h2>
            <button
              type="button"
              onClick={handleAddItem}
              className="btn-secondary flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Item
            </button>
          </div>

          <div className="space-y-3">
            <div className="grid grid-cols-12 gap-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              <div className="col-span-4">Description</div>
              <div className="col-span-2">Quantity</div>
              <div className="col-span-2">Unit Price</div>
              <div className="col-span-2">Tax Rate</div>
              <div className="col-span-2">Amount</div>
            </div>
            {items.map((item, index) => (
              <div key={index} className="grid grid-cols-12 gap-3 items-start">
                <div className="col-span-4">
                  <input
                    type="text"
                    placeholder="Description"
                    className="input-field"
                    value={item.description}
                    onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                    required
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Qty"
                    className="input-field"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                    required
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Unit Price"
                    className="input-field"
                    value={item.unit_price}
                    onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                    required
                  />
                </div>
                <div className="col-span-2">
                  <select
                    className="input-field text-sm"
                    value={item.tax_rate || ''}
                    onChange={(e) => handleItemChange(index, 'tax_rate', e.target.value)}
                  >
                    <option value="">No Tax</option>
                    {taxRates.filter(tr => tr.is_active).map(taxRate => (
                      <option key={taxRate.id} value={taxRate.id}>
                        {taxRate.name} ({taxRate.rate}%)
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">
                      {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateLineTotal(item).total.toFixed(2)}
                    </span>
                    {calculateLineTotal(item).tax > 0 && (
                      <span className="text-xs text-gray-500">
                        (Tax: {calculateLineTotal(item).tax.toFixed(2)})
                      </span>
                    )}
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(index)}
                      className="text-red-600 hover:text-red-800"
                      aria-label="Remove item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-end">
              <div className="text-right space-y-2">
                <div className="flex justify-between gap-8">
                  <span className="text-sm text-gray-600">Subtotal:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotals().subtotal.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between gap-8">
                  <span className="text-sm text-gray-600">Tax:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotals().tax.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between gap-8 pt-2 border-t border-gray-200">
                  <span className="text-base font-semibold text-gray-700">Total:</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotal().toFixed(2)}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Tax calculated in invoice currency
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
            disabled={saving}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
