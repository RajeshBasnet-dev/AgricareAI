import logging
import json
import re
from typing import Dict, Optional, Union
from pathlib import Path
from PIL import Image
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GlobalCropAnalyzer:
    def __init__(self, language: str = "en") -> None:
        """
        Initialize GlobalCropAnalyzer with Gemini API for crop disease analysis worldwide.

        Args:
            language (str): Language for prompts and responses (e.g., 'en' for English, 'es' for Spanish).
        """
        self.model = None
        self.language = language
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Global crop analyzer initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI model: {e}", exc_info=True)
                self.model = None
        else:
            logger.warning("Gemini API key not configured; using mock responses.")

    def analyze_crop_image(self, image_path: str) -> Dict[str, Union[str, float, bool]]:
        """
        Analyze crop image for diseases, suitable for global crops and conditions.

        Args:
            image_path (str): Path to the image file.

        Returns:
            dict: Contains disease analysis results including plant type, disease name,
                  confidence score, explanation, treatment advice, and success status.
        """
        if not Path(image_path).is_file():
            return self._get_error_response("Invalid image path provided.")

        if not self.model:
            return self._get_mock_response()

        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                prompt = self._build_prompt()

                response = self.model.generate_content([prompt, img])
                return self._parse_gemini_response(response.text)

        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return self._get_error_response(str(e))

    def _build_prompt(self) -> str:
        """
        Build a detailed prompt for crop analysis, applicable to global agricultural contexts.

        Returns:
            str: The prompt string in the specified language.
        """
        prompt_templates = {
            "en": (
                "You are an expert agricultural pathologist with global expertise. Analyze this crop/plant image and provide a detailed diagnosis for any agricultural region worldwide.\n\n"
                "Please respond in the following JSON format:\n"
                "{\n"
                '    "plant_type": "specific plant/crop name (e.g., Wheat, Rice, Tomato)",\n'
                '    "disease_name": "specific disease name or \'Healthy\' if no disease detected",\n'
                '    "confidence": confidence_score_as_percentage,\n'
                '    "explanation": "detailed explanation of visible symptoms and diagnosis reasoning, considering diverse climates and soil types",\n'
                '    "treatment": "practical, accessible treatment recommendations suitable for farmers worldwide, including organic and conventional options"\n'
                "}\n\n"
                "Focus on:\n"
                "1. Identifying the plant/crop type (e.g., cereals, legumes, vegetables, fruits, or ornamentals)\n"
                "2. Detecting disease symptoms (e.g., spots, wilting, discoloration, pest damage) relevant to various climates\n"
                "3. Providing accurate disease identification with clear reasoning\n"
                "4. Recommending cost-effective, sustainable treatments (e.g., organic pest control, resistant varieties)\n"
                "5. If no disease is detected, indicate 'Healthy' status with preventive advice\n"
            ),
            "es": (
                "Eres un patólogo agrícola experto con experiencia global. Analiza esta imagen de cultivo/planta y proporciona un diagnóstico detallado para cualquier región agrícola del mundo.\n\n"
                "Por favor, responde en el siguiente formato JSON:\n"
                "{\n"
                '    "plant_type": "nombre específico del cultivo/planta (p. ej., Trigo, Arroz, Tomate)",\n'
                '    "disease_name": "nombre específico de la enfermedad o \'Sano\' si no se detecta ninguna enfermedad",\n'
                '    "confidence": porcentaje_de_confianza,\n'
                '    "explanation": "explicación detallada de los síntomas visibles y razonamiento del diagnóstico, considerando diversos climas y tipos de suelo",\n'
                '    "treatment": "recomendaciones de tratamiento prácticas y accesibles para agricultores de todo el mundo, incluyendo opciones orgánicas y convencionales"\n'
                "}\n\n"
                "Enfócate en:\n"
                "1. Identificar el tipo de planta/cultivo (p. ej., cereales, legumbres, hortalizas, frutas, ornamentales)\n"
                "2. Detectar síntomas de enfermedades (p. ej., manchas, marchitamiento, decoloración, daño por plagas) relevantes para diversos climas\n"
                "3. Proporcionar una identificación precisa de la enfermedad con razonamiento claro\n"
                "4. Recomendar tratamientos rentables y sostenibles (p. ej., control de plagas orgánico, variedades resistentes)\n"
                "5. Si no se detecta ninguna enfermedad, indicar estado 'Sano' con consejos preventivos\n"
            )
        }
        return prompt_templates.get(self.language, prompt_templates["en"])

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Union[str, float, bool]]:
        """
        Parse the Gemini AI response into a structured format.

        Args:
            response_text (str): Raw text response from Gemini AI.

        Returns:
            dict: Parsed data or fallback parsed text response.
        """
        try:
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON object found in response, falling back to text parsing.")
                return self._parse_text_response(response_text)

            json_str = json_match.group()
            data = json.loads(json_str)

            return {
                'plant_type': data.get('plant_type', 'Unknown'),
                'disease_name': data.get('disease_name', 'Unknown'),
                'confidence': float(data.get('confidence', 0)),
                'explanation': data.get('explanation', 'No explanation provided'),
                'treatment': data.get('treatment', 'No treatment information available'),
                'success': True
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            return self._parse_text_response(response_text)
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}", exc_info=True)
            return self._get_error_response(f"Failed to parse AI response: {str(e)}")

    def _parse_text_response(self, text: str) -> Dict[str, Union[str, float, bool]]:
        """
        Fallback parser for non-JSON responses.

        Args:
            text (str): Raw text from AI response.

        Returns:
            dict: Parsed text response in a standard format.
        """
        snippet = (text[:500] + "...") if len(text) > 500 else text
        return {
            'plant_type': 'Unknown',
            'disease_name': 'Analysis completed',
            'confidence': 75.0,
            'explanation': snippet,
            'treatment': (
                'Consult a local agricultural extension service or expert for specific treatment '
                'recommendations tailored to your region.'
            ),
            'success': True
        }

    def _get_mock_response(self) -> Dict[str, Union[str, float, bool]]:
        """
        Provide a mock response for testing or when API key is missing, suitable for global crops.

        Returns:
            dict: Mock disease analysis result.
        """
        return {
            'plant_type': 'Tomato',
            'disease_name': 'Early Blight',
            'confidence': 85.0,
            'explanation': (
                'The image shows dark, concentric spots on tomato leaves, indicative of Early Blight '
                'caused by Alternaria solani, common in warm, wet conditions.'
            ),
            'treatment': (
                'Apply copper-based fungicides or neem oil. Rotate crops, remove infected debris, and ensure '
                'proper spacing for air circulation to prevent spread.'
            ),
            'success': True
        }

    def _get_error_response(self, error_message: str) -> Dict[str, Union[str, float, bool]]:
        """
        Format the error response.

        Args:
            error_message (str): Description of the error.

        Returns:
            dict: Standardized error response.
        """
        error_messages = {
            "en": f"Error during analysis: {error_message}",
            "es": f"Error durante el análisis: {error_message}"
        }
        return {
            'plant_type': 'Unknown',
            'disease_name': 'Analysis Failed',
            'confidence': 0.0,
            'explanation': error_messages.get(self.language, error_messages["en"]),
            'treatment': (
                'Please try uploading the image again or consult a local agricultural expert for assistance.'
            ),
            'success': False,
            'error': error_message
        }