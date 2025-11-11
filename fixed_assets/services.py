"""
Asset Management Services
Handles asset capitalization, depreciation calculations, disposal, and journal entry automation
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from .models import Asset, DepreciationSchedule
from finance.models import JournalEntry, JournalLine
try:
    from finance.models import JournalLineSegment
except ImportError:
    JournalLineSegment = None
from segment.models import XX_Segment


class AssetGLService:
    """Service for handling asset-related journal entries"""
    
    @transaction.atomic
    def create_capitalization_journal(self, asset, user=None):
        """
        Create journal entry for asset capitalization
        
        Dr. Asset Account (from category or asset)
        Cr. AP/Cash (from invoice/payment)
        
        Returns: JournalEntry instance
        """
        if not asset.asset_account:
            raise ValueError("Asset must have an asset GL account assigned")
        
        # Create journal entry
        journal = JournalEntry.objects.create(
            entry_date=asset.capitalization_date or asset.acquisition_date,
            period=asset.capitalization_date or asset.acquisition_date,
            description=f"Capitalization of {asset.name} - {asset.asset_number}",
            reference=f"ASSET-CAP-{asset.asset_number}",
            status='POSTED',
            source='ASSET_CAPITALIZATION',
            created_by=user
        )
        
        # Debit: Asset Account
        JournalLine.objects.create(
            journal=journal,
            account=asset.asset_account,
            debit=asset.acquisition_cost,
            credit=Decimal('0.00'),
            description=f"Asset: {asset.name}",
            line_number=1
        )
        
        # Credit: AP or clearing account (would need to be configured)
        # For now, using a placeholder - in real scenario, this would link to AP invoice
        clearing_account = asset.asset_account  # Placeholder
        JournalLine.objects.create(
            journal=journal,
            account=clearing_account,
            debit=Decimal('0.00'),
            credit=asset.acquisition_cost,
            description=f"Asset purchase: {asset.name}",
            line_number=2
        )
        
        # Update asset
        asset.capitalization_journal = journal
        asset.save(update_fields=['capitalization_journal'])
        
        return journal
    
    @transaction.atomic
    def create_depreciation_journal(self, depreciation_schedule, user=None):
        """
        Create journal entry for depreciation
        
        Dr. Depreciation Expense Account
        Cr. Accumulated Depreciation Account
        
        Returns: JournalEntry instance
        """
        asset = depreciation_schedule.asset
        
        if not asset.depreciation_expense_account:
            raise ValueError("Asset must have a depreciation expense account assigned")
        
        if not asset.accumulated_depreciation_account:
            raise ValueError("Asset must have an accumulated depreciation account assigned")
        
        # Create journal entry
        journal = JournalEntry.objects.create(
            entry_date=depreciation_schedule.period_date,
            period=depreciation_schedule.period_date,
            description=f"Depreciation - {asset.name} - {depreciation_schedule.period_date.strftime('%B %Y')}",
            reference=f"DEPR-{asset.asset_number}-{depreciation_schedule.period_date.strftime('%Y%m')}",
            status='POSTED',
            source='ASSET_DEPRECIATION',
            created_by=user
        )
        
        # Debit: Depreciation Expense
        JournalLine.objects.create(
            journal=journal,
            account=asset.depreciation_expense_account,
            debit=depreciation_schedule.depreciation_amount,
            credit=Decimal('0.00'),
            description=f"Depreciation: {asset.name}",
            line_number=1
        )
        
        # Credit: Accumulated Depreciation
        JournalLine.objects.create(
            journal=journal,
            account=asset.accumulated_depreciation_account,
            debit=Decimal('0.00'),
            credit=depreciation_schedule.depreciation_amount,
            description=f"Accumulated depreciation: {asset.name}",
            line_number=2
        )
        
        # Update depreciation schedule
        depreciation_schedule.journal_entry = journal
        depreciation_schedule.posting_status = 'POSTED'
        depreciation_schedule.save(update_fields=['journal_entry', 'posting_status'])
        
        # Update asset totals
        asset.total_depreciation = (asset.total_depreciation or Decimal('0.00')) + depreciation_schedule.depreciation_amount
        asset.net_book_value = asset.acquisition_cost - asset.total_depreciation
        asset.last_depreciation_date = depreciation_schedule.period_date
        asset.save(update_fields=['total_depreciation', 'net_book_value', 'last_depreciation_date'])
        
        return journal
    
    @transaction.atomic
    def create_disposal_journal(self, asset, disposal_date, disposal_proceeds, user=None):
        """
        Create journal entry for asset disposal
        
        Dr. Cash/Receivable (disposal proceeds)
        Dr. Accumulated Depreciation (total depreciation to date)
        Dr./Cr. Gain/Loss on Disposal (balancing entry)
        Cr. Asset Account (original cost)
        
        Returns: JournalEntry instance
        """
        if not asset.asset_account:
            raise ValueError("Asset must have an asset GL account assigned")
        
        if not asset.accumulated_depreciation_account:
            raise ValueError("Asset must have an accumulated depreciation account assigned")
        
        # Calculate gain/loss
        net_book_value = asset.net_book_value or (asset.acquisition_cost - (asset.total_depreciation or Decimal('0.00')))
        gain_loss = disposal_proceeds - net_book_value
        
        # Create journal entry
        journal = JournalEntry.objects.create(
            entry_date=disposal_date,
            period=disposal_date,
            description=f"Disposal of {asset.name} - {asset.asset_number}",
            reference=f"ASSET-DISP-{asset.asset_number}",
            status='POSTED',
            source='ASSET_DISPOSAL',
            created_by=user
        )
        
        line_num = 1
        
        # Debit: Cash (or receivable)
        if disposal_proceeds > 0:
            cash_account = asset.asset_account  # Placeholder - should be configured
            JournalLine.objects.create(
                journal=journal,
                account=cash_account,
                debit=disposal_proceeds,
                credit=Decimal('0.00'),
                description=f"Proceeds from disposal: {asset.name}",
                line_number=line_num
            )
            line_num += 1
        
        # Debit: Accumulated Depreciation
        JournalLine.objects.create(
            journal=journal,
            account=asset.accumulated_depreciation_account,
            debit=asset.total_depreciation or Decimal('0.00'),
            credit=Decimal('0.00'),
            description=f"Clear accumulated depreciation: {asset.name}",
            line_number=line_num
        )
        line_num += 1
        
        # Gain or Loss on Disposal
        if gain_loss != 0:
            gain_loss_account = asset.depreciation_expense_account  # Placeholder
            if gain_loss > 0:
                # Gain - Credit
                JournalLine.objects.create(
                    journal=journal,
                    account=gain_loss_account,
                    debit=Decimal('0.00'),
                    credit=abs(gain_loss),
                    description=f"Gain on disposal: {asset.name}",
                    line_number=line_num
                )
            else:
                # Loss - Debit
                JournalLine.objects.create(
                    journal=journal,
                    account=gain_loss_account,
                    debit=abs(gain_loss),
                    credit=Decimal('0.00'),
                    description=f"Loss on disposal: {asset.name}",
                    line_number=line_num
                )
            line_num += 1
        
        # Credit: Asset Account
        JournalLine.objects.create(
            journal=journal,
            account=asset.asset_account,
            debit=Decimal('0.00'),
            credit=asset.acquisition_cost,
            description=f"Remove asset: {asset.name}",
            line_number=line_num
        )
        
        # Update asset
        asset.disposal_journal = journal
        asset.save(update_fields=['disposal_journal'])
        
        return journal


class AssetDepreciationService:
    """Service for calculating and posting asset depreciation"""
    
    def calculate_straight_line_depreciation(self, asset, period_date):
        """
        Calculate straight-line depreciation
        Formula: (Cost - Salvage Value) / Useful Life
        """
        depreciable_amount = asset.calculate_depreciable_amount()
        
        if not asset.useful_life_years or asset.useful_life_years == 0:
            return Decimal('0.00')
        
        # Annual depreciation
        annual_depreciation = depreciable_amount / asset.useful_life_years
        
        # Monthly depreciation
        monthly_depreciation = annual_depreciation / 12
        
        return monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_declining_balance_depreciation(self, asset, period_date, accumulated_to_date):
        """
        Calculate declining balance depreciation
        Formula: (Cost - Accumulated Depreciation) × (2 / Useful Life)
        """
        if not asset.useful_life_years or asset.useful_life_years == 0:
            return Decimal('0.00')
        
        # Book value at start of period
        book_value = asset.acquisition_cost - accumulated_to_date
        
        # Don't depreciate below salvage value
        if book_value <= asset.salvage_value:
            return Decimal('0.00')
        
        # Double declining balance rate
        rate = Decimal('2.00') / asset.useful_life_years
        
        # Annual depreciation
        annual_depreciation = book_value * rate
        
        # Monthly depreciation
        monthly_depreciation = annual_depreciation / 12
        
        # Ensure we don't depreciate below salvage value
        depreciable_amount = book_value - asset.salvage_value
        if monthly_depreciation > depreciable_amount:
            monthly_depreciation = depreciable_amount
        
        return monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_sum_of_years_depreciation(self, asset, period_date, months_elapsed):
        """
        Calculate sum-of-years-digits depreciation
        Formula: (Cost - Salvage) × (Remaining Life / Sum of Years)
        """
        if not asset.useful_life_years or asset.useful_life_years == 0:
            return Decimal('0.00')
        
        depreciable_amount = asset.calculate_depreciable_amount()
        
        # Sum of years digits
        n = asset.useful_life_years
        sum_of_years = (n * (n + 1)) / 2
        
        # Years elapsed
        years_elapsed = Decimal(months_elapsed) / 12
        
        # Remaining years
        remaining_years = Decimal(n) - years_elapsed
        if remaining_years <= 0:
            return Decimal('0.00')
        
        # Annual depreciation for current year
        annual_depreciation = depreciable_amount * (remaining_years / Decimal(sum_of_years))
        
        # Monthly depreciation
        monthly_depreciation = annual_depreciation / 12
        
        return monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_units_of_production_depreciation(self, asset, period_date, units_produced):
        """
        Calculate units of production depreciation
        Formula: (Cost - Salvage) × (Units Produced / Total Expected Units)
        
        Note: This method requires tracking units produced, which would need
        additional fields in the Asset model
        """
        # This is a placeholder - would need additional implementation
        # for tracking production units
        return Decimal('0.00')
    
    def calculate_depreciation_for_period(self, asset, period_date):
        """
        Calculate depreciation for a specific period
        Returns: (depreciation_amount, accumulated_depreciation, net_book_value)
        """
        # Get previous depreciation
        previous_schedules = DepreciationSchedule.objects.filter(
            asset=asset,
            period_date__lt=period_date
        ).order_by('-period_date')
        
        if previous_schedules.exists():
            last_schedule = previous_schedules.first()
            accumulated_to_date = last_schedule.accumulated_depreciation
        else:
            accumulated_to_date = Decimal('0.00')
        
        # Calculate months elapsed since depreciation start
        if not asset.depreciation_start_date:
            return Decimal('0.00'), accumulated_to_date, asset.acquisition_cost
        
        start_date = asset.depreciation_start_date
        months_elapsed = (
            (period_date.year - start_date.year) * 12 +
            (period_date.month - start_date.month)
        )
        
        # Calculate depreciation based on method
        if asset.depreciation_method == 'STRAIGHT_LINE':
            depreciation_amount = self.calculate_straight_line_depreciation(asset, period_date)
        
        elif asset.depreciation_method == 'DECLINING_BALANCE':
            depreciation_amount = self.calculate_declining_balance_depreciation(
                asset, period_date, accumulated_to_date
            )
        
        elif asset.depreciation_method == 'SUM_OF_YEARS':
            depreciation_amount = self.calculate_sum_of_years_depreciation(
                asset, period_date, months_elapsed
            )
        
        elif asset.depreciation_method == 'UNITS_OF_PRODUCTION':
            depreciation_amount = self.calculate_units_of_production_depreciation(
                asset, period_date, units_produced=0
            )
        
        else:
            depreciation_amount = Decimal('0.00')
        
        # Calculate new accumulated and net book value
        new_accumulated = accumulated_to_date + depreciation_amount
        net_book_value = asset.acquisition_cost - new_accumulated
        
        # Ensure net book value doesn't go below salvage value
        if net_book_value < asset.salvage_value:
            excess = asset.salvage_value - net_book_value
            depreciation_amount -= excess
            new_accumulated = accumulated_to_date + depreciation_amount
            net_book_value = asset.acquisition_cost - new_accumulated
        
        return depreciation_amount, new_accumulated, net_book_value
    
    def generate_depreciation_schedule(self, asset):
        """
        Generate full depreciation schedule for an asset
        Creates monthly entries from depreciation start date to end of useful life
        """
        if not asset.depreciation_start_date or not asset.useful_life_years:
            return []
        
        schedules = []
        start_date = asset.depreciation_start_date
        
        # Calculate end date
        end_date = start_date + relativedelta(years=asset.useful_life_years)
        
        # Generate monthly schedules
        current_date = start_date.replace(day=1)  # Start of first month
        
        while current_date < end_date:
            # Check if schedule already exists
            existing = DepreciationSchedule.objects.filter(
                asset=asset,
                period_date=current_date
            ).first()
            
            if not existing:
                depreciation_amount, accumulated, nbv = self.calculate_depreciation_for_period(
                    asset, current_date
                )
                
                if depreciation_amount > 0:
                    schedule = DepreciationSchedule.objects.create(
                        asset=asset,
                        period_date=current_date,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation=accumulated,
                        net_book_value=nbv,
                        is_posted=False
                    )
                    schedules.append(schedule)
            
            # Move to next month
            current_date = current_date + relativedelta(months=1)
        
        return schedules
    
    def calculate_monthly_depreciation(self, period_date):
        """
        Calculate depreciation for all active assets for a specific month
        Returns list of DepreciationSchedule objects
        """
        if isinstance(period_date, str):
            period_date = datetime.strptime(period_date, '%Y-%m-%d').date()
        
        # Get all active/capitalized assets (both statuses should be depreciated)
        active_assets = Asset.objects.filter(
            status__in=['ACTIVE', 'CAPITALIZED'],
            depreciation_start_date__lte=period_date
        )
        
        schedules = []
        
        for asset in active_assets:
            # Check if schedule already exists
            existing = DepreciationSchedule.objects.filter(
                asset=asset,
                period_date=period_date
            ).first()
            
            if existing:
                schedules.append(existing)
            else:
                # Calculate and create schedule
                depreciation_amount, accumulated, nbv = self.calculate_depreciation_for_period(
                    asset, period_date
                )
                
                if depreciation_amount > 0:
                    schedule = DepreciationSchedule.objects.create(
                        asset=asset,
                        period_date=period_date,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation=accumulated,
                        net_book_value=nbv,
                        is_posted=False
                    )
                    schedules.append(schedule)
        
        return schedules
    
    @transaction.atomic
    def post_monthly_depreciation(self, period_date, user):
        """
        Post depreciation entries for a month
        Creates journal entries for all unposted depreciation schedules
        """
        if isinstance(period_date, str):
            period_date = datetime.strptime(period_date, '%Y-%m-%d').date()
        
        # Get unposted schedules for the period
        schedules = DepreciationSchedule.objects.filter(
            period_date=period_date,
            is_posted=False
        ).select_related('asset', 'asset__category')
        
        if not schedules.exists():
            return {
                'success': True,
                'message': 'No unposted depreciation entries found',
                'count': 0
            }
        
        posted_count = 0
        total_amount = Decimal('0.00')
        gl_service = AssetGLService()
        
        for schedule in schedules:
            asset = schedule.asset
            
            # Verify GL accounts exist
            if not asset.depreciation_expense_account or not asset.accumulated_depreciation_account:
                continue
            
            # Create journal entry using GL service
            try:
                journal = gl_service.create_depreciation_journal(schedule, user)
                posted_count += 1
                total_amount += schedule.depreciation_amount
            except Exception as e:
                # Log error but continue with other assets
                print(f"Error posting depreciation for {asset.asset_number}: {str(e)}")
                continue
        
        return {
            'success': True,
            'message': f'Posted {posted_count} depreciation entries',
            'count': posted_count,
            'total_amount': str(total_amount),
            'period_date': period_date.strftime('%Y-%m-%d')
        }


class AssetProcurementService:
    """
    Service for creating assets from procurement (GRN)
    Handles automatic asset creation when capitalizable items are received
    """
    
    @transaction.atomic
    def create_asset_from_grn(self, grn_line, category=None, location=None, user=None):
        """
        Create an asset from a GRN line
        
        Args:
            grn_line: GRNLine instance
            category: AssetCategory instance (optional, will try to auto-detect)
            location: AssetLocation instance (optional, will use warehouse location)
            user: User creating the asset
            
        Returns:
            Asset instance or None if not capitalizable
        """
        from .models import Asset, AssetCategory, AssetLocation
        
        # Check if item should be capitalized
        catalog_item = grn_line.catalog_item
        
        # Only create assets for categorized goods with catalog items
        if grn_line.goods_receipt.grn_type != 'CATEGORIZED_GOODS':
            return None
        
        # Check if catalog item is flagged as capitalizable
        # For now, we'll assume items with 'asset' or 'equipment' in category are capitalizable
        # In future, add a boolean field to CatalogItem model: is_capitalizable
        if not catalog_item:
            return None
        
        # Try to find matching asset category
        if not category:
            # Try to match by catalog item category or name
            category_name = getattr(catalog_item, 'category', None)
            if category_name:
                category = AssetCategory.objects.filter(
                    name__icontains=category_name
                ).first()
            
            # If still no category, use a default 'Equipment' category
            if not category:
                category, _ = AssetCategory.objects.get_or_create(
                    code='EQUIP',
                    defaults={
                        'name': 'Equipment',
                        'description': 'General equipment and machinery'
                    }
                )
        
        # Try to find or create matching location
        if not location:
            # Use warehouse as location
            warehouse = grn_line.goods_receipt.warehouse
            location, _ = AssetLocation.objects.get_or_create(
                code=warehouse.code,
                defaults={
                    'name': warehouse.name,
                    'description': f'Location for {warehouse.name}',
                    'location_type': 'WAREHOUSE'
                }
            )
        
        # Calculate acquisition cost
        acquisition_cost = (grn_line.unit_price or Decimal('0.00')) * grn_line.accepted_quantity
        
        # Create the asset
        asset = Asset.objects.create(
            # Basic info from catalog item
            name=catalog_item.description or catalog_item.item_code,
            category=category,
            description=grn_line.item_description,
            
            # Acquisition details
            acquisition_cost=acquisition_cost,
            acquisition_date=grn_line.goods_receipt.receipt_date,
            supplier=grn_line.goods_receipt.supplier,
            
            # Location
            location=location,
            
            # Status
            status='DRAFT',  # Will be capitalized separately
            
            # Procurement reference
            po_reference=grn_line.goods_receipt.po_reference,
            
            # Tracking
            serial_number=grn_line.serial_numbers[0] if grn_line.serial_numbers else '',
            barcode=grn_line.lot_number,
            
            # User tracking
            created_by=user
        )
        
        # Store GRN reference in asset notes
        asset.notes = f"Created from GRN {grn_line.goods_receipt.grn_number}, Line {grn_line.line_number}"
        asset.save()
        
        return asset
    
    @transaction.atomic
    def bulk_create_assets_from_grn(self, goods_receipt, user=None):
        """
        Create multiple assets from all eligible GRN lines
        
        Args:
            goods_receipt: GoodsReceipt instance
            user: User creating the assets
            
        Returns:
            dict with created assets count and list
        """
        created_assets = []
        skipped_lines = []
        
        # Only process completed GRNs for categorized goods
        if goods_receipt.grn_type != 'CATEGORIZED_GOODS':
            return {
                'success': False,
                'message': 'Only CATEGORIZED_GOODS GRNs can create assets',
                'created_count': 0,
                'skipped_count': 0
            }
        
        for line in goods_receipt.lines.all():
            # Only create assets for accepted quantities
            if line.accepted_quantity <= 0:
                skipped_lines.append({
                    'line': line.line_number,
                    'reason': 'No accepted quantity'
                })
                continue
            
            # Try to create asset
            try:
                asset = self.create_asset_from_grn(line, user=user)
                if asset:
                    created_assets.append(asset)
                else:
                    skipped_lines.append({
                        'line': line.line_number,
                        'reason': 'Not capitalizable'
                    })
            except Exception as e:
                skipped_lines.append({
                    'line': line.line_number,
                    'reason': str(e)
                })
        
        return {
            'success': True,
            'message': f'Created {len(created_assets)} assets from GRN {goods_receipt.grn_number}',
            'created_count': len(created_assets),
            'skipped_count': len(skipped_lines),
            'assets': created_assets,
            'skipped': skipped_lines
        }
