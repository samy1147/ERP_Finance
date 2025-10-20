from django.contrib import admin
from .models import Currency, TaxRate, ExchangeRate, FXGainLossAccount

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "is_base")
    list_filter = ("is_base",)
    search_fields = ("code", "name", "symbol")
    ordering = ("code",)
    
    fieldsets = (
        ("Currency Information", {
            "fields": ("code", "name", "symbol", "is_base")
        }),
    )

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("country", "name", "rate", "category", "code", "effective_from", "effective_to", "is_active")
    list_filter = ("country", "category", "is_active")
    search_fields = ("country", "name", "code")
    date_hierarchy = "effective_from"
    ordering = ("country", "-effective_from")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "rate", "country", "category", "code", "is_active")
        }),
        ("Effective Dates", {
            "fields": ("effective_from", "effective_to")
        }),
    )


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("from_currency", "to_currency", "rate", "rate_date", "rate_type", "is_active", "source")
    list_filter = ("from_currency", "to_currency", "rate_type", "is_active", "rate_date")
    search_fields = ("from_currency__code", "to_currency__code", "source")
    date_hierarchy = "rate_date"
    ordering = ("-rate_date", "from_currency", "to_currency")
    
    fieldsets = (
        ("Currency Pair", {
            "fields": ("from_currency", "to_currency")
        }),
        ("Rate Information", {
            "fields": ("rate", "rate_date", "rate_type", "source", "is_active")
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")


@admin.register(FXGainLossAccount)
class FXGainLossAccountAdmin(admin.ModelAdmin):
    list_display = ("gain_loss_type", "account", "is_active")
    list_filter = ("gain_loss_type", "is_active")
    search_fields = ("account__code", "account__name", "notes")
    
    fieldsets = (
        ("Account Configuration", {
            "fields": ("account", "gain_loss_type", "is_active")
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
    )

