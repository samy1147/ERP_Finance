from django.contrib import admin
from .models import XX_SegmentType, XX_Segment


@admin.register(XX_SegmentType)
class SegmentTypeAdmin(admin.ModelAdmin):
    list_display = ("segment_id", "segment_name", "segment_type",
                    "is_required", "has_hierarchy", "is_active", "display_order")
    list_filter = ("is_required", "has_hierarchy", "is_active")
    search_fields = ("segment_name", "segment_type", "description")
    ordering = ("display_order", "segment_id")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("segment_id", "segment_name", "segment_type", "description")
        }),
        ("Configuration", {
            "fields": ("is_required", "has_hierarchy", "length", "display_order", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")


@admin.register(XX_Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ("code", "alias", "segment_type", "parent_code", "level", "is_active", "envelope_amount")
    list_filter = ("segment_type", "is_active", "level")
    search_fields = ("code", "alias", "parent_code")
    ordering = ("segment_type", "level", "code")
    
    fieldsets = (
        ("Segment Information", {
            "fields": ("segment_type", "code", "alias", "parent_code", "level")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Financial", {
            "fields": ("envelope_amount",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("segment_type",)

