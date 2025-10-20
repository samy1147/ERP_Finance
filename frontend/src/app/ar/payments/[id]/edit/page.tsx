'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { arPaymentsAPI, customersAPI, outstandingInvoicesAPI, currenciesAPI, bankAccountsAPI } from '../../../../../services/api';
import { Customer, Currency, BankAccount, ARPayment } from '../../../../../types';
import toast from 'react-hot-toast';

interface InvoiceAllocation {
  invoice: number;
  invoiceNumber: string;
  invoiceTotal: string;
  outstanding: string;
  amount: string;
  selected: boolean;
}

export default function EditARPaymentPage() {
  const router = useRouter();
  const params = useParams();
  const paymentId = parseInt(params.id as string);
  
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [invoices, setInvoices] = useState<InvoiceAllocation[]>([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [payment, setPayment] = useState<ARPayment | null>(null);
  
  const [formData, setFormData] = useState({
    customer: '',
    date: new Date().toISOString().split('T')[0],
    total_amount: '',
    currency: '1',
    reference: '',
    memo: '',
    bank_account: '',
  });

  useEffect(() => {
    fetchPayment();
    fetchCustomers();
    fetchCurrencies();
    fetchBankAccounts();
  }, [paymentId]);

  useEffect(() => {
    if (formData.customer) {
      fetchOutstandingInvoices(parseInt(formData.customer));
    } else {
      setInvoices([]);
    }
  }, [formData.customer]);

  const fetchPayment = async () => {
    try {
      const response = await arPaymentsAPI.get(paymentId);
      const paymentData = response.data;
      setPayment(paymentData);
      
      // Check if payment is already posted
      if (paymentData.posted_at) {
        toast.error('Cannot edit posted payment');
        router.push('/ar/payments');
        return;
      }
      
      // Set form data
      setFormData({
        customer: paymentData.customer.toString(),
        date: paymentData.date,
        total_amount: paymentData.total_amount,
        currency: paymentData.currency.toString(),
        reference: paymentData.reference,
        memo: paymentData.memo || '',
        bank_account: paymentData.bank_account?.toString() || '',
      });
    } catch (error) {
      console.error('Failed to load payment:', error);
      toast.error('Failed to load payment');
      router.push('/ar/payments');
    } finally {
      setLoadingData(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.list();
      setCustomers(response.data);
    } catch (error) {
      console.error('Failed to load customers:', error);
      toast.error('Failed to load customers');
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await currenciesAPI.list();
      setCurrencies(response.data);
    } catch (error) {
      console.error('Failed to load currencies:', error);
      toast.error('Failed to load currencies');
    }
  };

  const fetchBankAccounts = async () => {
    try {
      const response = await bankAccountsAPI.list();
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Failed to load bank accounts:', error);
      toast.error('Failed to load bank accounts');
    }
  };

  const fetchOutstandingInvoices = async (customerId: number) => {
    setLoadingInvoices(true);
    try {
      const response = await outstandingInvoicesAPI.getByCustomer(customerId);
      const invoiceData = response.data.map((inv: any) => ({
        invoice: inv.id,
        invoiceNumber: inv.invoice_number,
        invoiceTotal: inv.total,
        outstanding: inv.balance,
        amount: '0.00',
        selected: false,
      }));
      
      // If payment has existing allocations, mark them as selected
      if (payment?.allocations) {
        payment.allocations.forEach((alloc: any) => {
          const idx = invoiceData.findIndex((inv: InvoiceAllocation) => inv.invoice === alloc.invoice);
          if (idx !== -1) {
            invoiceData[idx].selected = true;
            invoiceData[idx].amount = alloc.amount;
          }
        });
      }
      
      setInvoices(invoiceData);
    } catch (error) {
      console.error('Failed to load outstanding invoices:', error);
      toast.error('Failed to load outstanding invoices');
      setInvoices([]);
    } finally {
      setLoadingInvoices(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleInvoiceSelect = (index: number) => {
    setInvoices(prev => {
      const updated = [...prev];
      updated[index].selected = !updated[index].selected;
      
      // Auto-fill with outstanding amount when selected
      if (updated[index].selected && (!updated[index].amount || updated[index].amount === '0.00')) {
        updated[index].amount = updated[index].outstanding;
      }
      
      return updated;
    });
  };

  const handleInvoiceAmountChange = (index: number, value: string) => {
    setInvoices(prev => {
      const updated = [...prev];
      updated[index].amount = value;
      return updated;
    });
  };

  const calculateTotalAllocated = () => {
    return invoices
      .filter(inv => inv.selected)
      .reduce((sum, inv) => sum + parseFloat(inv.amount || '0'), 0);
  };

  const calculateUnallocated = () => {
    const total = parseFloat(formData.total_amount) || 0;
    const allocated = calculateTotalAllocated();
    return total - allocated;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.customer) {
      toast.error('Please select a customer');
      return;
    }
    
    if (!formData.total_amount || parseFloat(formData.total_amount) <= 0) {
      toast.error('Please enter a valid payment amount');
      return;
    }

    const selectedInvoices = invoices.filter(inv => inv.selected);
    if (selectedInvoices.length === 0) {
      toast.error('Please select at least one invoice to allocate');
      return;
    }

    // Validate allocations
    for (const inv of selectedInvoices) {
      const amount = parseFloat(inv.amount);
      const outstanding = parseFloat(inv.outstanding);
      
      if (amount <= 0) {
        toast.error(`Please enter a valid amount for invoice ${inv.invoiceNumber}`);
        return;
      }
      
      if (amount > outstanding) {
        toast.error(`Allocation for invoice ${inv.invoiceNumber} exceeds outstanding balance`);
        return;
      }
    }

    const totalAllocated = calculateTotalAllocated();
    const paymentTotal = parseFloat(formData.total_amount);
    
    if (totalAllocated > paymentTotal) {
      toast.error('Total allocated amount exceeds payment amount');
      return;
    }

    setLoading(true);
    try {
      const allocations = selectedInvoices.map(inv => ({
        invoice: inv.invoice,
        amount: inv.amount,
      }));

      await arPaymentsAPI.update(paymentId, {
        ...formData,
        customer: parseInt(formData.customer),
        currency: parseInt(formData.currency),
        bank_account: formData.bank_account ? parseInt(formData.bank_account) : undefined,
        allocations,
      });

      toast.success('Payment updated successfully');
      router.push('/ar/payments');
    } catch (error: any) {
      console.error('Failed to update payment:', error);
      toast.error(error.response?.data?.error || 'Failed to update payment');
    } finally {
      setLoading(false);
    }
  };

  const handleClearAllocations = () => {
    setInvoices(prev => prev.map(inv => ({ ...inv, selected: false, amount: '0.00' })));
  };

  if (loadingData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading payment...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Edit AR Payment</h1>
        <p className="mt-2 text-gray-600">Modify payment and allocations to customer invoices</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Payment Details */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label">Customer *</label>
              <select
                name="customer"
                value={formData.customer}
                onChange={handleInputChange}
                className="form-input"
                required
                disabled // Can't change customer on edit
              >
                <option value="">Select customer</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="form-label">Payment Date *</label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                className="form-input"
                required
              />
            </div>

            <div>
              <label className="form-label">Total Amount *</label>
              <input
                type="number"
                step="0.01"
                name="total_amount"
                value={formData.total_amount}
                onChange={handleInputChange}
                className="form-input"
                placeholder="0.00"
                required
              />
            </div>

            <div>
              <label className="form-label">Currency *</label>
              <select
                name="currency"
                value={formData.currency}
                onChange={handleInputChange}
                className="form-input"
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
              <label className="form-label">Reference</label>
              <input
                type="text"
                name="reference"
                value={formData.reference}
                onChange={handleInputChange}
                className="form-input"
                placeholder="Payment reference"
                disabled // Can't change reference on edit
              />
            </div>

            <div>
              <label className="form-label">Bank Account</label>
              <select
                name="bank_account"
                value={formData.bank_account}
                onChange={handleInputChange}
                className="form-input"
              >
                <option value="">Select bank account</option>
                {bankAccounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.name} - {account.account_code}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="form-label">Memo</label>
              <textarea
                name="memo"
                value={formData.memo}
                onChange={handleInputChange}
                className="form-input"
                rows={2}
                placeholder="Optional memo"
              />
            </div>
          </div>
        </div>

        {/* Allocation Summary */}
        {formData.customer && formData.total_amount && (
          <div className="card bg-blue-50 border-blue-200">
            <h2 className="text-lg font-semibold mb-3 text-blue-900">Allocation Summary</h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-blue-700">Total Payment Amount</div>
                <div className="text-2xl font-bold text-green-600">
                  ${parseFloat(formData.total_amount).toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-700">Total Allocated</div>
                <div className="text-2xl font-bold text-blue-600">
                  ${calculateTotalAllocated().toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-700">Unallocated Amount</div>
                <div className={`text-2xl font-bold ${calculateUnallocated() > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ${calculateUnallocated().toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Invoice Allocations */}
        {formData.customer && (
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Invoice Allocations</h2>
              {invoices.some(inv => inv.selected) && (
                <button
                  type="button"
                  onClick={handleClearAllocations}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Clear All Allocations
                </button>
              )}
            </div>

            {loadingInvoices ? (
              <div className="text-center py-8 text-gray-600">Loading invoices...</div>
            ) : invoices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No outstanding invoices for this customer
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Select</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Outstanding</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount to Allocate</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {invoices.map((invoice, index) => (
                      <tr key={invoice.invoice} className={invoice.selected ? 'bg-blue-50' : ''}>
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={invoice.selected}
                            onChange={() => handleInvoiceSelect(index)}
                            className="h-4 w-4 text-blue-600 rounded"
                          />
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {invoice.invoiceNumber}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          ${invoice.invoiceTotal}
                        </td>
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                          ${invoice.outstanding}
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            step="0.01"
                            value={invoice.amount}
                            onChange={(e) => handleInvoiceAmountChange(index, e.target.value)}
                            disabled={!invoice.selected}
                            className="form-input w-32"
                            placeholder="0.00"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => router.push('/ar/payments')}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || loadingInvoices}
          >
            {loading ? 'Updating...' : 'Update Payment'}
          </button>
        </div>
      </form>
    </div>
  );
}
