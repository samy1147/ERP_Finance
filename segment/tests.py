# Segment app tests
from django.test import TestCase
from .models import XX_Segment, XX_SegmentType
from .utils import SegmentHelper


class SegmentTestCase(TestCase):
    def setUp(self):
        # Create Account segment type
        self.account_type = XX_SegmentType.objects.create(
            segment_id=1,
            segment_name="Account",
            segment_type="account",
            has_hierarchy=True,
            length=4,
            is_required=True
        )
        
        # Create test account segment
        self.account = XX_Segment.objects.create(
            code="1000",
            alias="Test Account",
            segment_type=self.account_type,
            node_type="parent",
            level=0,
            is_active=True
        )
    
    def test_segment_creation(self):
        """Test that segment is created correctly"""
        self.assertEqual(self.account.code, "1000")
        self.assertEqual(self.account.alias, "Test Account")
        self.assertTrue(self.account.is_active)
        
    def test_segment_helper_get_account(self):
        """Test SegmentHelper can retrieve accounts"""
        account = SegmentHelper.get_account_by_code("1000")
        self.assertIsNotNone(account)
        self.assertEqual(account.code, "1000")
        
    def test_segment_helper_get_all_accounts(self):
        """Test SegmentHelper can retrieve all accounts"""
        accounts = SegmentHelper.get_account_segments()
        self.assertEqual(accounts.count(), 1)
        self.assertEqual(accounts.first().code, "1000")
