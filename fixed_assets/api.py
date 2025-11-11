"""
Asset Management API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date

from .models import (
    AssetCategory, AssetLocation, Asset, AssetTransfer,
    DepreciationSchedule, AssetMaintenance, AssetDocument, AssetConfiguration,
    AssetRetirement, AssetAdjustment, AssetApproval
)
from .serializers import (
    AssetCategorySerializer, AssetLocationSerializer, AssetSerializer,
    AssetTransferSerializer, DepreciationScheduleSerializer,
    AssetMaintenanceSerializer, AssetDocumentSerializer, AssetListSerializer,
    AssetConfigurationSerializer, AssetRetirementSerializer, 
    AssetAdjustmentSerializer, AssetApprovalSerializer
)
from .services import AssetDepreciationService, AssetGLService


class AssetCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for asset categories"""
    queryset = AssetCategory.objects.all().order_by('code')
    serializer_class = AssetCategorySerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        # Only set created_by if user is authenticated
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class AssetLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for asset locations"""
    queryset = AssetLocation.objects.all().order_by('code')
    serializer_class = AssetLocationSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def assets(self, request, pk=None):
        """Get all assets at this location"""
        location = self.get_object()
        assets = Asset.objects.filter(location=location, status='ACTIVE')
        serializer = AssetListSerializer(assets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get child locations"""
        location = self.get_object()
        children = AssetLocation.objects.filter(parent_location=location, is_active=True)
        serializer = AssetLocationSerializer(children, many=True)
        return Response(serializer.data)


