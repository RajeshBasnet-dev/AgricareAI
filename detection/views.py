from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import CropImage, DetectionHistory
from .forms import ImageUploadForm
from .ai_service import GlobalCropAnalyzer
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

class HomeView(View):
    def get(self, request):
        form = ImageUploadForm()
        recent_detections = CropImage.objects.filter(is_processed=True).select_related('user').order_by('-uploaded_at')[:6]
        context = {
            'form': form,
            'recent_detections': recent_detections,
            'supported_languages': getattr(settings, 'SUPPORTED_LANGUAGES', {'en': 'English'}),
        }
        return render(request, 'detection/upload.html', context)

class UploadImageView(View):
    def post(self, request):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                crop_image = form.save(commit=False)
                if request.user.is_authenticated:
                    crop_image.user = request.user
                language = request.POST.get('language', 'en')
                crop_image.language = language
                crop_image.save()
                ai_service = GlobalCropAnalyzer(language=language)
                result = ai_service.analyze_crop_image(crop_image.image.path)
                crop_image.plant_type = result.get('plant_type', 'Unknown')
                crop_image.disease_name = result.get('disease_name', 'Unknown')
                crop_image.confidence = result.get('confidence', 0.0)
                crop_image.explanation = result.get('explanation', '')
                crop_image.treatment = result.get('treatment', '')
                crop_image.is_processed = True
                if not result.get('success', True):
                    crop_image.processing_error = result.get('error', 'Unknown error')
                crop_image.save()
                DetectionHistory.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    crop_image=crop_image,
                    session_id=request.session.session_key or request.session.create(),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, _('Image processed successfully!'))
                return redirect('crop_detection:result', pk=crop_image.pk)
            except Exception as e:
                logger.error(f"Image upload processing error: {str(e)}", exc_info=True)
                messages.error(request, _('An error occurred while processing the image. Please try again.'))
                return redirect('crop_detection:home')
        else:
            messages.error(request, _('Please select a valid image file.'))
            return redirect('crop_detection:home')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        return ip

class ResultView(View):
    def get(self, request, pk):
        crop_image = get_object_or_404(CropImage.objects.select_related('user'), pk=pk)
        context = {
            'crop_image': crop_image,
            'language': crop_image.language,
        }
        return render(request, 'detection/result.html', context)

class HistoryView(View):
    def get(self, request):
        if request.user.is_authenticated:
            crop_images = CropImage.objects.filter(
                user=request.user, is_processed=True
            ).select_related('user').order_by('-uploaded_at')
        else:
            session_key = request.session.session_key
            if session_key:
                detection_histories = DetectionHistory.objects.filter(session_id=session_key).values_list('crop_image_id', flat=True)
                crop_images = CropImage.objects.filter(
                    id__in=detection_histories, is_processed=True
                ).select_related('user').order_by('-uploaded_at')
            else:
                crop_images = CropImage.objects.none()
        paginator = Paginator(crop_images, 12)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        context = {
            'page_obj': page_obj,
            'total_detections': crop_images.count(),
        }
        return render(request, 'detection/history.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class APIUploadView(View):
    def post(self, request):
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'error': 'No image file provided'}, status=400)
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                crop_image = form.save(commit=False)
                if request.user.is_authenticated:
                    crop_image.user = request.user
                language = request.POST.get('language', 'en')
                crop_image.language = language
                crop_image.save()
                ai_service = GlobalCropAnalyzer(language=language)
                result = ai_service.analyze_crop_image(crop_image.image.path)
                crop_image.plant_type = result.get('plant_type', 'Unknown')
                crop_image.disease_name = result.get('disease_name', 'Unknown')
                crop_image.confidence = result.get('confidence', 0.0)
                crop_image.explanation = result.get('explanation', '')
                crop_image.treatment = result.get('treatment', '')
                crop_image.is_processed = True
                if not result.get('success', True):
                    crop_image.processing_error = result.get('error', 'Unknown error')
                crop_image.save()
                DetectionHistory.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    crop_image=crop_image,
                    session_id=request.session.session_key or request.session.create(),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return JsonResponse({
                    'success': True,
                    'id': crop_image.id,
                    'plant_type': crop_image.plant_type,
                    'disease_name': crop_image.disease_name,
                    'confidence': round(crop_image.confidence, 2),
                    'explanation': crop_image.explanation,
                    'treatment': crop_image.treatment,
                    'image_url': crop_image.image.url,
                    'language': crop_image.language,
                })
            else:
                return JsonResponse({'error': 'Invalid form data'}, status=400)
        except Exception as e:
            logger.error(f"API upload error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Server error occurred'}, status=500)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        return ip

class APIResultView(View):
    def get(self, request, pk):
        try:
            crop_image = get_object_or_404(CropImage.objects.select_related('user'), pk=pk)
            return JsonResponse({
                'success': True,
                'id': crop_image.id,
                'plant_type': crop_image.plant_type,
                'disease_name': crop_image.disease_name,
                'confidence': round(crop_image.confidence, 2),
                'explanation': crop_image.explanation,
                'treatment': crop_image.treatment,
                'image_url': crop_image.image.url,
                'language': crop_image.language,
                'uploaded_at': crop_image.uploaded_at.isoformat(),
            })
        except Exception as e:
            logger.error(f"API result error for pk={pk}: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Server error occurred'}, status=500)