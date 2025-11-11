
from decimal import Decimal
from rest_framework import serializers
from .models import Invoice, InvoiceLine, InvoiceStatus, JournalEntry, JournalLine, JournalLineSegment, BankAccount
from segment.models import XX_Segment, XX_SegmentType
from ar.models import ARInvoice, ARItem, ARPayment, ARPaymentAllocation, InvoiceGLLine
from ap.models import APInvoice, APItem, APPayment, APPaymentAllocation, APInvoiceGLLine
from core.models import Currency, TaxRate
from .services import validate_ready_to_post, ar_totals, ap_totals
from django.core.exceptions import ValidationError as DjangoValidationError

class CurrencySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Currency
        fields = ["id", "code", "name", "symbol", "is_base"]
        read_only_fields = ["id"]


class JournalLineSegmentSerializer(serializers.ModelSerializer):
    """Serializer for dynamic segment assignments on journal lines"""
    segment_type_name = serializers.CharField(source='segment_type.segment_name', read_only=True)
    segment_code = serializers.CharField(source='segment.code', read_only=True)
    segment_alias = serializers.CharField(source='segment.alias', read_only=True)
    
    class Meta:
        model = JournalLineSegment
        fields = ["id", "segment_type", "segment_type_name", "segment", "segment_code", "segment_alias"]
        read_only_fields = ["id", "segment_type_name", "segment_code", "segment_alias"]
    
    def validate_segment(self, value):
        """Validate that only child segments are selected"""
        if value and value.node_type != 'child':
            raise serializers.ValidationError(
                f"Only child segments can be assigned. "
                f"Segment '{value.code}' is a '{value.node_type}' type. "
                f"Please select a child segment."
            )
        return value
    
    def validate(self, data):
        """Validate that segment belongs to the specified segment_type"""
        segment = data.get('segment')
        segment_type = data.get('segment_type')
        
        if segment and segment_type:
            if segment.segment_type_id != segment_type.segment_id:
                raise serializers.ValidationError({
                    'segment': f"Segment '{segment.code}' does not belong to segment type '{segment_type.segment_name}'"
                })
        
        return data


class JournalLineSerializer(serializers.ModelSerializer):
    segments = JournalLineSegmentSerializer(many=True, required=False)
    
    class Meta:
        model = JournalLine
        fields = ["id", "account", "debit", "credit", "segments"]
    
    def validate(self, data):
        """Validate that all required segment types have a segment assigned"""
        segments_data = data.get('segments', [])
        
        # Get all required segment types
        required_segment_types = XX_SegmentType.objects.filter(is_required=True, is_active=True)
        
        # Check that we have a segment for each required type
        provided_types = {seg['segment_type'].segment_id for seg in segments_data if 'segment_type' in seg}
        required_types = {st.segment_id for st in required_segment_types}
        
        missing_types = required_types - provided_types
        if missing_types:
            missing_names = [
                st.segment_name for st in required_segment_types 
                if st.segment_id in missing_types
            ]
            raise serializers.ValidationError({
                'segments': f"Missing required segment types: {', '.join(missing_names)}. "
                           f"You must provide one child segment from each required segment type."
            })
        
        return data
    
    def create(self, validated_data):
        segments_data = validated_data.pop('segments', [])
        journal_line = JournalLine.objects.create(**validated_data)
        
        # Create segment assignments
        for segment_data in segments_data:
            JournalLineSegment.objects.create(
                journal_line=journal_line,
                **segment_data
            )
        
        return journal_line
    
    def update(self, instance, validated_data):
        segments_data = validated_data.pop('segments', None)
        
        # Update journal line fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update segments if provided
        if segments_data is not None:
            # Delete existing segments
            instance.segments.all().delete()
            
            # Create new segments
            for segment_data in segments_data:
                JournalLineSegment.objects.create(
                    journal_line=instance,
                    **segment_data
                )
        
        return instance

class JournalLineDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for journal lines with nested entry, account info, and segments"""
    entry = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()
    segments = JournalLineSegmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = JournalLine
        fields = ["id", "debit", "credit", "entry", "account", "segments"]
    
    def get_entry(self, obj):
        return {
            "id": obj.entry.id,
            "date": obj.entry.date,
            "memo": obj.entry.memo,
            "posted": obj.entry.posted,
            "currency": obj.entry.currency.id if obj.entry.currency else None,
        }
    
    def get_account(self, obj):
        return {
            "id": obj.account.id,
            "code": obj.account.code,
            "name": obj.account.alias,  # XX_Segment uses 'alias' not 'name'
            "type": obj.account.segment_type.segment_type if obj.account.segment_type else "account",
        }

class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    
    class Meta: 
        model = JournalEntry
        fields = ["id", "date", "currency", "memo", "posted", "lines"]
        read_only_fields = ["posted"]
    
    def validate_lines(self, lines_data):
        """Validate that debits equal credits"""
        total_debit = sum(Decimal(line.get('debit', 0)) for line in lines_data)
        total_credit = sum(Decimal(line.get('credit', 0)) for line in lines_data)
        
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"Total debits ({total_debit}) must equal total credits ({total_credit})"
            )
        
        return lines_data
    
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        entry = JournalEntry.objects.create(**validated_data)
        
        for line_data in lines_data:
            segments_data = line_data.pop('segments', [])
            journal_line = JournalLine.objects.create(entry=entry, **line_data)
            
            # Create segment assignments
            for segment_data in segments_data:
                JournalLineSegment.objects.create(
                    journal_line=journal_line,
                    **segment_data
                )
        
        return entry

class ARItemSerializer(serializers.ModelSerializer):
    tax_rate = serializers.PrimaryKeyRelatedField(
        queryset=TaxRate.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta: 
        model = ARItem
        fields = ["id","description","quantity","unit_price","tax_rate"]

class InvoiceGLLineSerializer(serializers.Serializer):
    """Serializer for AR Invoice GL Distribution Lines - DEPRECATED"""
    id = serializers.IntegerField(required=False)
    account = serializers.IntegerField(required=False)
    account_code = serializers.CharField(required=False, allow_blank=True)
    account_name = serializers.CharField(required=False, allow_blank=True)
    line_type = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

class ARInvoiceSerializer(serializers.ModelSerializer):
    items = ARItemSerializer(many=True)
    gl_lines = InvoiceGLLineSerializer(many=True, required=False)
    totals = serializers.SerializerMethodField()
    invoice_number = serializers.CharField(source='number', required=False)
    subtotal = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta: 
        model = ARInvoice
        fields = ["id","customer","customer_name","number","invoice_number","date","due_date","currency","currency_code","country","exchange_rate","base_currency_total","is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","items","gl_lines","totals","subtotal","tax_amount","total","paid_amount","balance"]
        read_only_fields = ["is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","exchange_rate","base_currency_total","totals","subtotal","tax_amount","total","paid_amount","balance","customer_name","currency_code"]
    
    def validate(self, attrs):
        print(f"DEBUG validate(): Received attrs keys: {attrs.keys()}")
        print(f"DEBUG validate(): Items count: {len(attrs.get('items', []))}")
        if 'items' in attrs:
            print(f"DEBUG validate(): Items data: {attrs['items']}")
        return attrs
    
    def _get_cached_totals(self, obj):
        """Cache totals calculation to avoid multiple database queries"""
        if not hasattr(obj, '_cached_totals'):
            obj._cached_totals = ar_totals(obj)
        return obj._cached_totals
    
    def get_totals(self, obj): 
        return self._get_cached_totals(obj)
    
    def get_subtotal(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.subtotal is not None:
            return str(obj.subtotal)
        return str(self._get_cached_totals(obj)["subtotal"])
    
    def get_tax_amount(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.tax_amount is not None:
            return str(obj.tax_amount)
        return str(self._get_cached_totals(obj)["tax"])
    
    def get_total(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.total is not None:
            return str(obj.total)
        return str(self._get_cached_totals(obj)["total"])
    
    def get_paid_amount(self, obj):
        return str(self._get_cached_totals(obj)["paid"])
    
    def get_balance(self, obj):
        return str(self._get_cached_totals(obj)["balance"])
    
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        gl_lines_data = validated_data.pop("gl_lines", [])
        print(f"DEBUG: Creating AR Invoice with {len(items_data)} items and {len(gl_lines_data)} GL lines")
        print(f"DEBUG: Items data: {items_data}")
        print(f"DEBUG: GL lines data: {gl_lines_data}")
        
        # Validate GL lines are provided
        if not gl_lines_data or len(gl_lines_data) == 0:
            raise serializers.ValidationError("GL distribution lines are required. Please add at least one GL line.")
        
        inv = ARInvoice.objects.create(**validated_data)
        print(f"DEBUG: Created invoice #{inv.id}: {inv.number}")
        
        created_items = 0
        skipped_items = []
        
        for idx, item_data in enumerate(items_data):
            try:
                print(f"DEBUG: Creating item {idx+1}: {item_data}")
                # Filter out empty descriptions or invalid data
                if not item_data.get('description') or not item_data.get('description').strip():
                    print(f"DEBUG: Skipping item {idx+1} - empty description")
                    skipped_items.append(idx + 1)
                    continue
                    
                item = ARItem.objects.create(invoice=inv, **item_data)
                print(f"DEBUG: Created item #{item.id}")
                created_items += 1
            except Exception as e:
                print(f"DEBUG: ERROR creating item {idx+1}: {e}")
                # Delete the invoice if item creation fails
                inv.delete()
                raise serializers.ValidationError(f"Failed to create item {idx+1}: {str(e)}")
        
        # Check if no items were created
        if created_items == 0:
            inv.delete()  # Delete invoice if no valid items
            if skipped_items:
                raise serializers.ValidationError(
                    f"Invoice not created: All {len(items_data)} items have empty descriptions. "
                    f"Please provide a description for each item."
                )
            else:
                raise serializers.ValidationError(
                    "Invoice not created: No valid items provided. Please add at least one item with a description."
                )
        
        # Refresh from DB to ensure related items are loaded
        inv.refresh_from_db()
        item_count = inv.items.count()
        print(f"DEBUG: Invoice now has {item_count} items after refresh (created {created_items}, skipped {len(skipped_items)})")
        
        # Calculate and save totals to database
        inv.calculate_and_save_totals()
        print(f"DEBUG: Saved totals - Subtotal: {inv.subtotal}, Tax: {inv.tax_amount}, Total: {inv.total}")
        
        # Create GL distribution lines (REQUIRED)
        from decimal import Decimal
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        
        for gl_line_data in gl_lines_data:
            gl_line = InvoiceGLLine.objects.create(invoice=inv, **gl_line_data)
            if gl_line.line_type == 'DEBIT':
                total_debits += gl_line.amount
            else:
                total_credits += gl_line.amount
        
        # Validate that debits = credits = invoice total
        invoice_total = inv.total or Decimal('0.00')
        if total_debits != total_credits:
            inv.delete()
            raise serializers.ValidationError(
                f"GL lines validation failed: Total debits ({total_debits}) must equal total credits ({total_credits})"
            )
        if total_debits != invoice_total:
            inv.delete()
            raise serializers.ValidationError(
                f"GL lines validation failed: Total debits/credits ({total_debits}) must equal invoice total ({invoice_total})"
            )
        
        print(f"DEBUG: Created {len(gl_lines_data)} GL lines. Debits={total_debits}, Credits={total_credits}, Invoice Total={invoice_total}")
        
        return inv
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        print(f"DEBUG: Updating AR Invoice #{instance.id}")
        print(f"DEBUG: Validated data keys: {validated_data.keys()}")
        
        # Check if invoice can be edited
        if instance.is_posted:
            raise serializers.ValidationError("Cannot edit posted invoices")
        if instance.is_cancelled:
            raise serializers.ValidationError("Cannot edit cancelled invoices")
        
        # Update invoice fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        print(f"DEBUG: Updated invoice fields")
        
        # Update items if provided
        if items_data is not None:
            print(f"DEBUG: Updating items - received {len(items_data)} items")
            # Delete existing items
            instance.items.all().delete()
            print(f"DEBUG: Deleted old items")
            
            created_items = 0
            for idx, item_data in enumerate(items_data):
                try:
                    print(f"DEBUG: Creating item {idx+1}: {item_data}")
                    if not item_data.get('description') or not item_data.get('description').strip():
                        print(f"DEBUG: Skipping item {idx+1} - empty description")
                        continue
                        
                    item = ARItem.objects.create(invoice=instance, **item_data)
                    print(f"DEBUG: Created item #{item.id}")
                    created_items += 1
                except Exception as e:
                    print(f"DEBUG: ERROR creating item {idx+1}: {e}")
                    raise serializers.ValidationError(f"Failed to create item {idx+1}: {str(e)}")
            
            if created_items == 0:
                raise serializers.ValidationError("Invoice must have at least one item with a description")
            
            print(f"DEBUG: Created {created_items} new items")
        
        # Refresh from DB
        instance.refresh_from_db()
        print(f"DEBUG: Invoice update complete - now has {instance.items.count()} items")
        
        # Recalculate and save totals to database
        instance.calculate_and_save_totals()
        print(f"DEBUG: Updated totals - Subtotal: {instance.subtotal}, Tax: {instance.tax_amount}, Total: {instance.total}")
        
        return instance

# Payment Allocation Serializers
class ARPaymentAllocationSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    invoice_currency_code = serializers.CharField(source='invoice_currency.code', read_only=True)
    
    class Meta:
        model = ARPaymentAllocation
        fields = [
            'id', 'payment', 'invoice', 'invoice_number', 
            'amount', 'memo', 'created_at',
            'invoice_currency', 'invoice_currency_code', 'current_exchange_rate'
        ]
        read_only_fields = ['id', 'created_at', 'invoice_currency', 'current_exchange_rate']

class APPaymentAllocationSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    invoice_currency_code = serializers.CharField(source='invoice_currency.code', read_only=True)
    
    class Meta:
        model = APPaymentAllocation
        fields = [
            'id', 'payment', 'invoice', 'invoice_number', 
            'amount', 'memo', 'created_at',
            'invoice_currency', 'invoice_currency_code', 'current_exchange_rate'
        ]
        read_only_fields = ['id', 'created_at', 'invoice_currency', 'current_exchange_rate']

class ARPaymentSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(source='invoice.customer', read_only=True)
    customer_name = serializers.CharField(source='invoice.customer.name', read_only=True)
    payment_date = serializers.DateField(source='date')
    reference_number = serializers.CharField(source='invoice.number', read_only=True)
    status = serializers.SerializerMethodField()
    invoice_currency_code = serializers.CharField(source='invoice_currency.code', read_only=True)
    payment_currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta:
        model = ARPayment
        fields = ["id", "customer", "customer_name", "payment_date", "amount", "reference_number", 
                  "memo", "bank_account", "invoice", "status", "posted_at", "reconciled",
                  "invoice_currency", "invoice_currency_code", "exchange_rate", 
                  "currency", "payment_currency_code"]
        extra_kwargs = {
            'invoice': {'write_only': False},
            'date': {'write_only': True}
        }
        read_only_fields = ['invoice_currency', 'exchange_rate']
    
    def get_status(self, obj):
        """Return payment status based on posted_at"""
        if obj.posted_at:
            return 'POSTED'
        return 'DRAFT'

    def validate(self, data):
        # Handle date field mapping
        if 'date' in data:
            date_value = data['date']
        elif 'payment_date' in self.initial_data:
            data['date'] = self.initial_data['payment_date']
            date_value = data['date']
        
        amt = data.get("amount") or 0
        if amt <= 0:
            raise serializers.ValidationError("Payment amount must be positive.")

        invoice = data.get("invoice") or (self.instance.invoice if self.instance else None)
        if invoice and not invoice.gl_journal:
            raise serializers.ValidationError("Cannot apply payment: invoice is not posted yet.")

        from .services import ar_totals, q2
        totals = ar_totals(invoice)
        existing = self.instance.amount if self.instance else Decimal("0.00")
        remaining = q2(totals["balance"] + existing)

        if amt > remaining:
            raise serializers.ValidationError(f"Payment exceeds invoice balance ({remaining:.2f}).")

        return data

class APItemSerializer(serializers.ModelSerializer):
    tax_rate = serializers.PrimaryKeyRelatedField(
        queryset=TaxRate.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta: 
        model = APItem
        fields = ["id","description","quantity","unit_price","tax_rate"]

class APInvoiceGLLineSerializer(serializers.Serializer):
    """Serializer for AP Invoice GL Distribution Lines (deprecated model)"""
    id = serializers.IntegerField(required=False)
    account = serializers.IntegerField(required=False)
    account_code = serializers.CharField(required=False, allow_blank=True)
    account_name = serializers.CharField(required=False, allow_blank=True)
    line_type = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

class APInvoiceSerializer(serializers.ModelSerializer):
    items = APItemSerializer(many=True)
    gl_lines = APInvoiceGLLineSerializer(many=True, required=False)
    totals = serializers.SerializerMethodField()
    invoice_number = serializers.CharField(source='number', required=False)
    subtotal = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    # GRN and PO display fields
    grn_number = serializers.CharField(source='goods_receipt.grn_number', read_only=True, allow_null=True)
    po_number = serializers.CharField(source='po_header.po_number', read_only=True, allow_null=True)
    
    # Include the IDs explicitly for frontend checking
    goods_receipt_id = serializers.IntegerField(source='goods_receipt.id', read_only=True, allow_null=True)
    po_header_id = serializers.IntegerField(source='po_header.id', read_only=True, allow_null=True)
    
    class Meta: 
        model = APInvoice
        fields = ["id","supplier","supplier_name","number","invoice_number","date","due_date","currency","currency_code","country","exchange_rate","base_currency_total","po_header","po_number","po_header_id","goods_receipt","grn_number","goods_receipt_id","three_way_match_status","match_variance_amount","match_variance_notes","match_performed_at","is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","items","gl_lines","totals","subtotal","tax_amount","total","paid_amount","balance"]
        read_only_fields = ["is_posted","payment_status","is_cancelled","posted_at","paid_at","cancelled_at","exchange_rate","base_currency_total","three_way_match_status","match_variance_amount","match_variance_notes","match_performed_at","totals","subtotal","tax_amount","total","paid_amount","balance","supplier_name","currency_code","grn_number","po_number","goods_receipt_id","po_header_id"]

    
    def validate(self, attrs):
        print(f"DEBUG validate(): Received attrs keys: {attrs.keys()}")
        print(f"DEBUG validate(): Items count: {len(attrs.get('items', []))}")
        if 'items' in attrs:
            print(f"DEBUG validate(): Items data: {attrs['items']}")
        return attrs
    
    def _get_cached_totals(self, obj):
        """Cache totals calculation to avoid multiple database queries"""
        if not hasattr(obj, '_cached_totals'):
            obj._cached_totals = ap_totals(obj)
        return obj._cached_totals
    
    def get_totals(self, obj): 
        return self._get_cached_totals(obj)
    
    def get_subtotal(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.subtotal is not None:
            return str(obj.subtotal)
        return str(self._get_cached_totals(obj)["subtotal"])
    
    def get_tax_amount(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.tax_amount is not None:
            return str(obj.tax_amount)
        return str(self._get_cached_totals(obj)["tax"])
    
    def get_total(self, obj):
        # Use stored value if available, otherwise calculate
        if obj.total is not None:
            return str(obj.total)
        return str(self._get_cached_totals(obj)["total"])
    
    def get_paid_amount(self, obj):
        return str(self._get_cached_totals(obj)["paid"])
    
    def get_balance(self, obj):
        return str(self._get_cached_totals(obj)["balance"])
    
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        gl_lines_data = validated_data.pop("gl_lines", [])  # Accept but don't use (deprecated)
        print(f"DEBUG: Creating AP Invoice with {len(items_data)} items")
        print(f"DEBUG: Items data: {items_data}")
        if gl_lines_data:
            print(f"DEBUG: GL lines data (deprecated): {len(gl_lines_data)} lines")
        
        inv = APInvoice.objects.create(**validated_data)
        print(f"DEBUG: Created invoice #{inv.id}: {inv.number}")
        
        created_items = 0
        skipped_items = []
        
        for idx, item_data in enumerate(items_data):
            try:
                print(f"DEBUG: Creating item {idx+1}: {item_data}")
                # Filter out empty descriptions or invalid data
                if not item_data.get('description') or not item_data.get('description').strip():
                    print(f"DEBUG: Skipping item {idx+1} - empty description")
                    skipped_items.append(idx + 1)
                    continue
                    
                item = APItem.objects.create(invoice=inv, **item_data)
                print(f"DEBUG: Created item #{item.id}")
                created_items += 1
            except Exception as e:
                print(f"DEBUG: ERROR creating item {idx+1}: {e}")
                # Delete the invoice if item creation fails
                inv.delete()
                raise serializers.ValidationError(f"Failed to create item {idx+1}: {str(e)}")
        
        # Check if no items were created
        if created_items == 0:
            inv.delete()  # Delete invoice if no valid items
            if skipped_items:
                raise serializers.ValidationError(
                    f"Invoice not created: All {len(items_data)} items have empty descriptions. "
                    f"Please provide a description for each item."
                )
            else:
                raise serializers.ValidationError(
                    "Invoice not created: No valid items provided. Please add at least one item with a description."
                )
        
        # Refresh from DB to ensure related items are loaded
        inv.refresh_from_db()
        item_count = inv.items.count()
        print(f"DEBUG: Invoice now has {item_count} items after refresh (created {created_items}, skipped {len(skipped_items)})")
        
        # Calculate and save totals to database
        inv.calculate_and_save_totals()
        print(f"DEBUG: Saved totals - Subtotal: {inv.subtotal}, Tax: {inv.tax_amount}, Total: {inv.total}")
        
        # Note: GL distribution lines are deprecated and no longer created
        # The GL lines are now handled when the invoice is posted to GL
        if gl_lines_data:
            print(f"DEBUG: Received {len(gl_lines_data)} GL lines (deprecated - not creating)")
        
        print(f"DEBUG: Invoice creation complete. Invoice #{inv.id}: {inv.number}")
        
        # Note: 3-way match is now triggered manually via the API endpoint
        # POST /api/ap/invoices/{id}/three-way-match/
        # The old automatic matching has been disabled
        if inv.po_header_id and inv.goods_receipt_id:
            print(f"DEBUG: Invoice linked to PO: {inv.po_header_id}, GR: {inv.goods_receipt_id}")
            print(f"DEBUG: User can run 3-way match via API endpoint")
        
        return inv
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        print(f"DEBUG: Updating AP Invoice #{instance.id}")
        print(f"DEBUG: Validated data keys: {validated_data.keys()}")
        
        # Check if invoice can be edited
        if instance.is_posted:
            raise serializers.ValidationError("Cannot edit posted invoices")
        if instance.is_cancelled:
            raise serializers.ValidationError("Cannot edit cancelled invoices")
        
        # Update invoice fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        print(f"DEBUG: Updated invoice fields")
        
        # Update items if provided
        if items_data is not None:
            print(f"DEBUG: Updating items - received {len(items_data)} items")
            # Delete existing items
            instance.items.all().delete()
            print(f"DEBUG: Deleted old items")
            
            created_items = 0
            for idx, item_data in enumerate(items_data):
                try:
                    print(f"DEBUG: Creating item {idx+1}: {item_data}")
                    if not item_data.get('description') or not item_data.get('description').strip():
                        print(f"DEBUG: Skipping item {idx+1} - empty description")
                        continue
                        
                    item = APItem.objects.create(invoice=instance, **item_data)
                    print(f"DEBUG: Created item #{item.id}")
                    created_items += 1
                except Exception as e:
                    print(f"DEBUG: ERROR creating item {idx+1}: {e}")
                    raise serializers.ValidationError(f"Failed to create item {idx+1}: {str(e)}")
            
            if created_items == 0:
                raise serializers.ValidationError("Invoice must have at least one item with a description")
            
            print(f"DEBUG: Created {created_items} new items")
        
        # Refresh from DB
        instance.refresh_from_db()
        print(f"DEBUG: Invoice update complete - now has {instance.items.count()} items")
        
        # Calculate and save totals to database
        instance.calculate_and_save_totals()
        print(f"DEBUG: Saved totals - Subtotal: {instance.subtotal}, Tax: {instance.tax_amount}, Total: {instance.total}")
        
        return instance

class APPaymentSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(source='invoice.supplier', read_only=True)
    supplier_name = serializers.CharField(source='invoice.supplier.name', read_only=True)
    payment_date = serializers.DateField(source='date')
    reference_number = serializers.CharField(source='invoice.number', read_only=True)
    status = serializers.SerializerMethodField()
    invoice_currency_code = serializers.CharField(source='invoice_currency.code', read_only=True)
    payment_currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta:
        model = APPayment
        fields = ["id", "supplier", "supplier_name", "payment_date", "amount", "reference_number", 
                  "memo", "bank_account", "invoice", "status", "posted_at", "reconciled",
                  "invoice_currency", "invoice_currency_code", "exchange_rate",
                  "currency", "payment_currency_code"]
        extra_kwargs = {
            'invoice': {'write_only': False},
            'date': {'write_only': True}
        }
        read_only_fields = ['invoice_currency', 'exchange_rate']
    
    def get_status(self, obj):
        """Return payment status based on posted_at"""
        if obj.posted_at:
            return 'POSTED'
        return 'DRAFT'

    def validate(self, data):
        # Handle date field mapping
        if 'date' in data:
            date_value = data['date']
        elif 'payment_date' in self.initial_data:
            data['date'] = self.initial_data['payment_date']
            date_value = data['date']
        
        amt = data.get("amount") or 0
        if amt <= 0:
            raise serializers.ValidationError("Payment amount must be positive.")

        invoice = data.get("invoice") or (self.instance.invoice if self.instance else None)
        if invoice and not invoice.gl_journal:
            raise serializers.ValidationError("Cannot apply payment: invoice is not posted yet.")

        from .services import ap_totals, q2
        totals = ap_totals(invoice)
        existing = self.instance.amount if self.instance else Decimal("0.00")
        remaining = q2(totals["balance"] + existing)

        if amt > remaining:
            raise serializers.ValidationError(f"Payment exceeds invoice balance ({remaining:.2f}).")

        return data


class JournalLineReadSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    class Meta:
        model = JournalLine
        fields = ["id","account_code","account_name","debit","credit"]


class JournalEntryReadSerializer(serializers.ModelSerializer):
    lines = JournalLineReadSerializer(many=True, read_only=True)
    class Meta:
        model = JournalEntry
        fields = ["id","date","currency","memo","posted","lines"]


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id","name","account_code","iban","swift","currency","active"]

class SeedVATRequestSerializer(serializers.Serializer):
    effective_from = serializers.DateField(required=False)

class CorpTaxAccrualRequestSerializer(serializers.Serializer):
    country = serializers.ChoiceField(choices=[("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")])
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ("id", "description", "account", "tax_code", "quantity", "unit_price",
                  "amount_net", "tax_amount", "amount_gross")
        read_only_fields = ("amount_net", "tax_amount", "amount_gross")

class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ("id", "invoice_no", "customer", "currency", "status",
                  "total_net", "total_tax", "total_gross", "posted_at", "lines")
        read_only_fields = ("total_net", "total_tax", "total_gross", "posted_at")

    def validate(self, attrs):
        instance = self.instance or Invoice(**attrs)
        # If updating posted: block (read-only)
        if self.instance and self.instance.status == InvoiceStatus.POSTED:
            raise serializers.ValidationError("Posted invoices are read-only. Use reversal API.")
        return attrs

    def create(self, validated):
        lines_data = validated.pop("lines", [])
        inv = Invoice.objects.create(**validated)
        for ld in lines_data:
            InvoiceLine.objects.create(invoice=inv, **ld)
        inv.recompute_totals()
        inv.save(update_fields=["total_net", "total_tax", "total_gross", "updated_at"])
        return inv

    def update(self, instance, validated):
        lines = validated.pop("lines", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()

        if lines is not None:
            # replace lines for simplicity (or implement delta)
            instance.lines.all().delete()
            for ld in lines:
                InvoiceLine.objects.create(invoice=instance, **ld)

        instance.recompute_totals()
        instance.save(update_fields=["total_net", "total_tax", "total_gross", "updated_at"])
        return instance


# ========== FX (Foreign Exchange) Serializers ==========

from core.models import ExchangeRate, FXGainLossAccount, Currency


class ExchangeRateSerializer(serializers.ModelSerializer):
    from_currency_code = serializers.CharField(source='from_currency.code', read_only=True)
    to_currency_code = serializers.CharField(source='to_currency.code', read_only=True)
    
    class Meta:
        model = ExchangeRate
        fields = [
            'id', 'from_currency', 'to_currency', 'from_currency_code', 'to_currency_code',
            'rate_date', 'rate', 'rate_type', 'source', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ExchangeRateCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating exchange rates with currency codes"""
    from_currency_code = serializers.CharField(max_length=3)
    to_currency_code = serializers.CharField(max_length=3)
    rate = serializers.DecimalField(max_digits=18, decimal_places=6)
    rate_date = serializers.DateField()
    rate_type = serializers.ChoiceField(
        choices=['SPOT', 'AVERAGE', 'FIXED', 'CLOSING'],
        default='SPOT'
    )
    source = serializers.CharField(max_length=128, required=False, allow_blank=True)
    
    def validate(self, data):
        # Validate currencies exist
        from_code = data['from_currency_code']
        to_code = data['to_currency_code']
        
        try:
            Currency.objects.get(code=from_code)
        except Currency.DoesNotExist:
            raise serializers.ValidationError(f"Currency {from_code} does not exist")
        
        try:
            Currency.objects.get(code=to_code)
        except Currency.DoesNotExist:
            raise serializers.ValidationError(f"Currency {to_code} does not exist")
        
        if from_code == to_code:
            raise serializers.ValidationError("From and to currencies cannot be the same")
        
        return data


class FXGainLossAccountSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = FXGainLossAccount
        fields = ['id', 'account', 'account_code', 'account_name', 'gain_loss_type', 'is_active', 'notes']


class CurrencyConversionRequestSerializer(serializers.Serializer):
    """Request serializer for currency conversion API"""
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    from_currency_code = serializers.CharField(max_length=3)
    to_currency_code = serializers.CharField(max_length=3)
    rate_date = serializers.DateField()
    rate_type = serializers.ChoiceField(
        choices=['SPOT', 'AVERAGE', 'FIXED', 'CLOSING'],
        default='SPOT',
        required=False
    )

