# procurement/api.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from decimal import Decimal

from .models import (
    RFxEvent, RFxItem, SupplierInvitation, SupplierQuote, SupplierQuoteLine,
    RFxAward, RFxAwardLine, AuctionBid
)
from .serializers import (
    RFxEventListSerializer, RFxEventDetailSerializer, RFxEventCreateUpdateSerializer,
    RFxItemSerializer, SupplierInvitationSerializer, SupplierQuoteSerializer,
    SupplierQuoteLineSerializer, RFxAwardSerializer, RFxAwardLineSerializer,
    AuctionBidSerializer, QuoteComparisonSerializer
)


class RFxEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RFx Events (RFQ/RFP/RFI/ITB)
    
    Provides CRUD operations and additional actions for:
    - Publishing events to suppliers
    - Closing events
    - Inviting suppliers
    - Quote comparison
    - Awarding to suppliers
    """
    queryset = RFxEvent.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'event_type': ['exact', 'in'],
        'status': ['exact', 'in'],
        'is_auction': ['exact'],
        'is_confidential': ['exact'],
        'category': ['exact'],
        'department': ['exact'],
        'submission_due_date': ['gte', 'lte'],
        'created_at': ['gte', 'lte'],
    }
    search_fields = ['rfx_number', 'title', 'description', 'category', 'department']
    ordering_fields = ['rfx_number', 'title', 'submission_due_date', 'created_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return RFxEventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RFxEventCreateUpdateSerializer
        return RFxEventDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating an RFx event"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish the RFx event to invited suppliers"""
        rfx_event = self.get_object()
        
        if rfx_event.publish(request.user):
            return Response({
                'status': 'success',
                'message': f'RFx {rfx_event.rfx_number} published successfully'
            })
        return Response(
            {'error': 'RFx cannot be published (must be in DRAFT status)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close the RFx event"""
        rfx_event = self.get_object()
        
        if rfx_event.close():
            return Response({
                'status': 'success',
                'message': f'RFx {rfx_event.rfx_number} closed successfully'
            })
        return Response(
            {'error': 'RFx cannot be closed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def invite_suppliers(self, request, pk=None):
        """Invite suppliers to participate in RFx"""
        rfx_event = self.get_object()
        supplier_ids = request.data.get('supplier_ids', [])
        message = request.data.get('message', '')
        
        if not supplier_ids:
            return Response(
                {'error': 'No suppliers specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from ap.models import Supplier
        invited_count = 0
        errors = []
        
        for supplier_id in supplier_ids:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
                
                # Check if already invited
                if SupplierInvitation.objects.filter(
                    rfx_event=rfx_event,
                    supplier=supplier
                ).exists():
                    errors.append(f'{supplier.name} already invited')
                    continue
                
                invitation = SupplierInvitation.objects.create(
                    rfx_event=rfx_event,
                    supplier=supplier,
                    invitation_message=message,
                    invited_by=request.user
                )
                invitation.mark_as_sent()
                invited_count += 1
                
            except Supplier.DoesNotExist:
                errors.append(f'Supplier ID {supplier_id} not found')
        
        return Response({
            'status': 'success',
            'invited_count': invited_count,
            'errors': errors
        })
    
    @action(detail=True, methods=['get'])
    def quote_comparison(self, request, pk=None):
        """Get side-by-side comparison of all quotes"""
        rfx_event = self.get_object()
        
        # Get all items
        items = RFxItem.objects.filter(rfx_event=rfx_event).order_by('line_number')
        
        # Get all submitted quotes
        quotes = SupplierQuote.objects.filter(
            rfx_event=rfx_event,
            status='SUBMITTED'
        ).select_related('supplier', 'currency')
        
        # Build comparison matrix
        comparison_matrix = {}
        
        for item in items:
            item_data = {
                'item_id': item.id,
                'line_number': item.line_number,
                'description': item.description,
                'quantity': str(item.quantity),
                'quotes': {}
            }
            
            for quote in quotes:
                try:
                    quote_line = SupplierQuoteLine.objects.get(
                        quote=quote,
                        rfx_item=item,
                        is_quoted=True
                    )
                    item_data['quotes'][quote.supplier.name] = {
                        'quote_id': quote.id,
                        'unit_price': str(quote_line.unit_price),
                        'line_total': str(quote_line.get_line_total()),
                        'delivery_days': quote_line.delivery_lead_time_days,
                        'meets_specs': quote_line.meets_specifications,
                        'brand': quote_line.brand_offered,
                    }
                except SupplierQuoteLine.DoesNotExist:
                    item_data['quotes'][quote.supplier.name] = {
                        'quoted': False
                    }
            
            comparison_matrix[f'line_{item.line_number}'] = item_data
        
        # Identify best quotes
        best_price = quotes.order_by('total_amount').first()
        best_technical = quotes.order_by('-technical_score').first()
        best_overall = quotes.order_by('-overall_score').first()
        
        result = {
            'rfx_event_id': rfx_event.id,
            'rfx_number': rfx_event.rfx_number,
            'rfx_title': rfx_event.title,
            'item_count': items.count(),
            'quote_count': quotes.count(),
            'items': RFxItemSerializer(items, many=True).data,
            'quotes': SupplierQuoteSerializer(quotes, many=True).data,
            'comparison_matrix': comparison_matrix,
            'best_price_supplier': best_price.supplier.name if best_price else None,
            'best_technical_supplier': best_technical.supplier.name if best_technical else None,
            'best_overall_supplier': best_overall.supplier.name if best_overall else None,
        }
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def create_award(self, request, pk=None):
        """Create award decision for RFx event"""
        rfx_event = self.get_object()
        
        award_data = request.data.get('awards', [])
        if not award_data:
            return Response(
                {'error': 'No award data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_awards = []
        
        for award_info in award_data:
            supplier_id = award_info.get('supplier_id')
            quote_id = award_info.get('quote_id')
            justification = award_info.get('justification', '')
            line_items = award_info.get('line_items', [])
            
            from ap.models import Supplier
            supplier = Supplier.objects.get(id=supplier_id)
            quote = SupplierQuote.objects.get(id=quote_id) if quote_id else None
            
            # Generate award number
            award_number = f"AWD-{rfx_event.rfx_number}-{supplier.code}"
            
            # Calculate award amount
            award_amount = Decimal('0.00')
            for line_item in line_items:
                qty = Decimal(str(line_item['quantity']))
                price = Decimal(str(line_item['unit_price']))
                award_amount += qty * price
            
            # Create award
            award = RFxAward.objects.create(
                rfx_event=rfx_event,
                supplier=supplier,
                quote=quote,
                award_number=award_number,
                award_amount=award_amount,
                currency=quote.currency if quote else rfx_event.currency,
                justification=justification,
                created_by=request.user
            )
            
            # Create award lines
            for line_item in line_items:
                rfx_item = RFxItem.objects.get(id=line_item['rfx_item_id'])
                quote_line = None
                
                if quote:
                    try:
                        quote_line = SupplierQuoteLine.objects.get(
                            quote=quote,
                            rfx_item=rfx_item
                        )
                    except SupplierQuoteLine.DoesNotExist:
                        pass
                
                RFxAwardLine.objects.create(
                    award=award,
                    rfx_item=rfx_item,
                    quote_line=quote_line,
                    quantity_awarded=line_item['quantity'],
                    unit_price=line_item['unit_price'],
                    delivery_date=line_item.get('delivery_date')
                )
            
            created_awards.append(award)
        
        # Update RFx status
        rfx_event.status = 'AWARDED'
        rfx_event.award_date = timezone.now()
        rfx_event.awarded_by = request.user
        rfx_event.save()
        
        return Response({
            'status': 'success',
            'message': f'{len(created_awards)} award(s) created',
            'awards': RFxAwardSerializer(created_awards, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall RFx statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_rfx': queryset.count(),
            'by_status': {
                status[0]: queryset.filter(status=status[0]).count()
                for status in RFxEvent.EVENT_STATUSES
            },
            'by_type': {
                etype[0]: queryset.filter(event_type=etype[0]).count()
                for etype in RFxEvent.EVENT_TYPES
            },
            'total_auctions': queryset.filter(is_auction=True).count(),
            'overdue_count': sum(1 for rfx in queryset if rfx.is_overdue()),
            'average_response_rate': self._calculate_avg_response_rate(queryset),
        }
        
        return Response(stats)
    
    def _calculate_avg_response_rate(self, queryset):
        """Calculate average response rate across RFx events"""
        total_invited = 0
        total_responded = 0
        
        for rfx in queryset:
            invited = rfx.get_invited_count()
            responded = rfx.get_response_count()
            total_invited += invited
            total_responded += responded
        
        if total_invited > 0:
            return round((total_responded / total_invited) * 100, 2)
        return 0


class RFxItemViewSet(viewsets.ModelViewSet):
    """ViewSet for RFx Items"""
    queryset = RFxItem.objects.all()
    serializer_class = RFxItemSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['rfx_event', 'is_mandatory', 'unit_of_measure']
    search_fields = ['item_code', 'description', 'part_number']
    ordering_fields = ['line_number', 'created_at']
    ordering = ['rfx_event', 'line_number']


class SupplierInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier Invitations"""
    queryset = SupplierInvitation.objects.all()
    serializer_class = SupplierInvitationSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['rfx_event', 'supplier', 'status']
    search_fields = ['rfx_event__rfx_number', 'supplier__name']
    ordering_fields = ['invited_date', 'responded_date']
    ordering = ['-invited_date']
    
    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """Mark invitation as sent"""
        invitation = self.get_object()
        invitation.mark_as_sent()
        return Response({
            'status': 'success',
            'message': 'Invitation marked as sent'
        })
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark invitation as viewed"""
        invitation = self.get_object()
        invitation.mark_as_viewed()
        return Response({
            'status': 'success',
            'message': 'Invitation marked as viewed'
        })


class SupplierQuoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier Quotes"""
    queryset = SupplierQuote.objects.all()
    serializer_class = SupplierQuoteSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'rfx_event': ['exact'],
        'supplier': ['exact'],
        'status': ['exact', 'in'],
        'is_auction_bid': ['exact'],
        'submitted_date': ['gte', 'lte'],
        'total_amount': ['gte', 'lte'],
        'overall_score': ['gte', 'lte'],
    }
    search_fields = ['quote_number', 'rfx_event__rfx_number', 'supplier__name']
    ordering_fields = ['quote_number', 'submitted_date', 'total_amount', 'overall_score']
    ordering = ['-submitted_date']
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit the quote"""
        quote = self.get_object()
        
        if quote.submit():
            return Response({
                'status': 'success',
                'message': f'Quote {quote.quote_number} submitted successfully'
            })
        return Response(
            {'error': 'Quote cannot be submitted (must be in DRAFT status)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate quote totals"""
        quote = self.get_object()
        total = quote.calculate_totals()
        
        return Response({
            'status': 'success',
            'total_amount': total,
            'subtotal': quote.subtotal
        })
    
    @action(detail=True, methods=['post'])
    def calculate_scores(self, request, pk=None):
        """Recalculate evaluation scores"""
        quote = self.get_object()
        quote.calculate_scores()
        
        return Response({
            'status': 'success',
            'price_score': quote.price_score,
            'technical_score': quote.technical_score,
            'overall_score': quote.overall_score
        })
    
    @action(detail=True, methods=['post'])
    def set_technical_score(self, request, pk=None):
        """Set technical evaluation score"""
        quote = self.get_object()
        technical_score = request.data.get('technical_score')
        evaluator_comments = request.data.get('evaluator_comments', '')
        
        if technical_score is None:
            return Response(
                {'error': 'Technical score is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quote.technical_score = Decimal(str(technical_score))
        quote.evaluator_comments = evaluator_comments
        quote.save()
        
        # Recalculate overall score
        quote.calculate_scores()
        
        return Response({
            'status': 'success',
            'technical_score': quote.technical_score,
            'overall_score': quote.overall_score
        })


class SupplierQuoteLineViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier Quote Lines"""
    queryset = SupplierQuoteLine.objects.all()
    serializer_class = SupplierQuoteLineSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['quote', 'rfx_item', 'is_quoted', 'meets_specifications', 'is_alternate']
    search_fields = ['item_description', 'brand_offered', 'part_number_offered']
    ordering = ['rfx_item__line_number']


class RFxAwardViewSet(viewsets.ModelViewSet):
    """ViewSet for RFx Awards"""
    queryset = RFxAward.objects.all()
    serializer_class = RFxAwardSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['rfx_event', 'supplier', 'status', 'approved_by']
    search_fields = ['award_number', 'rfx_event__rfx_number', 'supplier__name', 'po_number']
    ordering_fields = ['award_date', 'award_amount']
    ordering = ['-award_date']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve the award"""
        award = self.get_object()
        
        if award.approve(request.user):
            return Response({
                'status': 'success',
                'message': f'Award {award.award_number} approved'
            })
        return Response(
            {'error': 'Award cannot be approved (must be PENDING)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def create_po(self, request, pk=None):
        """Create Purchase Order from award"""
        award = self.get_object()
        
        if award.status != 'APPROVED':
            return Response(
                {'error': 'Award must be approved before creating PO'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would integrate with your PO creation logic
        # For now, just update the award
        po_number = request.data.get('po_number')
        
        if not po_number:
            return Response(
                {'error': 'PO number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        award.po_number = po_number
        award.po_created_date = timezone.now()
        award.po_created_by = request.user
        award.status = 'PO_CREATED'
        award.save()
        
        return Response({
            'status': 'success',
            'message': f'PO {po_number} created from award {award.award_number}',
            'po_number': po_number
        })


class AuctionBidViewSet(viewsets.ModelViewSet):
    """ViewSet for Auction Bids"""
    queryset = AuctionBid.objects.all()
    serializer_class = AuctionBidSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['rfx_event', 'supplier', 'is_valid', 'is_current_best']
    search_fields = ['rfx_event__rfx_number', 'supplier__name']
    ordering_fields = ['bid_time', 'bid_amount', 'rank']
    ordering = ['rfx_event', '-bid_time']
    
    @action(detail=False, methods=['post'])
    def submit_bid(self, request):
        """Submit a new auction bid"""
        rfx_event_id = request.data.get('rfx_event_id')
        supplier_id = request.data.get('supplier_id')
        bid_amount = request.data.get('bid_amount')
        
        if not all([rfx_event_id, supplier_id, bid_amount]):
            return Response(
                {'error': 'rfx_event_id, supplier_id, and bid_amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rfx_event = RFxEvent.objects.get(id=rfx_event_id)
        
        # Validate auction is active
        now = timezone.now()
        if not rfx_event.is_auction:
            return Response(
                {'error': 'This is not an auction event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (rfx_event.auction_start_date <= now <= rfx_event.auction_end_date):
            return Response(
                {'error': 'Auction is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from ap.models import Supplier
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Get next bid number
        last_bid = AuctionBid.objects.filter(
            rfx_event=rfx_event,
            supplier=supplier
        ).order_by('-bid_number').first()
        
        bid_number = (last_bid.bid_number + 1) if last_bid else 1
        
        # Validate bid amount (must be lower than current best)
        current_best = AuctionBid.objects.filter(
            rfx_event=rfx_event,
            is_current_best=True
        ).first()
        
        bid_amount = Decimal(str(bid_amount))
        
        if current_best and bid_amount >= current_best.bid_amount:
            return Response(
                {'error': f'Bid must be lower than current best bid of {current_best.bid_amount}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create bid
        bid = AuctionBid.objects.create(
            rfx_event=rfx_event,
            supplier=supplier,
            bid_number=bid_number,
            bid_amount=bid_amount
        )
        
        # Update best bid flags
        if current_best:
            current_best.is_current_best = False
            current_best.save()
        
        bid.is_current_best = True
        bid.save()
        
        # Check for auto-extension
        time_remaining = (rfx_event.auction_end_date - now).total_seconds() / 60
        if time_remaining < rfx_event.auction_extension_minutes:
            rfx_event.auction_end_date = timezone.now() + timezone.timedelta(
                minutes=rfx_event.auction_extension_minutes
            )
            rfx_event.save()
            bid.caused_extension = True
            bid.save()
        
        # Update ranks
        self._update_bid_ranks(rfx_event)
        
        return Response({
            'status': 'success',
            'message': 'Bid submitted successfully',
            'bid': AuctionBidSerializer(bid).data,
            'is_best': bid.is_current_best,
            'caused_extension': bid.caused_extension
        })
    
    def _update_bid_ranks(self, rfx_event):
        """Update rank for all bids in an auction"""
        # Get latest bid from each supplier
        from django.db.models import Max
        
        latest_bids = AuctionBid.objects.filter(
            rfx_event=rfx_event
        ).values('supplier').annotate(
            latest_bid_time=Max('bid_time')
        )
        
        bids = []
        for item in latest_bids:
            bid = AuctionBid.objects.get(
                rfx_event=rfx_event,
                supplier_id=item['supplier'],
                bid_time=item['latest_bid_time']
            )
            bids.append(bid)
        
        # Sort by amount and assign ranks
        bids.sort(key=lambda x: x.bid_amount)
        for rank, bid in enumerate(bids, 1):
            bid.rank = rank
            bid.save()
