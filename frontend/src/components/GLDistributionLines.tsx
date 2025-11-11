'use client';

import React from 'react';
import { Plus, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { GLDistributionLine, Account } from '../types';
import SegmentSelector from './SegmentSelector';

interface GLDistributionLinesProps {
  lines: Partial<GLDistributionLine>[];
  accounts: Account[];
  invoiceTotal: number;
  currencySymbol?: string;
  onChange: (lines: Partial<GLDistributionLine>[]) => void;
}

export default function GLDistributionLines({
  lines,
  accounts,
  invoiceTotal,
  currencySymbol = '',
  onChange,
}: GLDistributionLinesProps) {
  
  // State to track which lines have expanded segment selectors
  const [expandedLines, setExpandedLines] = React.useState<Set<number>>(new Set());

  const handleAddLine = () => {
    const newLine: Partial<GLDistributionLine> = {
      account: 0,
      line_type: 'DEBIT',
      amount: '0',
      description: '',
      segments: [],
    };
    onChange([...lines, newLine]);
    // Auto-expand the new line's segments
    setExpandedLines(prev => {
      const newSet = new Set(prev);
      newSet.add(lines.length);
      return newSet;
    });
  };

  const handleRemoveLine = (index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
    // Remove from expanded set
    setExpandedLines(prev => {
      const newSet = new Set(prev);
      newSet.delete(index);
      return newSet;
    });
  };

  const handleLineChange = (index: number, field: keyof GLDistributionLine, value: any) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    onChange(newLines);
  };

  const toggleSegmentExpansion = (index: number) => {
    setExpandedLines(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // Calculate totals
  const totalDebits = lines.reduce((sum, line) => {
    return line.line_type === 'DEBIT' ? sum + parseFloat(line.amount || '0') : sum;
  }, 0);

  const totalCredits = lines.reduce((sum, line) => {
    return line.line_type === 'CREDIT' ? sum + parseFloat(line.amount || '0') : sum;
  }, 0);

  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;
  const matchesInvoiceTotal = Math.abs(totalDebits - invoiceTotal) < 0.01 && Math.abs(totalCredits - invoiceTotal) < 0.01;

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-semibold">GL Distribution Lines</h2>
          <p className="text-sm text-gray-600 mt-1">
            Define how this invoice will post to the general ledger. Click ▼ to select segments for each line.
          </p>
        </div>
        <button
          type="button"
          onClick={handleAddLine}
          className="btn-secondary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Line
        </button>
      </div>

      {lines.length > 0 && (
        <>
          <div className="space-y-3 mb-4">
            <div className="grid grid-cols-12 gap-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
              <div className="col-span-3">Type</div>
              <div className="col-span-3">Amount</div>
              <div className="col-span-5">Description</div>
              <div className="col-span-1"></div>
            </div>
            
            {lines.map((line, index) => {
              const isExpanded = expandedLines.has(index);
              const hasSegments = line.segments && line.segments.length > 0;
              
              return (
                <div key={index} className="border border-gray-200 rounded-lg p-3 bg-white">
                  <div className="grid grid-cols-12 gap-3 items-start">
                    <div className="col-span-3">
                      <select
                        className="input-field"
                        value={line.line_type || 'DEBIT'}
                        onChange={(e) => handleLineChange(index, 'line_type', e.target.value)}
                        required
                      >
                        <option value="DEBIT">Debit</option>
                        <option value="CREDIT">Credit</option>
                      </select>
                    </div>
                    
                    <div className="col-span-3">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        className="input-field"
                        value={line.amount || ''}
                        onChange={(e) => handleLineChange(index, 'amount', e.target.value)}
                        placeholder="0.00"
                        required
                      />
                    </div>
                    
                    <div className="col-span-5">
                      <input
                        type="text"
                        className="input-field"
                        value={line.description || ''}
                        onChange={(e) => handleLineChange(index, 'description', e.target.value)}
                        placeholder="Description (optional)"
                      />
                    </div>
                    
                    <div className="col-span-1 flex justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => toggleSegmentExpansion(index)}
                        className="text-blue-600 hover:text-blue-800 p-2"
                        title={isExpanded ? "Hide segments" : "Show segments"}
                      >
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemoveLine(index)}
                        className="text-red-600 hover:text-red-800 p-2"
                        title="Remove line"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Segment Selector - Collapsible */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200 bg-gray-50 -mx-3 -mb-3 px-3 pb-3 rounded-b-lg">
                      <SegmentSelector
                        value={line.segments || []}
                        onChange={(segments) => handleLineChange(index, 'segments', segments)}
                      />
                    </div>
                  )}
                  
                  {/* Show indicator if segments are set but collapsed */}
                  {!isExpanded && hasSegments && (
                    <div className="mt-2 text-xs text-green-600 flex items-center gap-1">
                      <span>✓</span>
                      <span>{line.segments!.filter(s => s.segment > 0).length} segment(s) configured</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Validation Summary */}
          <div className="border-t pt-4 space-y-2">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-gray-600">Total Debits:</div>
                <div className={`font-semibold ${totalDebits > 0 ? 'text-blue-600' : 'text-gray-900'}`}>
                  {currencySymbol}{totalDebits.toFixed(2)}
                </div>
              </div>
              
              <div>
                <div className="text-gray-600">Total Credits:</div>
                <div className={`font-semibold ${totalCredits > 0 ? 'text-blue-600' : 'text-gray-900'}`}>
                  {currencySymbol}{totalCredits.toFixed(2)}
                </div>
              </div>
              
              <div>
                <div className="text-gray-600">Invoice Total:</div>
                <div className="font-semibold text-gray-900">
                  {currencySymbol}{invoiceTotal.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Validation Messages */}
            <div className="space-y-1 mt-3">
              {!isBalanced && (
                <div className="text-sm text-red-600 flex items-center gap-2">
                  <span className="font-bold">⚠️</span>
                  Debits and Credits must be equal (Difference: {currencySymbol}{Math.abs(totalDebits - totalCredits).toFixed(2)})
                </div>
              )}
              
              {isBalanced && !matchesInvoiceTotal && (
                <div className="text-sm text-red-600 flex items-center gap-2">
                  <span className="font-bold">⚠️</span>
                  Total debits/credits must equal invoice total (Difference: {currencySymbol}{Math.abs(totalDebits - invoiceTotal).toFixed(2)})
                </div>
              )}
              
              {isBalanced && matchesInvoiceTotal && (
                <div className="text-sm text-green-600 flex items-center gap-2">
                  <span className="font-bold">✓</span>
                  GL Distribution is balanced and matches invoice total
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {lines.length === 0 && (
        <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <p className="text-gray-600 mb-2 font-medium">No GL distribution lines added yet</p>
          <p className="text-sm text-gray-500 mb-4">GL distribution lines are required to post this invoice</p>
          <button
            type="button"
            onClick={handleAddLine}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 inline mr-2" />
            Add First Line
          </button>
        </div>
      )}
    </div>
  );
}
