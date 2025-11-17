
from decimal import Decimal
from rest_framework import serializers
from .models import JournalEntry, JournalLine, JournalLineSegment, BankAccount
from segment.models import XX_Segment, XX_SegmentType
from ar.models import ARInvoice, ARItem, ARPayment, ARPaymentAllocation, InvoiceGLLine
from ap.models import APInvoice, APItem, APPayment, APPaymentAllocation, APInvoiceGLLine
from core.models import Currency, TaxRate
from .services import ar_totals, ap_totals
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
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate that ALL active segment types have exactly one segment assigned"""
        segments_data = data.get('segments', [])
        
        # Get all active segment types (not just required ones)
        active_segment_types = XX_SegmentType.objects.filter(is_active=True)
        
        # Get provided segment types
        provided_type_ids = [seg['segment_type'].segment_id for seg in segments_data if 'segment_type' in seg]
        expected_type_ids = {st.segment_id for st in active_segment_types}
        provided_type_set = set(provided_type_ids)
        
        # Check for missing segment types
        missing_types = expected_type_ids - provided_type_set
        if missing_types:
            missing_names = [
                st.segment_name for st in active_segment_types 
                if st.segment_id in missing_types
            ]
            raise serializers.ValidationError({
                'segments': f"Missing segment types: {', '.join(missing_names)}. "
                           f"You must provide exactly one segment for EACH active segment type. "
                           f"Expected {len(expected_type_ids)} segment types, got {len(provided_type_set)}."
            })
        
        # Check for extra segment types (not active)
        extra_types = provided_type_set - expected_type_ids
        if extra_types:
            raise serializers.ValidationError({
                'segments': f"Provided segments for inactive or non-existent segment types. "
                           f"Only active segment types are allowed."
            })
        
        # Check for duplicate segment types (should have exactly one per type)
        from collections import Counter
        type_counts = Counter(provided_type_ids)
        duplicates = [type_id for type_id, count in type_counts.items() if count > 1]
        if duplicates:
            duplicate_names = [
                st.segment_name for st in active_segment_types 
                if st.segment_id in duplicates
            ]
            raise serializers.ValidationError({
                'segments': f"Duplicate segment types found: {', '.join(duplicate_names)}. "
                           f"You must provide exactly ONE segment for each segment type."
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
        read_only_fields = ['id']
    
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
        read_only_fields = ['id', "posted"]
    
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
        read_only_fields = ['id']

class InvoiceGLLineSerializer(serializers.Serializer):
    """Serializer for AR Invoice GL Distribution Lines (DEPRECATED - Old single-segment model)
    
    This is the OLD structure with a single 'account' field.
    For NEW invoices using dynamic segments, use ARInvoiceDistributionSerializer instead.
    """
    id = serializers.IntegerField(required=False)
    account = serializers.IntegerField(required=False)
    account_code = serializers.CharField(required=False, allow_blank=True)
    account_name = serializers.CharField(required=False, allow_blank=True)
    line_type = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class ARInvoiceDistributionSegmentSerializer(serializers.Serializer):
    """Serializer for segment assignments in AR dynamic GL distributions"""
    segment_type = serializers.IntegerField(help_text="ID of the segment type (e.g., Account, Department, Cost Center)")
    segment_type_name = serializers.CharField(read_only=True, help_text="Name of the segment type")
    segment = serializers.IntegerField(help_text="ID of the child segment to assign")
    segment_code = serializers.CharField(read_only=True, help_text="Code of the assigned segment")
    segment_name = serializers.CharField(read_only=True, help_text="Name of the assigned segment")
    
    def validate_segment(self, value):
        """Validate that the segment exists and is a child segment"""
        try:
            segment = XX_Segment.objects.get(id=value)
            if segment.node_type != 'child':
                raise serializers.ValidationError(
                    f"Only child segments can be assigned. "
                    f"Segment '{segment.code}' is a '{segment.node_type}' type."
                )
            return value
        except XX_Segment.DoesNotExist:
            raise serializers.ValidationError(f"Segment with ID {value} does not exist")


class ARInvoiceDistributionSerializer(serializers.Serializer):
    """Serializer for AR Invoice GL Distribution Lines (NEW dynamic multi-segment model)"""
    id = serializers.IntegerField(required=False, read_only=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, help_text="Distribution amount")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Description")
    line_type = serializers.ChoiceField(choices=['DEBIT', 'CREDIT'], required=True, help_text="Debit or Credit")
    segments = ARInvoiceDistributionSegmentSerializer(many=True, help_text="Segment assignments")
    
    def validate_segments(self, value):
        """Validate that all required segment types are provided"""
        if not value:
            raise serializers.ValidationError("At least one segment must be provided")
        
        required_types = XX_SegmentType.objects.filter(is_required=True, is_active=True)
        provided_type_ids = {seg['segment_type'] for seg in value}
        required_type_ids = {st.segment_id for st in required_types}
        
        missing = required_type_ids - provided_type_ids
        if missing:
            missing_names = [st.segment_name for st in required_types if st.segment_id in missing]
            raise serializers.ValidationError(f"Missing required segment types: {', '.join(missing_names)}")
        
        for seg_data in value:
            segment_type_id = seg_data['segment_type']
            segment_id = seg_data['segment']
            try:
                segment = XX_Segment.objects.get(id=segment_id)
                if segment.segment_type_id != segment_type_id:
                    raise serializers.ValidationError(
                        f"Segment {segment.code} does not belong to segment type {segment_type_id}"
                    )
            except XX_Segment.DoesNotExist:
                raise serializers.ValidationError(f"Segment {segment_id} does not exist")
        
        return value
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class ARInvoiceSerializer(serializers.ModelSerializer):
    items = ARItemSerializer(many=True)
    gl_lines = InvoiceGLLineSerializer(many=True, required=False)  # OLD: Deprecated single-segment
    distributions = ARInvoiceDistributionSerializer(many=True, required=False)  # NEW: Dynamic multi-segment
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
        fields = ["id","customer","customer_name","number","invoice_number","date","due_date","currency","currency_code","country","exchange_rate","base_currency_total","is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","items","gl_lines","distributions","totals","subtotal","tax_amount","total","paid_amount","balance"]
        read_only_fields = ['id', "is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","exchange_rate","base_currency_total","totals","subtotal","tax_amount","total","paid_amount","balance","customer_name","currency_code"]
    
    def validate(self, attrs):
        print(f"DEBUG validate(): Received attrs keys: {attrs.keys()}")
        print(f"DEBUG validate(): Items count: {len(attrs.get('items', []))}")
        if 'items' in attrs:
            print(f"DEBUG validate(): Items data: {attrs['items']}")
        
        # Check if using new distribution format
        distributions = attrs.get('distributions', [])
        if distributions:
            print(f"DEBUG validate(): Using NEW dynamic segment distributions: {len(distributions)} lines")
        
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
        gl_lines_data = validated_data.pop("gl_lines", [])  # OLD format (deprecated)
        distributions_data = validated_data.pop("distributions", [])  # NEW format (multi-segment)
        
        print(f"DEBUG: Creating AR Invoice with {len(items_data)} items")
        print(f"DEBUG: Items data: {items_data}")
        print(f"DEBUG: Old GL lines: {len(gl_lines_data)}, New distributions: {len(distributions_data)}")
        
        # Support both old and new formats - prefer new format if provided
        if distributions_data:
            print(f"DEBUG: Using NEW distributions format with {len(distributions_data)} lines")
            gl_lines_data = distributions_data  # Use new format
        elif not gl_lines_data:
            # Neither format provided
            raise serializers.ValidationError("GL distribution lines are required. Please add at least one distribution line.")
        
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
        
        # CREATE GL DISTRIBUTION LINES WITH DYNAMIC SEGMENTS
        if gl_lines_data:
            print(f"DEBUG: Creating {len(gl_lines_data)} distributions with dynamic segments")
            from ar.models import InvoiceGLLine, ARInvoiceDistributionSegment
            from segment.models import XX_Segment, XX_SegmentType
            from decimal import Decimal
            
            total_debits = Decimal('0.00')
            total_credits = Decimal('0.00')
            
            for idx, dist_data in enumerate(gl_lines_data):
                try:
                    amount = dist_data['amount']
                    description = dist_data.get('description', '')
                    line_type = dist_data.get('line_type', 'DEBIT')
                    segments_data = dist_data.get('segments', [])
                    
                    print(f"DEBUG: Creating distribution {idx+1}: Amount={amount}, Type={line_type}, Segments={len(segments_data)}")
                    
                    # Create the GL line
                    gl_line = InvoiceGLLine.objects.create(
                        invoice=inv,
                        amount=amount,
                        description=description,
                        line_type=line_type
                    )
                    
                    # Track debits/credits
                    if line_type == 'DEBIT':
                        total_debits += Decimal(str(amount))
                    else:
                        total_credits += Decimal(str(amount))
                    
                    # Create segment assignments for this distribution line
                    for seg_data in segments_data:
                        segment_type_id = seg_data['segment_type']
                        segment_id = seg_data['segment']
                        
                        # Validate segment exists and is child type
                        try:
                            segment = XX_Segment.objects.get(id=segment_id)
                            segment_type = XX_SegmentType.objects.get(segment_id=segment_type_id)
                            
                            if segment.node_type != 'child':
                                raise serializers.ValidationError(
                                    f"Segment {segment_id} must be a child type, got: {segment.node_type}"
                                )
                            
                            if segment.segment_type_id != segment_type_id:
                                raise serializers.ValidationError(
                                    f"Segment {segment_id} does not belong to segment type {segment_type_id}"
                                )
                            
                            # Create segment assignment
                            ARInvoiceDistributionSegment.objects.create(
                                gl_line=gl_line,
                                segment_type=segment_type,
                                segment=segment
                            )
                            print(f"DEBUG: Created segment assignment: Type={segment_type.segment_name}, Segment={segment.alias}")
                            
                        except XX_Segment.DoesNotExist:
                            inv.delete()
                            raise serializers.ValidationError(f"Segment with ID {segment_id} does not exist")
                        except XX_SegmentType.DoesNotExist:
                            inv.delete()
                            raise serializers.ValidationError(f"Segment type with ID {segment_type_id} does not exist")
                    
                except KeyError as e:
                    inv.delete()
                    raise serializers.ValidationError(f"Distribution {idx+1} missing required field: {e}")
                except Exception as e:
                    inv.delete()
                    raise serializers.ValidationError(f"Error creating distribution {idx+1}: {str(e)}")
            
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
            
            print(f"DEBUG: Created {len(gl_lines_data)} distributions. Debits={total_debits}, Credits={total_credits}, Invoice Total={invoice_total}")
        
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

# Payment Distribution Serializers (Dynamic Segments)
class PaymentDistributionSegmentSerializer(serializers.Serializer):
    """Serializer for segment assignments in payment GL distributions"""
    segment_type = serializers.IntegerField(help_text="ID of the segment type")
    segment_type_name = serializers.CharField(read_only=True, help_text="Name of the segment type")
    segment = serializers.IntegerField(help_text="ID of the child segment")
    segment_code = serializers.CharField(read_only=True, help_text="Code of the segment")
    segment_name = serializers.CharField(read_only=True, help_text="Name of the segment")
    
    def validate_segment(self, value):
        try:
            segment = XX_Segment.objects.get(id=value)
            if segment.node_type != 'child':
                raise serializers.ValidationError(
                    f"Only child segments can be assigned. Segment '{segment.code}' is a '{segment.node_type}' type."
                )
            return value
        except XX_Segment.DoesNotExist:
            raise serializers.ValidationError(f"Segment with ID {value} does not exist")


class PaymentDistributionSerializer(serializers.Serializer):
    """Serializer for Payment GL Distribution Lines (NEW dynamic multi-segment model)"""
    id = serializers.IntegerField(required=False, read_only=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, help_text="Distribution amount")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Description")
    segments = PaymentDistributionSegmentSerializer(many=True, help_text="Segment assignments")
    
    def validate_segments(self, value):
        if not value:
            raise serializers.ValidationError("At least one segment must be provided")
        
        required_types = XX_SegmentType.objects.filter(is_required=True, is_active=True)
        provided_type_ids = {seg['segment_type'] for seg in value}
        required_type_ids = {st.segment_id for st in required_types}
        
        missing = required_type_ids - provided_type_ids
        if missing:
            missing_names = [st.segment_name for st in required_types if st.segment_id in missing]
            raise serializers.ValidationError(f"Missing required segment types: {', '.join(missing_names)}")
        
        for seg_data in value:
            segment_type_id = seg_data['segment_type']
            segment_id = seg_data['segment']
            try:
                segment = XX_Segment.objects.get(id=segment_id)
                if segment.segment_type_id != segment_type_id:
                    raise serializers.ValidationError(
                        f"Segment {segment.code} does not belong to segment type {segment_type_id}"
                    )
            except XX_Segment.DoesNotExist:
                raise serializers.ValidationError(f"Segment {segment_id} does not exist")
        
        return value
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


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
    distributions = PaymentDistributionSerializer(many=True, required=False)  # NEW: Dynamic multi-segment
    
    class Meta:
        model = ARPayment
        fields = ["id", "customer", "customer_name", "payment_date", "amount", "reference_number", 
                  "memo", "bank_account", "invoice", "status", "posted_at", "reconciled",
                  "invoice_currency", "invoice_currency_code", "exchange_rate", 
                  "currency", "payment_currency_code", "distributions"]
        extra_kwargs = {
            'invoice': {'write_only': False},
            'date': {'write_only': True}
        }
        read_only_fields = ['id', 'invoice_currency', 'exchange_rate']
    
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
        read_only_fields = ['id']

class APInvoiceGLLineSerializer(serializers.Serializer):
    """Serializer for AP Invoice GL Distribution Lines (DEPRECATED - Old single-segment model)
    
    This is the OLD structure with a single 'account' field.
    For NEW invoices using dynamic segments, use APInvoiceDistributionSerializer instead.
    """
    id = serializers.IntegerField(required=False)
    account = serializers.IntegerField(required=False)
    account_code = serializers.CharField(required=False, allow_blank=True)
    account_name = serializers.CharField(required=False, allow_blank=True)
    line_type = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class APInvoiceDistributionSegmentSerializer(serializers.Serializer):
    """Serializer for segment assignments in dynamic GL distributions"""
    segment_type = serializers.IntegerField(help_text="ID of the segment type (e.g., Account, Department, Cost Center)")
    segment_type_name = serializers.CharField(read_only=True, help_text="Name of the segment type")
    segment = serializers.IntegerField(help_text="ID of the child segment to assign")
    segment_code = serializers.CharField(read_only=True, help_text="Code of the assigned segment")
    segment_name = serializers.CharField(read_only=True, help_text="Name of the assigned segment")
    
    def to_representation(self, instance):
        """Convert model instance to dict for serialization"""
        from ap.models import APInvoiceDistributionSegment
        
        # If instance is a model object, extract the data
        if isinstance(instance, APInvoiceDistributionSegment):
            return {
                'segment_type': instance.segment_type.segment_id if instance.segment_type else None,
                'segment_type_name': instance.segment_type.segment_name if instance.segment_type else None,
                'segment': instance.segment.id if instance.segment else None,
                'segment_code': instance.segment.code if instance.segment else None,
                'segment_name': instance.segment.alias if instance.segment else None,  # Use 'alias' field
            }
        # Otherwise it's already a dict from create()
        return super().to_representation(instance)
    
    def validate_segment(self, value):
        """Validate that the segment exists and is a child segment"""
        try:
            segment = XX_Segment.objects.get(id=value)
            if segment.node_type != 'child':
                raise serializers.ValidationError(
                    f"Only child segments can be assigned. "
                    f"Segment '{segment.code}' is a '{segment.node_type}' type."
                )
            return value
        except XX_Segment.DoesNotExist:
            raise serializers.ValidationError(f"Segment with ID {value} does not exist")


class APInvoiceDistributionSerializer(serializers.Serializer):
    """Serializer for AP Invoice GL Distribution Lines (NEW dynamic multi-segment model)
    
    This is the NEW structure for dynamic segment system.
    Each distribution line can have multiple segment assignments (Account, Department, Cost Center, Project, etc.)
    
    Example:
    {
        "amount": "1000.00",
        "description": "Office supplies expense",
        "segments": [
            {"segment_type": 1, "segment": 101},  // Account: 5000-001 (Expenses)
            {"segment_type": 2, "segment": 201},  // Department: SALES
            {"segment_type": 3, "segment": 301}   // Cost Center: CC-001
        ]
    }
    """
    id = serializers.IntegerField(required=False, read_only=True)
    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text="Distribution amount"
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Description of this distribution line"
    )
    segments = APInvoiceDistributionSegmentSerializer(
        many=True,
        help_text="List of segment assignments (Account, Department, Cost Center, Project, etc.)"
    )
    
    def validate_segments(self, value):
        """Validate that all required segment types are provided"""
        if not value:
            raise serializers.ValidationError("At least one segment must be provided")
        
        # Get all required segment types
        required_types = XX_SegmentType.objects.filter(is_required=True, is_active=True)
        provided_type_ids = {seg['segment_type'] for seg in value}
        required_type_ids = {st.segment_id for st in required_types}
        
        missing = required_type_ids - provided_type_ids
        if missing:
            missing_names = [st.segment_name for st in required_types if st.segment_id in missing]
            raise serializers.ValidationError(
                f"Missing required segment types: {', '.join(missing_names)}"
            )
        
        # Validate that each segment belongs to its segment type
        for seg_data in value:
            segment_type_id = seg_data['segment_type']
            segment_id = seg_data['segment']
            
            try:
                segment = XX_Segment.objects.get(id=segment_id)
                if segment.segment_type_id != segment_type_id:
                    raise serializers.ValidationError(
                        f"Segment {segment.code} does not belong to segment type {segment_type_id}"
                    )
            except XX_Segment.DoesNotExist:
                raise serializers.ValidationError(f"Segment {segment_id} does not exist")
        
        return value
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def to_representation(self, instance):
        """Convert model instance to dict for serialization"""
        from ap.models import APInvoiceGLLine
        
        # If instance is a model object, extract the data
        if isinstance(instance, APInvoiceGLLine):
            return {
                'id': instance.id,
                'amount': str(instance.amount),
                'description': instance.description,
                'segments': APInvoiceDistributionSegmentSerializer(
                    instance.segments.all(),  # Use 'segments' related name
                    many=True
                ).data
            }
        # Otherwise it's already a dict from create()
        return super().to_representation(instance)

class APInvoiceSerializer(serializers.ModelSerializer):
    items = APItemSerializer(many=True)
    gl_lines = APInvoiceGLLineSerializer(many=True, required=False)  # OLD: Deprecated single-segment
    distributions = APInvoiceDistributionSerializer(many=True, required=False)  # NEW: Dynamic multi-segment
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
        fields = ["id","supplier","supplier_name","number","invoice_number","date","due_date","currency","currency_code","country","exchange_rate","base_currency_total","po_header","po_number","po_header_id","goods_receipt","grn_number","goods_receipt_id","three_way_match_status","match_variance_amount","match_variance_notes","match_performed_at","is_posted","payment_status","approval_status","is_cancelled","posted_at","paid_at","cancelled_at","items","gl_lines","distributions","totals","subtotal","tax_amount","total","paid_amount","balance"]
        read_only_fields = ['id', "is_posted","payment_status","is_cancelled","posted_at","paid_at","cancelled_at","exchange_rate","base_currency_total","three_way_match_status","match_variance_amount","match_variance_notes","match_performed_at","totals","subtotal","tax_amount","total","paid_amount","balance","supplier_name","currency_code","grn_number","po_number","goods_receipt_id","po_header_id"]

    
    def validate(self, attrs):
        print(f"DEBUG validate(): Received attrs keys: {attrs.keys()}")
        print(f"DEBUG validate(): Items count: {len(attrs.get('items', []))}")
        if 'items' in attrs:
            print(f"DEBUG validate(): Items data: {attrs['items']}")
        
        # Check if using new distribution format
        distributions = attrs.get('distributions', [])
        if distributions:
            print(f"DEBUG validate(): Using NEW dynamic segment distributions: {len(distributions)} lines")
        
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
        distributions_data = validated_data.pop("distributions", [])  # NEW: Dynamic multi-segment distributions
        print(f"DEBUG: Creating AP Invoice with {len(items_data)} items")
        print(f"DEBUG: Items data: {items_data}")
        if gl_lines_data:
            print(f"DEBUG: GL lines data (deprecated): {len(gl_lines_data)} lines")
        if distributions_data:
            print(f"DEBUG: Distributions data (NEW): {len(distributions_data)} lines")
        
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
        
        # CREATE GL DISTRIBUTION LINES
        if distributions_data:
            # NEW: User provided explicit distributions with dynamic segments
            print(f"DEBUG: Creating {len(distributions_data)} user-provided distributions with dynamic segments")
            from ap.models import APInvoiceGLLine, APInvoiceDistributionSegment
            from segment.models import XX_Segment, XX_SegmentType
            
            for idx, dist_data in enumerate(distributions_data):
                try:
                    amount = dist_data['amount']
                    description = dist_data.get('description', '')
                    segments_data = dist_data['segments']
                    
                    print(f"DEBUG: Creating distribution {idx+1}: Amount={amount}, Segments={len(segments_data)}")
                    
                    # Create the GL line (without account field for new dynamic model)
                    gl_line = APInvoiceGLLine.objects.create(
                        invoice=inv,
                        amount=amount,
                        description=description,
                        line_type='distribution'
                    )
                    print(f"DEBUG: Created GL line #{gl_line.id}")
                    
                    # Create segment assignments
                    for seg_data in segments_data:
                        segment_type_id = seg_data['segment_type']
                        segment_id = seg_data['segment']
                        
                        APInvoiceDistributionSegment.objects.create(
                            distribution=gl_line,
                            segment_type_id=segment_type_id,
                            segment_id=segment_id
                        )
                        print(f"DEBUG: Assigned segment type {segment_type_id}, segment {segment_id}")
                    
                    print(f"DEBUG: Distribution {idx+1} created successfully with {len(segments_data)} segments")
                except Exception as e:
                    print(f"DEBUG: ERROR creating distribution {idx+1}: {e}")
                    inv.delete()
                    raise serializers.ValidationError(f"Failed to create distribution {idx+1}: {str(e)}")
            
            print(f"DEBUG: All {len(distributions_data)} distributions created successfully")
            
        else:
            # AUTO-CREATE GL DISTRIBUTION LINES FROM ITEMS (OLD BEHAVIOR)
            try:
                # Get default expense account for distributions
                from segment.models import XX_Segment
                default_account = XX_Segment.objects.filter(
                    segment_type__segment_name='Account',
                    code__in=['5000-001', '5000', '6000-001'],  # Common expense accounts
                    node_type='child',
                    is_active=True
                ).first()
                
                if default_account:
                    print(f"DEBUG: Auto-creating distribution lines using account: {default_account.code}")
                    distributions = inv.create_distributions_from_items(default_account=default_account)
                    print(f"DEBUG: Created {len(distributions)} distribution lines")
                    
                    # Validate distributions
                    validation = inv.validate_distributions()
                    if validation['valid']:
                        print(f"DEBUG: Distribution validation passed ✓")
                    else:
                        print(f"DEBUG: Distribution validation warnings: {validation['errors']}")
                else:
                    print(f"DEBUG: WARNING - No default expense account found for distributions")
                    print(f"DEBUG: Invoice created without GL distributions - will need manual entry")
            except Exception as e:
                print(f"DEBUG: Error creating distributions (non-fatal): {e}")
                # Don't fail invoice creation if distribution creation fails
                # User can add distributions manually later
        
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
    distributions = PaymentDistributionSerializer(many=True, required=False)  # NEW: Dynamic multi-segment
    
    class Meta:
        model = APPayment
        fields = ["id", "supplier", "supplier_name", "payment_date", "amount", "reference_number", 
                  "memo", "bank_account", "invoice", "status", "posted_at", "reconciled",
                  "invoice_currency", "invoice_currency_code", "exchange_rate",
                  "currency", "payment_currency_code", "distributions"]
        extra_kwargs = {
            'invoice': {'write_only': False},
            'date': {'write_only': True}
        }
        read_only_fields = ['id', 'invoice_currency', 'exchange_rate']
    
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
        read_only_fields = ['id']


class JournalEntryReadSerializer(serializers.ModelSerializer):
    lines = JournalLineReadSerializer(many=True, read_only=True)
    class Meta:
        model = JournalEntry
        fields = ["id","date","currency","memo","posted","lines"]
        read_only_fields = ['id']


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id","name","account_code","iban","swift","currency","active"]
        read_only_fields = ['id']

class SeedVATRequestSerializer(serializers.Serializer):
    effective_from = serializers.DateField(required=False)

class CorpTaxAccrualRequestSerializer(serializers.Serializer):
    country = serializers.ChoiceField(choices=[("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")])
    date_from = serializers.DateField()
    date_to = serializers.DateField()


# ============================================================================
# REMOVED: Legacy Invoice Serializers
# ============================================================================
# The following serializers were for the deprecated finance.Invoice model
# which has been removed. Use ARInvoiceSerializer or APInvoiceSerializer instead.
#
# - InvoiceLineSerializer - REMOVED
# - InvoiceSerializer - REMOVED
# ============================================================================


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
        read_only_fields = ['id', 'created_at', 'updated_at']


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
        read_only_fields = ['id']


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

