'use client';

import { useState, useEffect } from 'react';

interface DepreciationSchedule {
  id: number;
  asset_number: string;
  asset_name: string;
  period_date: string;
  depreciation_amount: string;
  accumulated_depreciation: string;
  net_book_value: string;
  is_posted: boolean;
  posted_at: string;
}

export default function DepreciationPage() {
  const [schedules, setSchedules] = useState<DepreciationSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [showPosted, setShowPosted] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    // Set current month as default
    const now = new Date();
    const period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
    setSelectedPeriod(period);
  }, []);

  useEffect(() => {
    if (selectedPeriod) {
      fetchSchedules();
    }
  }, [selectedPeriod, showPosted]);

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      let url = `http://localhost:8007/api/fixed-assets/depreciation/?period=${selectedPeriod}`;
      if (!showPosted) {
        url += '&is_posted=false';
      }
      
      const response = await fetch(url);
      const data = await response.json();
      setSchedules(data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    if (!selectedPeriod) {
      alert('Please select a period');
      return;
    }

    setCalculating(true);
    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/depreciation/calculate_monthly/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period_date: selectedPeriod }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Calculated depreciation for ${result.count} assets`);
        fetchSchedules();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to calculate'}`);
      }
    } catch (error) {
      console.error('Error calculating depreciation:', error);
      alert('Failed to calculate depreciation');
    } finally {
      setCalculating(false);
    }
  };

  const handlePost = async () => {
    if (!selectedPeriod) {
      alert('Please select a period');
      return;
    }

    const unposted = schedules.filter(s => !s.is_posted);
    if (unposted.length === 0) {
      alert('No unposted depreciation entries to post');
      return;
    }

    if (!confirm(`Post ${unposted.length} depreciation entries for ${selectedPeriod}?`)) {
      return;
    }

    setPosting(true);
    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/depreciation/post_monthly/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period_date: selectedPeriod }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        fetchSchedules();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to post'}`);
      }
    } catch (error) {
      console.error('Error posting depreciation:', error);
      alert('Failed to post depreciation');
    } finally {
      setPosting(false);
    }
  };

  const totalDepreciation = schedules.reduce((sum, s) => sum + parseFloat(s.depreciation_amount || '0'), 0);
  const unpostedCount = schedules.filter(s => !s.is_posted).length;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Depreciation Management</h1>

      {/* Controls */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Period
            </label>
            <input
              type="month"
              value={selectedPeriod ? selectedPeriod.substring(0, 7) : ''}
              onChange={(e) => setSelectedPeriod(`${e.target.value}-01`)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleCalculate}
              disabled={calculating || !selectedPeriod}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              {calculating ? 'Calculating...' : 'Calculate'}
            </button>
          </div>

          <div className="flex items-end">
            <button
              onClick={handlePost}
              disabled={posting || !selectedPeriod || unpostedCount === 0}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {posting ? 'Posting...' : `Post (${unpostedCount})`}
            </button>
          </div>

          <div className="flex items-end">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showPosted}
                onChange={(e) => setShowPosted(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-900">Show Posted</span>
            </label>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Total Entries</div>
            <div className="text-2xl font-bold text-blue-600">{schedules.length}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Unposted</div>
            <div className="text-2xl font-bold text-green-600">{unpostedCount}</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Total Depreciation</div>
            <div className="text-2xl font-bold text-purple-600">
              {totalDepreciation.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Asset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Depreciation
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accumulated
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Net Book Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {schedules.map((schedule) => (
                  <tr key={schedule.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{schedule.asset_number}</div>
                      <div className="text-sm text-gray-500">{schedule.asset_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(schedule.period_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {parseFloat(schedule.depreciation_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
                      {parseFloat(schedule.accumulated_depreciation).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
                      {parseFloat(schedule.net_book_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        schedule.is_posted
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {schedule.is_posted ? 'Posted' : 'Unposted'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {schedules.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No depreciation schedules found for this period
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
