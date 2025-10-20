# Invoice Approval Quick Reference

## URLs
- **Enhanced Interface**: http://localhost:3001/invoice-approvals ⭐ RECOMMENDED
- **Basic Interface**: http://localhost:3001/approvals
- **AR Invoices**: http://localhost:3001/ar/invoices
- **AP Invoices**: http://localhost:3001/ap/invoices

## Quick Actions

### Submit Invoice for Approval
1. Go to AR or AP invoices page
2. Find draft invoice (not posted)
3. Click blue "Submit for Approval" button (Send icon)
4. Invoice status changes to "Pending Approval"

### Approve Single Invoice (Quick)
1. Go to `/invoice-approvals`
2. Click green "Approve" button
3. (Optional) Add comments
4. Done! ✓

### Approve Single Invoice (Detailed)
1. Go to `/invoice-approvals`
2. Click "View" (eye icon)
3. Review invoice details
4. Click "Approve Invoice"
5. (Optional) Add comments
6. Done! ✓

### Bulk Approve Multiple Invoices
1. Go to `/invoice-approvals`
2. Click checkboxes for invoices to approve
3. Click "Approve Selected" button
4. Confirm action
5. All approved! ✓

### Reject Invoice
1. Go to `/invoice-approvals`
2. Click red "Reject" button
3. Enter rejection reason (required)
4. Invoice rejected with reason saved

### Search for Invoice
1. Go to `/invoice-approvals`
2. Type in search box:
   - Invoice number: "INV-001"
   - Submitter name: "John Doe"
   - Approver name: "Jane Smith"
3. Results filter instantly

### Filter by Invoice Type
1. Go to `/invoice-approvals`
2. Click filter dropdown
3. Select:
   - All Types
   - Receivables (AR)
   - Payables (AP)

## Status Badges

| Badge | Color | Meaning |
|-------|-------|---------|
| ⚠️ Pending | Yellow | Awaiting approval |
| ✓ Approved | Green | Approved by approver |
| ✗ Rejected | Red | Rejected with reason |
| 📄 Draft | Gray | Not yet submitted |

## Tab Navigation

| Tab | Shows |
|-----|-------|
| **Pending** | Awaiting your approval |
| **Approved** | Already approved invoices |
| **Rejected** | Rejected invoices with reasons |
| **All** | Complete approval history |

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Focus search | `/` (when implemented) |
| Next tab | `Tab` |
| Previous tab | `Shift + Tab` |
| Select checkbox | `Space` |

## Common Workflows

### Daily Approval Routine
```
Morning:
1. Check /invoice-approvals (Pending tab)
2. Review count in yellow badge
3. For quick approvals: Click "Approve" buttons
4. For detailed review: Use "View" then approve
5. Bulk approve routine items using checkboxes
```

### End of Week Review
```
Friday:
1. Go to /invoice-approvals
2. Switch to "All" tab
3. Review week's approval activity
4. Check rejected items for follow-up
5. Export data if needed (future feature)
```

### Monthly Audit
```
Month End:
1. Go to /invoice-approvals
2. Filter by invoice type (AR or AP)
3. Switch to "History" tab
4. Review approval patterns
5. Check for any outstanding rejections
6. Generate reports (future feature)
```

## Troubleshooting

### Can't Submit Invoice for Approval
- ✅ Check: Is invoice in Draft status?
- ✅ Check: Is invoice already submitted?
- ✅ Check: Does invoice have line items?
- ✅ Check: Is invoice already posted?

### Can't Approve Invoice
- ✅ Check: Are you the assigned approver?
- ✅ Check: Is invoice in Pending status?
- ✅ Check: Do you have approval permissions?

### Bulk Approve Not Working
- ✅ Check: Did you select invoices with checkboxes?
- ✅ Check: Are selected invoices all in Pending status?
- ✅ Check: Did you confirm the action?

### Invoice Not Appearing in List
- ✅ Check: Is search filter active?
- ✅ Check: Is invoice type filter set?
- ✅ Check: Are you on correct tab?
- ✅ Check: Has invoice been submitted?

### Details Not Loading
- ✅ Check: Internet connection
- ✅ Check: Backend server running
- ✅ Check: Browser console for errors
- ✅ Try: Refresh page

## Best Practices

### For Submitters
1. ✅ Always add clear descriptions to invoices
2. ✅ Double-check amounts before submitting
3. ✅ Submit in batches for efficiency
4. ✅ Add submission comments if needed
5. ✅ Monitor approval status regularly

### For Approvers
1. ✅ Review approvals daily
2. ✅ Check invoice details before approving
3. ✅ Provide clear rejection reasons
4. ✅ Use bulk approve for routine items
5. ✅ Add comments for audit trail

### For Administrators
1. ✅ Monitor pending approval counts
2. ✅ Review rejection patterns
3. ✅ Ensure approvers are responsive
4. ✅ Set approval thresholds
5. ✅ Review approval workflow regularly

## Tips & Tricks

### Speed Up Approvals
- Use bulk approve for multiple similar invoices
- Keep "Pending" tab as default view
- Use search to find specific invoices quickly
- Review details inline instead of navigating away

### Better Organization
- Filter by invoice type (AR/AP) first
- Then search within filtered results
- Use tabs to segment approval stages
- Check summary cards for quick stats

### Improve Accuracy
- Always view details before large approvals
- Double-check amounts and dates
- Read existing comments carefully
- Add your own comments for clarity

### Enhanced Workflow
- Approve routine items in bulk first
- Review special cases individually
- Use rejection comments effectively
- Monitor summary cards for workload

## Summary Statistics

### On Dashboard Cards
- **Pending**: Invoices awaiting approval
- **Approved**: Successfully approved count
- **Rejected**: Rejected invoice count
- **Total**: Complete approval history

### What They Mean
- **High Pending**: Action needed
- **Low Approved**: Review approval speed
- **High Rejected**: Check submission quality
- **Growing Total**: Approval activity increasing

## Support & Help

### Need Help?
1. Check this quick reference
2. Review full documentation: `docs/frontend/INVOICE_APPROVALS_PAGE.md`
3. Check system documentation: `docs/frontend/INVOICE_APPROVAL_SYSTEM_COMPLETE.md`
4. Contact system administrator

### Report Issues
1. Note the error message
2. Check browser console (F12)
3. Document steps to reproduce
4. Report to development team

### Feature Requests
1. Document desired feature clearly
2. Explain use case and benefits
3. Submit to product team
4. Track in backlog

---

**Last Updated**: October 16, 2025  
**Version**: 1.0  
**Primary Interface**: `/invoice-approvals`

**Quick Tip**: Bookmark `/invoice-approvals` for daily use! 📌
