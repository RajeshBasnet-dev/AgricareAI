from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CropImage(models.Model):
    """
    Model to store uploaded crop images and their AI analysis results.
    """
    # Expanded disease choices for global relevance
    DISEASE_CHOICES = [
        ('healthy', _('Healthy')),
        ('bacterial_blight', _('Bacterial Blight')),
        ('brown_spot', _('Brown Spot')),
        ('leaf_blast', _('Leaf Blast')),
        ('tungro', _('Tungro')),
        ('bacterial_leaf_streak', _('Bacterial Leaf Streak')),
        ('sheath_blight', _('Sheath Blight')),
        ('early_blight', _('Early Blight')),
        ('powdery_mildew', _('Powdery Mildew')),
        ('downy_mildew', _('Downy Mildew')),
        ('mosaic_virus', _('Mosaic Virus')),
        ('unknown', _('Unknown Disease')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("The user who uploaded the image, if authenticated.")
    )
    image = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        verbose_name=_("Image"),
        help_text=_("Uploaded crop image for analysis.")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At"),
        help_text=_("Timestamp when the image was uploaded.")
    )
    language = models.CharField(
        max_length=10,
        default='en',
        choices=[(lang_code, lang_name) for lang_code, lang_name in settings.SUPPORTED_LANGUAGES.items()],
        verbose_name=_("Language"),
        help_text=_("Language used for AI analysis and result display.")
    )

    # AI Analysis Results
    plant_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Plant Type"),
        help_text=_("Type of plant or crop identified (e.g., Tomato, Rice).")
    )
    disease_name = models.CharField(
        max_length=100,
        choices=DISEASE_CHOICES,
        blank=True,
        verbose_name=_("Disease Name"),
        help_text=_("Identified disease or 'Healthy' if no disease detected.")
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Confidence Score"),
        help_text=_("Confidence percentage of the AI diagnosis.")
    )
    explanation = models.TextField(
        blank=True,
        verbose_name=_("Explanation"),
        help_text=_("Detailed explanation of the diagnosis and symptoms.")
    )
    treatment = models.TextField(
        blank=True,
        verbose_name=_("Treatment"),
        help_text=_("Recommended treatment and preventive measures.")
    )

    # Processing status
    is_processed = models.BooleanField(
        default=False,
        verbose_name=_("Is Processed"),
        help_text=_("Indicates if the image has been processed by AI.")
    )
    processing_error = models.TextField(
        blank=True,
        verbose_name=_("Processing Error"),
        help_text=_("Error message if AI processing failed.")
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _("Crop Image")
        verbose_name_plural = _("Crop Images")
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['user', 'is_processed']),
        ]

    def __str__(self):
        return f"{_('Image')} {self.id} - {self.disease_name or _('Unprocessed')} ({self.language})"

    def save(self, *args, **kwargs):
        """
        Override save to resize large images and optimize storage.
        """
        super().save(*args, **kwargs)

        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize image if too large (max 1024x1024)
                max_size = getattr(settings, 'MAX_IMAGE_SIZE', (1024, 1024))
                if img.height > max_size[0] or img.width > max_size[1]:
                    img.thumbnail(max_size)
                    img.save(self.image.path, quality=85, optimize=True)
            except Exception as e:
                logger.error(f"Image resizing error for {self.image.path}: {str(e)}", exc_info=True)

    def delete(self, *args, **kwargs):
        """
        Override delete to remove associated image file from storage.
        """
        if self.image:
            if os.path.isfile(self.image.path):
                try:
                    os.remove(self.image.path)
                except Exception as e:
                    logger.error(f"Error deleting image file {self.image.path}: {str(e)}", exc_info=True)
        super().delete(*args, **kwargs)

class DetectionHistory(models.Model):
    """
    Model to store history of crop image detections for tracking purposes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("The user who performed the detection, if authenticated.")
    )
    crop_image = models.ForeignKey(
        CropImage,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name=_("Crop Image"),
        help_text=_("The associated crop image.")
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Session ID"),
        help_text=_("Session identifier for anonymous users.")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("Client IP address for tracking.")
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Client user agent for tracking.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when the detection was recorded.")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Detection History")
        verbose_name_plural = _("Detection Histories")
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{_('Detection')} {self.id} - {self.crop_image} ({self.created_at})"