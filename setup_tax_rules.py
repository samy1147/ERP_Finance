import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from finance.models import CorporateTaxRule

print('Checking Corporate Tax Rules:\n')
rules = CorporateTaxRule.objects.all()
print(f'Total rules: {rules.count()}\n')

if rules.count() > 0:
    for rule in rules:
        print(f'Country: {rule.country} ({rule.get_country_display()})')
        print(f'  Rate: {rule.rate}%')
        print(f'  Threshold: {rule.threshold}')
        print(f'  Active: {rule.active}')
        print()
else:
    print('⚠ No Corporate Tax Rules found!')
    print('\nCreating default tax rules for UAE, KSA, Egypt, and India...\n')
    
    # UAE - 9% corporate tax (effective from June 2023)
    CorporateTaxRule.objects.create(
        country='AE',
        rate=9.0,
        threshold=None,
        active=True
    )
    print('✓ Created UAE corporate tax rule: 9%')
    
    # KSA - 20% corporate tax
    CorporateTaxRule.objects.create(
        country='SA',
        rate=20.0,
        threshold=None,
        active=True
    )
    print('✓ Created KSA corporate tax rule: 20%')
    
    # Egypt - 22.5% corporate tax
    CorporateTaxRule.objects.create(
        country='EG',
        rate=22.5,
        threshold=None,
        active=True
    )
    print('✓ Created Egypt corporate tax rule: 22.5%')
    
    # India - 30% corporate tax (basic rate)
    CorporateTaxRule.objects.create(
        country='IN',
        rate=30.0,
        threshold=None,
        active=True
    )
    print('✓ Created India corporate tax rule: 30%')
    
    print('\n✓ All tax rules created successfully!')
