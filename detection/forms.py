from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import CropImage
from PIL import Image
import io

class ImageUploadForm(forms.ModelForm):
    """
    Form for uploading crop images with validation and language selection.
    """
    language = forms.ChoiceField(
        choices=lambda: [(code, name) for code, name in settings.SUPPORTED_LANGUAGES.items()],
        label=_("Language"),
        help_text=_("Select the language for AI analysis and results."),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'languageSelect'
        })
    )

    class Meta:
        model = CropImage
        fields = ['image', 'language']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'imageUpload'
            }),
        }
        labels = {
            'image': _("Crop Image"),
        }
        help_texts = {
            'image': _("Upload an image of the crop for disease analysis (JPEG, PNG, max 10MB)."),
        }

    def clean_image(self):
        """
        Validate the uploaded image for size, format, and dimensions.
        """
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError(_("No image file provided."))

        # Check file size (configurable max size, default 10MB)
        max_size_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)
        if image.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                _("Image file too large (max %(size)d MB)") % {'size': max_size_mb}
            )

        # Check file type
        if not image.content_type.startswith('image/'):
            raise forms.ValidationError(_("File must be an image (e.g., JPEG, PNG)."))

        # Validate image dimensions and format
        try:
            with Image.open(image.file) as img:
                # Ensure image is readable
                img.verify()

                # Reopen image for further checks since verify() closes the file
                image.file.seek(0)
                with Image.open(image.file) as img:
                    # Check minimum dimensions (e.g., 100x100 pixels)
                    min_dimensions = getattr(settings, 'MIN_IMAGE_DIMENSIONS', (100, 100))
                    if img.size[0] < min_dimensions[0] or img.size[1] < min_dimensions[1]:
                        raise forms.ValidationError(
                            _("Image dimensions too small (minimum %(width)dx%(height)d pixels).") % {
                                'width': min_dimensions[0],
                                'height': min_dimensions[1]
                            }
                        )

                    # Ensure image format is supported
                    supported_formats = getattr(settings, 'SUPPORTED_IMAGE_FORMATS', ['JPEG', 'PNG', 'GIF'])
                    if img.format not in supported_formats:
                        raise forms.ValidationError(
                            _("Unsupported image format. Supported formats: %(formats)s.") % {
                                'formats': ', '.join(supported_formats)
                            }
                        )
        except Exception as e:
            raise forms.ValidationError(_("Invalid image file: %(error)s") % {'error': str(e)})

        return image

    def clean_language(self):
        """
        Validate the selected language.
        """
        language = self.cleaned_data.get('language', 'en')
        if language not in dict(settings.SUPPORTED_LANGUAGES):
            raise forms.ValidationError(_("Selected language is not supported."))
        return language

    def clean(self):
        """
        Perform additional form-wide validation.
        """
        cleaned_data = super().clean()
        # Add any cross-field validation if needed in the future
        return cleaned_data