from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from .models import CropImage, DetectionHistory
import csv
from django.http import HttpResponse

@admin.register(CropImage)
class CropImageAdmin(admin.ModelAdmin):
    """
    Admin interface for managing CropImage instances.
    """
    list_display = (
        'id',
        'thumbnail',
        'plant_type',
        'disease_name',
        'confidence_display',
        'language',
        'is_processed',
        'uploaded_at',
        'user',
    )
    list_filter = (
        'is_processed',
        'language',
        'disease_name',
        'plant_type',
        ('uploaded_at', admin.DateFieldListFilter),
    )
    search_fields = ('plant_type', 'disease_name', 'explanation', 'treatment')
    list_per_page = 20
    readonly_fields = ('uploaded_at', 'processing_error', 'image_preview')
    list_select_related = ('user',)
    autocomplete_fields = ('user',)
    ordering = ('-uploaded_at',)
    fieldsets = (
        (_('Image Details'), {
            'fields': ('image', 'image_preview', 'user', 'language', 'uploaded_at'),
        }),
        (_('AI Analysis Results'), {
            'fields': ('plant_type', 'disease_name', 'confidence', 'explanation', 'treatment'),
        }),
        (_('Processing Status'), {
            'fields': ('is_processed', 'processing_error'),
        }),
    )
    actions = ['export_to_csv']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related for performance.
        """
        return super().get_queryset(request).select_related('user')

    def thumbnail(self, obj):
        """
        Display a thumbnail of the uploaded image.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url
            )
        return '-'
    thumbnail.short_description = _('Thumbnail')

    def image_preview(self, obj):
        """
        Display a larger image preview in the change view.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 300px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = _('Image Preview')

    def confidence_display(self, obj):
        """
        Display confidence score as a percentage.
        """
        return f"{obj.confidence:.2f}%" if obj.confidence is not None else '-'
    confidence_display.short_description = _('Confidence')

    def export_to_csv(self, request, queryset):
        """
        Export selected CropImage records to CSV.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="crop_images_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Plant Type', 'Disease Name', 'Confidence',
            'Explanation', 'Treatment', 'Language', 'Uploaded At', 'Processed', 'Image URL'
        ])

        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.user.username if obj.user else 'Anonymous',
                obj.plant_type,
                obj.disease_name,
                obj.confidence,
                obj.explanation,
                obj.treatment,
                obj.language,
                obj.uploaded_at,
                obj.is_processed,
                obj.image.url if obj.image else '',
            ])

        return response
    export_to_csv.short_description = _('Export selected images to CSV')

@admin.register(DetectionHistory)
class DetectionHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for managing DetectionHistory instances.
    """
    list_display = (
        'id',
        'crop_image_link',
        'user',
        'session_id',
        'ip_address',
        'created_at',
    )
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        'user',
    )
    search_fields = ('session_id', 'ip_address', 'user_agent', 'crop_image__plant_type', 'crop_image__disease_name')
    list_per_page = 20
    readonly_fields = ('created_at', 'user_agent')
    list_select_related = ('user', 'crop_image')
    autocomplete_fields = ('user', 'crop_image')
    ordering = ('-created_at',)
    fieldsets = (
        (_('Detection Details'), {
            'fields': ('crop_image', 'user', 'session_id', 'ip_address', 'user_agent', 'created_at'),
        }),
    )
    actions = ['export_to_csv']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related for performance.
        """
        return super().get_queryset(request).select_related('user', 'crop_image')

    def crop_image_link(self, obj):
        """
        Display a clickable link to the associated CropImage.
        """
        if obj.crop_image:
            url = reverse('admin:crop_detection_cropimage_change', args=[obj.crop_image.id])
            return format_html('<a href="{}">{}</a>', url, obj.crop_image)
        return '-'
    crop_image_link.short_description = _('Crop Image')

    def export_to_csv(self, request, queryset):
        """
        Export selected DetectionHistory records to CSV.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="detection_history_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Crop Image ID', 'Plant Type', 'Disease Name',
            'Session ID', 'IP Address', 'User Agent', 'Created At'
        ])

        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.user.username if obj.user else 'Anonymous',
                obj.crop_image.id if obj.crop_image else '',
                obj.crop_image.plant_type if obj.crop_image else '',
                obj.crop_image.disease_name if obj.crop_image else '',
                obj.session_id,
                obj.ip_address,
                obj.user_agent,
                obj.created_at,
            ])

        return response
    export_to_csv.short_description = _('Export selected detection history to CSV')