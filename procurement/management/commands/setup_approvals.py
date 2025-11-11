"""
Management command to setup approval workflows.
Usage: python manage.py setup_approvals
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from procurement.approvals.models import ApprovalWorkflow, ApprovalStep, ApprovalInstance
from django.contrib.contenttypes.models import ContentType
from procurement.requisitions.models import PRHeader


class Command(BaseCommand):
    help = 'Setup default approval workflows for procurement'

    def handle(self, *args, **options):
        self.stdout.write('Setting up approval workflows...\n')
        
        # Get admin user
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('No admin user found. Please create a superuser first.'))
            return
        
        # Get PR content type
        pr_content_type = ContentType.objects.get_for_model(PRHeader)
        
        # Create workflow
        workflow, created = ApprovalWorkflow.objects.get_or_create(
            name="PR Standard Approval",
            defaults={
                'description': 'Standard approval workflow for Purchase Requisitions',
                'document_type': 'requisitions.PRHeader',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created workflow: {workflow.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Workflow already exists: {workflow.name}'))
        
        # Ensure approval steps exist
        if not workflow.steps.exists():
            self.stdout.write('Creating approval steps...')
            
            # Create approval steps
            step1 = ApprovalStep.objects.create(
                workflow=workflow,
                sequence=1,
                name="Manager Approval",
                description="Approval by department manager",
                approver_type='USER',
                amount_threshold=0,  # Apply to all amounts
            )
            step1.approvers.add(admin)
            self.stdout.write(self.style.SUCCESS(f'Created step: {step1.name}'))
        else:
            self.stdout.write(f'Steps already exist: {workflow.steps.count()} steps')
        
        # Apply to existing submitted PRs
        submitted_prs = PRHeader.objects.filter(status='SUBMITTED')
        self.stdout.write(f'\nFound {submitted_prs.count()} submitted PRs')
        
        for pr in submitted_prs:
            if not ApprovalInstance.objects.filter(
                content_type=pr_content_type,
                object_id=pr.id
            ).exists():
                # Use workflow's initiate_approval method
                instance = workflow.initiate_approval(
                    document=pr,
                    amount=pr.total_amount,
                    requested_by=pr.requestor
                )
                if instance:
                    self.stdout.write(self.style.SUCCESS(f'Created approval instance for {pr.pr_number}'))
                else:
                    self.stdout.write(self.style.WARNING(f'No approval needed for {pr.pr_number} (auto-approved)'))
            else:
                self.stdout.write(self.style.WARNING(f'Approval already exists for {pr.pr_number}'))
        
        self.stdout.write(self.style.SUCCESS('\nSetup complete!'))