class AssetViewSet(viewsets.ModelViewSet):
    """ViewSet for assets"""
    queryset = Asset.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssetListSerializer
        return AssetSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location_id=location)
        
        return queryset
    
    def perform_create(self, serializer):
        # Only set created_by if user is authenticated
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def capitalize(self, request, pk=None):
        """Capitalize an asset"""
        asset = self.get_object()
        
        if asset.status != 'DRAFT':
            return Response(
                {'error': 'Only draft assets can be capitalized'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        capitalization_date = request.data.get('capitalization_date')
        if not capitalization_date:
            capitalization_date = timezone.now().date()
        
        try:
            with transaction.atomic():
                # Create journal entry for capitalization
                # DR Asset Account / CR AP or Clearing Account
                gl_service = AssetGLService()
                user = request.user if request.user.is_authenticated else None
                journal = gl_service.create_capitalization_journal(asset, user)
                
                asset.status = 'ACTIVE'
                asset.capitalization_date = capitalization_date
                if not asset.depreciation_start_date:
                    asset.depreciation_start_date = capitalization_date
                asset.save()
                
                # Generate depreciation schedule
                service = AssetDepreciationService()
                service.generate_depreciation_schedule(asset)
            
            serializer = AssetSerializer(asset)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Initiate asset transfer with approval workflow"""
        asset = self.get_object()
        
        to_location_id = request.data.get('to_location')
        reason = request.data.get('reason', '')
        transfer_date = request.data.get('transfer_date', timezone.now().date())
        
        if not to_location_id:
            return Response(
                {'error': 'to_location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            to_location = AssetLocation.objects.get(id=to_location_id)
        except AssetLocation.DoesNotExist:
            return Response(
                {'error': 'Location not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if asset.location == to_location:
            return Response(
                {'error': 'Asset is already at this location'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create transfer record
                transfer = AssetTransfer.objects.create(
                    asset=asset,
                    transfer_date=transfer_date,
                    from_location=asset.location,
                    to_location=to_location,
                    reason=reason,
                    requested_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    transfer=transfer,
                    operation_type='TRANSFER',
                    approval_status='PENDING',
                    notes=f'Transfer from {asset.location.name if asset.location else "None"} to {to_location.name}',
                    requested_by=request.user if request.user.is_authenticated else None
                )
        
            return Response({
                'message': 'Transfer request submitted for approval',
                'transfer_id': transfer.id,
                'approval_id': approval.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def dispose(self, request, pk=None):
        """Dispose of an asset"""
        asset = self.get_object()
        
        if asset.status not in ['ACTIVE', 'DRAFT']:
            return Response(
                {'error': 'Asset is already disposed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        disposal_date = request.data.get('disposal_date', timezone.now().date())
        disposal_method = request.data.get('disposal_method', 'SOLD')
        disposal_proceeds = request.data.get('disposal_proceeds', 0)
        disposal_notes = request.data.get('disposal_notes', '')
        
        try:
            with transaction.atomic():
                # Create journal entry for disposal
                # DR Accumulated Depreciation
                # DR Loss on Disposal (if loss) OR CR Gain on Disposal (if gain)
                # DR Cash/AR (proceeds)
                # CR Asset Account
                gl_service = AssetGLService()
                user = request.user if request.user.is_authenticated else None
                journal = gl_service.create_disposal_journal(
                    asset, 
                    disposal_date, 
                    Decimal(str(disposal_proceeds)),
                    user
                )
                
                asset.status = 'DISPOSED'
                asset.disposal_date = disposal_date
                asset.disposal_method = disposal_method
                asset.disposal_proceeds = disposal_proceeds
                asset.disposal_notes = disposal_notes
                asset.save()
            
            serializer = AssetSerializer(asset)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def depreciation_schedule(self, request, pk=None):
        """Get depreciation schedule for an asset"""
        asset = self.get_object()
        schedules = DepreciationSchedule.objects.filter(asset=asset).order_by('period_date')
        serializer = DepreciationScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """Get maintenance history for an asset"""
        asset = self.get_object()
        maintenance = AssetMaintenance.objects.filter(asset=asset).order_by('-maintenance_date')
        serializer = AssetMaintenanceSerializer(maintenance, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get documents for an asset"""
        asset = self.get_object()
        documents = AssetDocument.objects.filter(asset=asset).order_by('-document_date')
        serializer = AssetDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_for_capitalization(self, request, pk=None):
        """Submit CIP asset for capitalization approval"""
        asset = self.get_object()
        
        if asset.status != 'CIP':
            return Response(
                {'error': 'Only CIP assets can be submitted for capitalization'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        capitalization_date = request.data.get('capitalization_date', timezone.now().date())
        notes = request.data.get('notes', '')
        
        try:
            with transaction.atomic():
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    operation_type='CAPITALIZE',
                    approval_status='PENDING',
                    notes=notes,
                    requested_by=request.user if request.user.is_authenticated else None
                )
                
                # Store capitalization date in approval notes or separate field
                asset.notes = f"{asset.notes}\nCapitalization requested for {capitalization_date}"
                asset.save()
            
            return Response({
                'message': 'Asset submitted for capitalization approval',
                'approval_id': approval.id,
                'asset': AssetSerializer(asset).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def recategorize(self, request, pk=None):
        """Submit asset recategorization request"""
        asset = self.get_object()
        
        new_category_id = request.data.get('new_category')
        reason = request.data.get('reason', '')
        
        if not new_category_id:
            return Response(
                {'error': 'new_category is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_category = AssetCategory.objects.get(id=new_category_id)
        except AssetCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if asset.category == new_category:
            return Response(
                {'error': 'Asset is already in this category'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create adjustment record
                adjustment = AssetAdjustment.objects.create(
                    asset=asset,
                    adjustment_type='RECATEGORIZE',
                    adjustment_date=timezone.now().date(),
                    old_value=str(asset.category.id) if asset.category else None,
                    new_value=str(new_category_id),
                    reason=reason,
                    adjusted_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    adjustment=adjustment,
                    operation_type='ADJUST',
                    approval_status='PENDING',
                    notes=f'Recategorize from {asset.category.name if asset.category else "None"} to {new_category.name}',
                    requested_by=request.user if request.user.is_authenticated else None
                )
            
            return Response({
                'message': 'Recategorization request submitted for approval',
                'adjustment_id': adjustment.id,
                'approval_id': approval.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def adjust_cost(self, request, pk=None):
        """Submit asset cost adjustment request"""
        asset = self.get_object()
        
        new_cost = request.data.get('new_cost')
        reason = request.data.get('reason', '')
        
        if not new_cost:
            return Response(
                {'error': 'new_cost is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_cost = Decimal(str(new_cost))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid cost amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create adjustment record
                adjustment = AssetAdjustment.objects.create(
                    asset=asset,
                    adjustment_type='COST',
                    adjustment_date=timezone.now().date(),
                    old_value=str(asset.acquisition_cost),
                    new_value=str(new_cost),
                    reason=reason,
                    adjusted_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    adjustment=adjustment,
                    operation_type='ADJUST',
                    approval_status='PENDING',
                    notes=f'Cost adjustment from {asset.acquisition_cost} to {new_cost}',
                    requested_by=request.user if request.user.is_authenticated else None
                )
            
            return Response({
                'message': 'Cost adjustment request submitted for approval',
                'adjustment_id': adjustment.id,
                'approval_id': approval.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def adjust_useful_life(self, request, pk=None):
        """Submit useful life adjustment request"""
        asset = self.get_object()
        
        new_useful_life = request.data.get('new_useful_life')
        reason = request.data.get('reason', '')
        
        if not new_useful_life:
            return Response(
                {'error': 'new_useful_life is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_useful_life = int(new_useful_life)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid useful life value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create adjustment record
                adjustment = AssetAdjustment.objects.create(
                    asset=asset,
                    adjustment_type='USEFUL_LIFE',
                    adjustment_date=timezone.now().date(),
                    old_value=str(asset.useful_life_months),
                    new_value=str(new_useful_life),
                    reason=reason,
                    adjusted_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    adjustment=adjustment,
                    operation_type='ADJUST',
                    approval_status='PENDING',
                    notes=f'Useful life adjustment from {asset.useful_life_months} to {new_useful_life} months',
                    requested_by=request.user if request.user.is_authenticated else None
                )
            
            return Response({
                'message': 'Useful life adjustment request submitted for approval',
                'adjustment_id': adjustment.id,
                'approval_id': approval.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def manual_depreciation_adjustment(self, request, pk=None):
        """Submit manual depreciation adjustment request"""
        asset = self.get_object()
        
        new_accumulated_depreciation = request.data.get('new_accumulated_depreciation')
        reason = request.data.get('reason', '')
        
        if not new_accumulated_depreciation:
            return Response(
                {'error': 'new_accumulated_depreciation is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_accumulated_depreciation = Decimal(str(new_accumulated_depreciation))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid depreciation amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create adjustment record
                adjustment = AssetAdjustment.objects.create(
                    asset=asset,
                    adjustment_type='DEPRECIATION',
                    adjustment_date=timezone.now().date(),
                    old_value=str(asset.accumulated_depreciation),
                    new_value=str(new_accumulated_depreciation),
                    reason=reason,
                    adjusted_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    adjustment=adjustment,
                    operation_type='ADJUST',
                    approval_status='PENDING',
                    notes=f'Manual depreciation adjustment from {asset.accumulated_depreciation} to {new_accumulated_depreciation}',
                    requested_by=request.user if request.user.is_authenticated else None
                )
            
            return Response({
                'message': 'Depreciation adjustment request submitted for approval',
                'adjustment_id': adjustment.id,
                'approval_id': approval.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def submit_for_retirement(self, request, pk=None):
        """Submit asset for retirement approval"""
        asset = self.get_object()
        
        if asset.status != 'CAPITALIZED':
            return Response(
                {'error': 'Only capitalized assets can be submitted for retirement'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        retirement_date = request.data.get('retirement_date', timezone.now().date())
        retirement_type = request.data.get('retirement_type', 'SOLD')
        disposal_proceeds = request.data.get('disposal_proceeds', 0)
        disposal_costs = request.data.get('disposal_costs', 0)
        buyer_recipient = request.data.get('buyer_recipient', '')
        sale_invoice_number = request.data.get('sale_invoice_number', '')
        reason = request.data.get('reason', '')
        
        try:
            with transaction.atomic():
                # Create retirement record
                retirement = AssetRetirement.objects.create(
                    asset=asset,
                    retirement_date=retirement_date,
                    retirement_type=retirement_type,
                    net_book_value_at_retirement=asset.net_book_value,
                    disposal_proceeds=disposal_proceeds,
                    disposal_costs=disposal_costs,
                    buyer_recipient=buyer_recipient,
                    sale_invoice_number=sale_invoice_number,
                    reason=reason,
                    submitted_by=request.user if request.user.is_authenticated else None,
                    approval_status='PENDING'
                )
                
                # Create approval request
                approval = AssetApproval.objects.create(
                    asset=asset,
                    retirement=retirement,
                    operation_type='RETIRE',
                    approval_status='PENDING',
                    notes=f'Retirement request - {retirement_type}',
                    requested_by=request.user if request.user.is_authenticated else None
                )
            
            return Response({
                'message': 'Asset submitted for retirement approval',
                'retirement_id': retirement.id,
                'approval_id': approval.id,
                'estimated_gain_loss': retirement.gain_loss
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def check_source_conversion(self, request):
        """
        Check if a source (AP Invoice line or GRN line) can be converted to an asset.
        POST data: {
            "source_type": "AP_INVOICE" or "GRN",
            "ap_invoice_id": 123,  # if AP_INVOICE
            "ap_invoice_line": 1,  # if AP_INVOICE
            "grn_line_id": 456     # if GRN
        }
        """
        source_type = request.data.get('source_type')
        ap_invoice_id = request.data.get('ap_invoice_id')
        ap_invoice_line = request.data.get('ap_invoice_line')
        grn_line_id = request.data.get('grn_line_id')
        
        result = Asset.check_source_already_converted(
            source_type=source_type,
            ap_invoice_id=ap_invoice_id,
            ap_invoice_line=ap_invoice_line,
            grn_line_id=grn_line_id
        )
        
        if result['exists']:
            return Response({
                'can_convert': False,
                'already_converted': True,
                'asset_id': result['asset'].id,
                'asset_number': result['asset'].asset_number,
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'can_convert': True,
                'already_converted': False,
                'message': 'Source can be converted to asset'
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def create_from_ap_invoice(self, request):
        """
        Create asset from AP Invoice line.
        POST data: {
            "ap_invoice_id": 123,
            "line_number": 1,
            "asset_data": {
                "asset_number": "ASSET-001",
                "name": "Laptop",
                "category": 1,
                "location": 1,
                ... other asset fields
            }
        }
        """
        from ap.models import APInvoice
        
        ap_invoice_id = request.data.get('ap_invoice_id')
        line_number = request.data.get('line_number')
        asset_data = request.data.get('asset_data', {})
        
        # Validate invoice exists
        try:
            ap_invoice = APInvoice.objects.get(id=ap_invoice_id)
        except APInvoice.DoesNotExist:
            return Response({'error': 'AP Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already converted
        check_result = Asset.check_source_already_converted(
            source_type='AP_INVOICE',
            ap_invoice_id=ap_invoice_id,
            ap_invoice_line=line_number
        )
        
        if check_result['exists']:
            return Response({
                'error': check_result['message'],
                'existing_asset': {
                    'id': check_result['asset'].id,
                    'asset_number': check_result['asset'].asset_number
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add source tracking to asset data
        asset_data['source_type'] = 'AP_INVOICE'
        asset_data['ap_invoice'] = ap_invoice_id
        asset_data['ap_invoice_line'] = line_number
        asset_data['supplier'] = ap_invoice.supplier.id
        asset_data['currency'] = ap_invoice.currency.id
        
        # Create the asset
        serializer = AssetSerializer(data=asset_data)
        if serializer.is_valid():
            if request.user and request.user.is_authenticated:
                serializer.save(created_by=request.user)
            else:
                serializer.save()
            
            return Response({
                'message': 'Asset created successfully from AP Invoice',
                'asset': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_from_grn(self, request):
        """
        Create asset from GRN line.
        POST data: {
            "grn_line_id": 456,
            "asset_data": {
                "asset_number": "ASSET-002",
                "name": "Equipment",
                "category": 2,
                "location": 1,
                ... other asset fields
            }
        }
        """
        from receiving.models import GRNLine
        
        grn_line_id = request.data.get('grn_line_id')
        asset_data = request.data.get('asset_data', {})
        
        # Validate GRN line exists
        try:
            grn_line = GRNLine.objects.select_related('goods_receipt').get(id=grn_line_id)
        except GRNLine.DoesNotExist:
            return Response({'error': 'GRN Line not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already converted
        check_result = Asset.check_source_already_converted(
            source_type='GRN',
            grn_line_id=grn_line_id
        )
        
        if check_result['exists']:
            return Response({
                'error': check_result['message'],
                'existing_asset': {
                    'id': check_result['asset'].id,
                    'asset_number': check_result['asset'].asset_number
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add source tracking to asset data
        asset_data['source_type'] = 'GRN'
        asset_data['grn'] = grn_line.goods_receipt.id
        asset_data['grn_line'] = grn_line_id
        
        # Try to get supplier from GRN if available
        if hasattr(grn_line.goods_receipt, 'supplier') and grn_line.goods_receipt.supplier:
            asset_data['supplier'] = grn_line.goods_receipt.supplier.id
        
        # Create the asset
        serializer = AssetSerializer(data=asset_data)
        if serializer.is_valid():
            if request.user and request.user.is_authenticated:
                serializer.save(created_by=request.user)
            else:
                serializer.save()
            
            return Response({
                'message': 'Asset created successfully from GRN',
                'asset': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetTransferViewSet(viewsets.ModelViewSet):
    """ViewSet for asset transfers"""
    queryset = AssetTransfer.objects.all().order_by('-created_at')
    serializer_class = AssetTransferSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by approval status
        approval_status = self.request.query_params.get('approval_status', None)
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset', None)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset
    
    def perform_create(self, serializer):
        # Only set requested_by if user is authenticated
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(requested_by=self.request.user, approval_status='PENDING')
        else:
            serializer.save(approval_status='PENDING')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve and complete a transfer"""
        transfer = self.get_object()
        
        if transfer.approval_status == 'APPROVED':
            return Response(
                {'error': 'Transfer is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transfer.approval_status == 'REJECTED':
            return Response(
                {'error': 'Transfer has been rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update asset location
                asset = transfer.asset
                asset.location = transfer.to_location
                asset.save()
                
                # Mark transfer as approved and completed
                transfer.approval_status = 'APPROVED'
                if request.user and request.user.is_authenticated:
                    transfer.approved_by = request.user
                transfer.approved_at = timezone.now()
                transfer.is_completed = True
                transfer.completed_at = timezone.now()
                transfer.save()
                
                # Update associated approval record if exists
                try:
                    approval = AssetApproval.objects.get(transfer=transfer)
                    approval.approval_status = 'APPROVED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetTransferSerializer(transfer)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a transfer"""
        transfer = self.get_object()
        
        if transfer.approval_status == 'APPROVED':
            return Response(
                {'error': 'Cannot reject an approved transfer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transfer.approval_status == 'REJECTED':
            return Response(
                {'error': 'Transfer is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            with transaction.atomic():
                # Mark transfer as rejected
                transfer.approval_status = 'REJECTED'
                transfer.notes = f"{transfer.notes}\nRejection reason: {rejection_reason}" if transfer.notes else f"Rejection reason: {rejection_reason}"
                transfer.save()
                
                # Update associated approval record if exists
                try:
                    approval = AssetApproval.objects.get(transfer=transfer)
                    approval.approval_status = 'REJECTED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.rejection_reason = rejection_reason
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetTransferSerializer(transfer)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DepreciationScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for depreciation schedules"""
    queryset = DepreciationSchedule.objects.all().order_by('-period_date')
    serializer_class = DepreciationScheduleSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by posted status
        is_posted = self.request.query_params.get('is_posted', None)
        if is_posted is not None:
            queryset = queryset.filter(is_posted=is_posted.lower() == 'true')
        
        # Filter by period
        period = self.request.query_params.get('period', None)
        if period:
            queryset = queryset.filter(period_date=period)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset', None)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def calculate_monthly(self, request):
        """Calculate depreciation for all assets for a given month"""
        period_date = request.data.get('period_date')
        
        if not period_date:
            return Response(
                {'error': 'period_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = AssetDepreciationService()
            schedules = service.calculate_monthly_depreciation(period_date)
            
            serializer = DepreciationScheduleSerializer(schedules, many=True)
            return Response({
                'count': len(schedules),
                'period_date': period_date,
                'schedules': serializer.data
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def post_monthly(self, request):
        """Post monthly depreciation entries"""
        period_date = request.data.get('period_date')
        
        if not period_date:
            return Response(
                {'error': 'period_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = AssetDepreciationService()
            result = service.post_monthly_depreciation(period_date, request.user)
            
            return Response(result)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AssetMaintenanceViewSet(viewsets.ModelViewSet):
    """ViewSet for asset maintenance"""
    queryset = AssetMaintenance.objects.all().order_by('-maintenance_date')
    serializer_class = AssetMaintenanceSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        # Only set performed_by if user is authenticated
        if self.request.user and self.request.user.is_authenticated:
            maintenance = serializer.save(performed_by=self.request.user)
        else:
            maintenance = serializer.save()
        
        # If capitalized, update asset cost
        if maintenance.is_capitalized and maintenance.cost:
            asset = maintenance.asset
            asset.acquisition_cost += maintenance.cost
            asset.update_net_book_value()
            asset.save()


class AssetDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for asset documents"""
    queryset = AssetDocument.objects.all().order_by('-created_at')
    serializer_class = AssetDocumentSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        # Only set uploaded_by if user is authenticated
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(uploaded_by=self.request.user)
        else:
            serializer.save()


class AssetConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for asset configuration (singleton)"""
    queryset = AssetConfiguration.objects.all()
    serializer_class = AssetConfigurationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'put', 'patch']  # No POST or DELETE for singleton
    
    def get_object(self):
        """Always return the singleton configuration"""
        return AssetConfiguration.get_config()
    
    def list(self, request, *args, **kwargs):
        """Return the singleton configuration as a single object"""
        config = AssetConfiguration.get_config()
        serializer = self.get_serializer(config)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        """Track who updated the configuration"""
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['post'])
    def check_threshold(self, request):
        """
        Check if an amount meets the capitalization threshold
        POST data: {
            "amount": 500.00,
            "currency_id": 2  # Currency ID of the amount
        }
        Returns: {
            "meets_threshold": false,
            "amount_in_base_currency": 450.00,
            "threshold_amount": 1000.00,
            "base_currency": "USD",
            "exchange_rate": 0.9
        }
        """
        from core.models import Currency, ExchangeRate
        from decimal import Decimal
        
        amount = Decimal(str(request.data.get('amount', 0)))
        currency_id = request.data.get('currency_id')
        
        config = AssetConfiguration.get_config()
        threshold = config.minimum_capitalization_amount
        
        # If no base currency configured, use threshold directly
        if not config.base_currency:
            return Response({
                'meets_threshold': amount >= threshold,
                'amount_in_base_currency': str(amount),
                'threshold_amount': str(threshold),
                'base_currency': None,
                'exchange_rate': 1.0,
                'warning_message': 'No base currency configured for threshold comparison'
            })
        
        # Convert amount to base currency
        try:
            from_currency = Currency.objects.get(id=currency_id)
            to_currency = config.base_currency
            
            if from_currency == to_currency:
                # Same currency, no conversion needed
                amount_in_base = amount
                rate = Decimal('1.0')
            else:
                # Get exchange rate
                try:
                    exchange_rate = ExchangeRate.objects.filter(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        is_active=True
                    ).latest('effective_date')
                    rate = exchange_rate.rate
                    amount_in_base = amount * rate
                except ExchangeRate.DoesNotExist:
                    # Try reverse rate
                    try:
                        exchange_rate = ExchangeRate.objects.filter(
                            from_currency=to_currency,
                            to_currency=from_currency,
                            is_active=True
                        ).latest('effective_date')
                        rate = Decimal('1.0') / exchange_rate.rate
                        amount_in_base = amount * rate
                    except ExchangeRate.DoesNotExist:
                        return Response({
                            'error': f'No exchange rate found between {from_currency.code} and {to_currency.code}'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            meets_threshold = amount_in_base >= threshold
            
            return Response({
                'meets_threshold': meets_threshold,
                'amount_in_base_currency': str(amount_in_base.quantize(Decimal('0.01'))),
                'threshold_amount': str(threshold),
                'base_currency': to_currency.code,
                'exchange_rate': str(rate),
                'from_currency': from_currency.code,
                'warning_message': None if meets_threshold else 
                    f'Amount ({from_currency.code} {amount}) converts to {to_currency.code} {amount_in_base.quantize(Decimal("0.01"))}, which is below the threshold of {to_currency.code} {threshold}'
            })
            
        except Currency.DoesNotExist:
            return Response({
                'error': 'Invalid currency ID'
            }, status=status.HTTP_400_BAD_REQUEST)


class AssetRetirementViewSet(viewsets.ModelViewSet):
    """ViewSet for asset retirements"""
    queryset = AssetRetirement.objects.all().order_by('-created_at')
    serializer_class = AssetRetirementSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by approval status
        approval_status = self.request.query_params.get('approval_status', None)
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        
        # Filter by retirement type
        retirement_type = self.request.query_params.get('retirement_type', None)
        if retirement_type:
            queryset = queryset.filter(retirement_type=retirement_type)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset', None)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset
    
    def perform_create(self, serializer):
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(submitted_by=self.request.user, approval_status='PENDING')
        else:
            serializer.save(approval_status='PENDING')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve retirement and update asset status"""
        retirement = self.get_object()
        
        if retirement.approval_status == 'APPROVED':
            return Response(
                {'error': 'Retirement is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if retirement.approval_status == 'REJECTED':
            return Response(
                {'error': 'Retirement has been rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update asset status
                asset = retirement.asset
                asset.status = 'RETIRED'
                asset.save()
                
                # Update retirement record
                retirement.approval_status = 'APPROVED'
                if request.user and request.user.is_authenticated:
                    retirement.approved_by = request.user
                retirement.approved_at = timezone.now()
                retirement.save()
                
                # Create GL journal entry for retirement
                if not retirement.is_posted:
                    gl_service = AssetGLService()
                    user = request.user if request.user.is_authenticated else None
                    journal = gl_service.create_retirement_journal(retirement, user)
                    retirement.journal_entry = journal
                    retirement.is_posted = True
                    retirement.save()
                
                # Update associated approval record
                try:
                    approval = AssetApproval.objects.get(retirement=retirement)
                    approval.approval_status = 'APPROVED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetRetirementSerializer(retirement)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject retirement"""
        retirement = self.get_object()
        
        if retirement.approval_status == 'APPROVED':
            return Response(
                {'error': 'Cannot reject an approved retirement'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if retirement.approval_status == 'REJECTED':
            return Response(
                {'error': 'Retirement is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            with transaction.atomic():
                retirement.approval_status = 'REJECTED'
                retirement.notes = f"{retirement.notes}\nRejection reason: {rejection_reason}" if retirement.notes else f"Rejection reason: {rejection_reason}"
                retirement.save()
                
                # Update associated approval record
                try:
                    approval = AssetApproval.objects.get(retirement=retirement)
                    approval.approval_status = 'REJECTED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.rejection_reason = rejection_reason
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetRetirementSerializer(retirement)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AssetAdjustmentViewSet(viewsets.ModelViewSet):
    """ViewSet for asset adjustments"""
    queryset = AssetAdjustment.objects.all().order_by('-created_at')
    serializer_class = AssetAdjustmentSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by approval status
        approval_status = self.request.query_params.get('approval_status', None)
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        
        # Filter by adjustment type
        adjustment_type = self.request.query_params.get('adjustment_type', None)
        if adjustment_type:
            queryset = queryset.filter(adjustment_type=adjustment_type)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset', None)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset
    
    def perform_create(self, serializer):
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(adjusted_by=self.request.user, approval_status='PENDING')
        else:
            serializer.save(approval_status='PENDING')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve adjustment and apply changes"""
        adjustment = self.get_object()
        
        if adjustment.approval_status == 'APPROVED':
            return Response(
                {'error': 'Adjustment is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if adjustment.approval_status == 'REJECTED':
            return Response(
                {'error': 'Adjustment has been rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                asset = adjustment.asset
                
                # Apply adjustment based on type
                if adjustment.adjustment_type == 'COST':
                    asset.acquisition_cost = Decimal(adjustment.new_value)
                    asset.update_net_book_value()
                elif adjustment.adjustment_type == 'USEFUL_LIFE':
                    asset.useful_life_months = int(adjustment.new_value)
                    # Regenerate depreciation schedule
                    service = AssetDepreciationService()
                    service.generate_depreciation_schedule(asset)
                elif adjustment.adjustment_type == 'DEPRECIATION':
                    asset.accumulated_depreciation = Decimal(adjustment.new_value)
                    asset.update_net_book_value()
                elif adjustment.adjustment_type == 'RECATEGORIZE':
                    new_category = AssetCategory.objects.get(id=int(adjustment.new_value))
                    asset.category = new_category
                
                asset.save()
                
                # Update adjustment record
                adjustment.approval_status = 'APPROVED'
                if request.user and request.user.is_authenticated:
                    adjustment.approved_by = request.user
                adjustment.approved_at = timezone.now()
                adjustment.save()
                
                # Update associated approval record
                try:
                    approval = AssetApproval.objects.get(adjustment=adjustment)
                    approval.approval_status = 'APPROVED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetAdjustmentSerializer(adjustment)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject adjustment"""
        adjustment = self.get_object()
        
        if adjustment.approval_status == 'APPROVED':
            return Response(
                {'error': 'Cannot reject an approved adjustment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if adjustment.approval_status == 'REJECTED':
            return Response(
                {'error': 'Adjustment is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            with transaction.atomic():
                adjustment.approval_status = 'REJECTED'
                adjustment.reason = f"{adjustment.reason}\nRejection reason: {rejection_reason}" if adjustment.reason else f"Rejection reason: {rejection_reason}"
                adjustment.save()
                
                # Update associated approval record
                try:
                    approval = AssetApproval.objects.get(adjustment=adjustment)
                    approval.approval_status = 'REJECTED'
                    if request.user and request.user.is_authenticated:
                        approval.approved_by = request.user
                    approval.approved_at = timezone.now()
                    approval.rejection_reason = rejection_reason
                    approval.save()
                except AssetApproval.DoesNotExist:
                    pass
            
            serializer = AssetAdjustmentSerializer(adjustment)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AssetApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for asset approvals (read-only list, approve/reject via actions)"""
    queryset = AssetApproval.objects.all().order_by('-created_at')
    serializer_class = AssetApprovalSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by approval status
        approval_status = self.request.query_params.get('approval_status', None)
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        
        # Filter by operation type
        operation_type = self.request.query_params.get('operation_type', None)
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset', None)
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        # Filter pending approvals
        pending_only = self.request.query_params.get('pending_only', None)
        if pending_only and pending_only.lower() == 'true':
            queryset = queryset.filter(approval_status='PENDING')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an operation"""
        approval = self.get_object()
        
        if approval.approval_status == 'APPROVED':
            return Response(
                {'error': 'Approval is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if approval.approval_status == 'REJECTED':
            return Response(
                {'error': 'Approval has been rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Route to appropriate approval handler
            if approval.operation_type == 'CAPITALIZE':
                return self._approve_capitalization(approval, request.user)
            elif approval.operation_type == 'RETIRE' and approval.retirement:
                # Use retirement viewset approve method
                viewset = AssetRetirementViewSet()
                viewset.request = request
                return viewset.approve(request, approval.retirement.id)
            elif approval.operation_type == 'ADJUST' and approval.adjustment:
                # Use adjustment viewset approve method
                viewset = AssetAdjustmentViewSet()
                viewset.request = request
                return viewset.approve(request, approval.adjustment.id)
            elif approval.operation_type == 'TRANSFER' and approval.transfer:
                # Use transfer viewset approve method
                viewset = AssetTransferViewSet()
                viewset.request = request
                return viewset.approve(request, approval.transfer.id)
            else:
                return Response(
                    {'error': 'Invalid operation type or missing related object'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _approve_capitalization(self, approval, user):
        """Handle capitalization approval"""
        try:
            with transaction.atomic():
                asset = approval.asset
                
                if asset.status != 'CIP':
                    return Response(
                        {'error': 'Only CIP assets can be capitalized'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                capitalization_date = timezone.now().date()
                
                # Create GL journal entry
                gl_service = AssetGLService()
                journal = gl_service.create_capitalization_journal(asset, user if user.is_authenticated else None)
                
                # Update asset
                asset.status = 'CAPITALIZED'
                asset.capitalization_date = capitalization_date
                if not asset.depreciation_start_date:
                    asset.depreciation_start_date = capitalization_date
                asset.save()
                
                # Generate depreciation schedule
                service = AssetDepreciationService()
                service.generate_depreciation_schedule(asset)
                
                # Update approval
                approval.approval_status = 'APPROVED'
                if user and user.is_authenticated:
                    approval.approved_by = user
                approval.approved_at = timezone.now()
                approval.save()
            
            return Response({
                'message': 'Asset capitalized successfully',
                'asset': AssetSerializer(asset).data
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an operation"""
        approval = self.get_object()
        
        if approval.approval_status == 'APPROVED':
            return Response(
                {'error': 'Cannot reject an approved operation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if approval.approval_status == 'REJECTED':
            return Response(
                {'error': 'Approval is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            with transaction.atomic():
                # Update approval
                approval.approval_status = 'REJECTED'
                if request.user and request.user.is_authenticated:
                    approval.approved_by = request.user
                approval.approved_at = timezone.now()
                approval.rejection_reason = rejection_reason
                approval.save()
                
                # Update related record
                if approval.retirement:
                    approval.retirement.approval_status = 'REJECTED'
                    approval.retirement.notes = f"{approval.retirement.notes}\nRejection: {rejection_reason}" if approval.retirement.notes else f"Rejection: {rejection_reason}"
                    approval.retirement.save()
                elif approval.adjustment:
                    approval.adjustment.approval_status = 'REJECTED'
                    approval.adjustment.reason = f"{approval.adjustment.reason}\nRejection: {rejection_reason}" if approval.adjustment.reason else f"Rejection: {rejection_reason}"
                    approval.adjustment.save()
                elif approval.transfer:
                    approval.transfer.approval_status = 'REJECTED'
                    approval.transfer.notes = f"{approval.transfer.notes}\nRejection: {rejection_reason}" if approval.transfer.notes else f"Rejection: {rejection_reason}"
                    approval.transfer.save()
            
            serializer = AssetApprovalSerializer(approval)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
