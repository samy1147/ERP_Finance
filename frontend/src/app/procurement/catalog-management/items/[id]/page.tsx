'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { catalogItemsAPI } from '../../../../../services/procurement-api';
import { CatalogItem } from '../../../../../types/procurement';
import { ArrowLeft, Package, DollarSign, Truck, ShoppingCart, Edit, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function CatalogItemDetailPage() {
  const router = useRouter();
  const params = useParams();
  const itemId = params.id as string;
  
  const [item, setItem] = useState<CatalogItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (itemId) {
      fetchItem();
    }
  }, [itemId]);

  const fetchItem = async () => {
    try {
      setLoading(true);
      const response = await catalogItemsAPI.get(parseInt(itemId));
      setItem(response.data);
    } catch (error: any) {
      console.error('Failed to load item', error);
      toast.error('Failed to load catalog item');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Package size={48} className="mx-auto text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Item Not Found</h2>
            <p className="text-gray-600 mb-6">The catalog item you're looking for doesn't exist.</p>
            <Link
              href="/procurement/catalog-management"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <ArrowLeft size={20} />
              Back to Catalog
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/procurement/catalog-management"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
          >
            <ArrowLeft size={20} />
            <span>Back to Catalog</span>
          </Link>
          
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900">{item.name}</h1>
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                  item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {item.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-gray-600">Item Code: <span className="font-semibold">{item.item_code}</span></p>
              {item.sku && <p className="text-gray-500 text-sm">SKU: {item.sku}</p>}
            </div>
            
            <div className="flex gap-2">
              <Link
                href="/procurement/requisitions/new"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <ShoppingCart size={20} />
                Create PR with this Item
              </Link>
              <Link
                href={`/procurement/catalog-management/items/${itemId}/edit`}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Edit size={20} />
                Edit
              </Link>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Information */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image */}
            {item.image_url && (
              <div className="bg-white rounded-lg shadow p-6">
                <img 
                  src={item.image_url} 
                  alt={item.name}
                  className="w-full h-96 object-contain rounded-lg"
                />
              </div>
            )}

            {/* Description */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Info size={20} />
                Description
              </h2>
              <div className="space-y-3">
                {item.short_description && (
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-1">Summary</h3>
                    <p className="text-gray-700">{item.short_description}</p>
                  </div>
                )}
                {item.long_description && (
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-1">Details</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">{item.long_description}</p>
                  </div>
                )}
                {!item.short_description && !item.long_description && (
                  <p className="text-gray-500">No description available</p>
                )}
              </div>
            </div>

            {/* Specifications */}
            {item.specifications && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Specifications</h2>
                <div className="text-gray-700 whitespace-pre-wrap">
                  {typeof item.specifications === 'string' 
                    ? item.specifications 
                    : JSON.stringify(item.specifications, null, 2)}
                </div>
              </div>
            )}

            {/* Price Tiers */}
            {item.price_tiers && item.price_tiers.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Volume Pricing</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Min Quantity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Unit Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Discount
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {item.price_tiers.map((tier, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {parseFloat(tier.min_quantity).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-blue-600">
                            ${parseFloat(tier.unit_price).toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {tier.discount_percentage ? `${tier.discount_percentage}%` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Pricing Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <DollarSign size={20} />
                Pricing
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Base Price</div>
                  <div className="text-3xl font-bold text-blue-600">
                    ${parseFloat(item.list_price).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500">{item.currency_code || 'USD'}</div>
                </div>
                <div className="border-t pt-3">
                  <div className="text-sm text-gray-600">Unit of Measure</div>
                  <div className="text-lg font-semibold text-gray-900">{item.uom_code}</div>
                </div>
                {item.minimum_order_quantity && (
                  <div className="border-t pt-3">
                    <div className="text-sm text-gray-600">Minimum Order Quantity</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {parseFloat(item.minimum_order_quantity).toLocaleString()} {item.uom_code}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Supplier Card */}
            {item.supplier_name && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Truck size={20} />
                  Supplier Information
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-sm text-gray-600">Preferred Supplier</div>
                    <div className="text-lg font-semibold text-gray-900">{item.supplier_name}</div>
                  </div>
                  {item.lead_time_days !== undefined && (
                    <div className="border-t pt-3">
                      <div className="text-sm text-gray-600">Lead Time</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {item.lead_time_days} days
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Category Card */}
            {item.category_name && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Package size={20} />
                  Classification
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-sm text-gray-600">Category</div>
                    <div className="text-lg font-semibold text-gray-900">{item.category_name}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Metadata</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Created:</span>
                  <span className="font-semibold text-gray-900">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Updated:</span>
                  <span className="font-semibold text-gray-900">
                    {new Date(item.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
