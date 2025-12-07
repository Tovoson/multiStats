# stats/utils.py

from .models import KpiDaily, StatsPeriod
from datetime import date
import pytesseract as pt
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os

def calculer_delta_journalier(date_jour):
    """
    Calcule la différence entre fin et début pour une date donnée
    """
    try:
        # Récupérer début et fin
        debut = KpiDaily.objects.get(date=date_jour, moment='debut')
        fin = KpiDaily.objects.get(date=date_jour, moment='fin')
        
        # Calculer les deltas stats (week et month)
        stat_debut_week = StatsPeriod.objects.get(kpi_daily=debut, period_type='week')
        stat_fin_week = StatsPeriod.objects.get(kpi_daily=fin, period_type='week')
        
        stat_debut_month = StatsPeriod.objects.get(kpi_daily=debut, period_type='month')
        stat_fin_month = StatsPeriod.objects.get(kpi_daily=fin, period_type='month')
        
        msg_env = fin.msg_sent - debut.msg_sent
        msg_recu = stat_fin_week.responses - stat_debut_week.responses
        
        # Calculer les deltas KPI
        delta_kpi = {
            'date': date_jour,
            'msg_sent': msg_env,
            'msg_rr': (msg_recu*100)/msg_env,
            'photos_sent': fin.photos_sent - debut.photos_sent,
            'gifts_sent': fin.gifts_sent - debut.gifts_sent,
        }
        
        delta_stats = {
            'week': {
                'responses': msg_recu,
                'kpi_effect': stat_fin_week.kpi_effect,
                'extra_benefit': stat_fin_week.extra_benefits,
                'penalite': stat_fin_week.penalites,
                'total': stat_fin_week.total(),
            },
            'month': {
                'responses': stat_fin_month.responses,
                'kpi_effect': stat_fin_month.kpi_effect,
                'extra_benefit': stat_fin_month.extra_benefits,
                'penalite': stat_fin_month.penalites,
                'total': stat_fin_month.total(),
            }
        }
        
        return {
            'success': True,
            'delta_kpi': delta_kpi,
            'delta_stats': delta_stats
        }
        
    except KpiDaily.DoesNotExist:
        return {
            'success': False,
            'error': f"Données manquantes pour le {date_jour}"
        }

def preprocess_image_for_ocr(image):
    """
    Améliore l'image pour un meilleur OCR
    Optimisé pour capturer du texte clair sur fond sombre
    """
    # Convertir en niveaux de gris
    image = image.convert('L')
    
    # Inverser les couleurs (texte clair sur fond sombre)
    image = ImageOps.invert(image)
    
    # Augmenter le contraste (x3 pour texte difficile)
    enchancer = ImageEnhance.Contrast(image)
    image = enchancer.enhance(3)

    #Augmenter la luminosité
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.5)

    # Appliquer un seuil (binarisation)
    # Convertir tous les pixels en noir ou blanc pur
    threshold = 150
    image = image.point(lambda p:255 if p > threshold else 0)

    #Appliquer la netteté
    image = image.filter(ImageFilter.SHARPEN)

    # Agrandir l'image (x2) pour meilleure reconnaissance
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.LANCZOS)

    return  image

def extract_text_from_image(image_file):
    """
    Extrait le texte d'une image uploadée avec pytesseract
    
    Args:
        image_file: Objet InMemoryUploadedFile ou TemporaryUploadedFile de Django
    
    Returns:
        dict: {'success': bool, 'text': str} ou {'success': bool, 'error': str}
    """
    try:
        image = Image.open(image_file)

        #Prétraiter l'image
        processed_image = preprocess_image_for_ocr(image)

        debug_path = 'img_debug.png'
        processed_image.save(debug_path)
        print(f'Image prétraitée sauvegardé dans {debug_path}')

        # Extraire le texte avec configuration optimisée
        # --psm 6 = assume a single uniform block of text
        # --oem 3 = use LSTM OCR Engine
        custom_config = r'--oem 3 --psm 6'
        text = pt.image_to_string(processed_image, lang='eng', config=custom_config)
        return {
            'success': True,
            'text': text.strip()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }