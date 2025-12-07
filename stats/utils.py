# stats/utils.py

from .models import KpiDaily, StatsPeriod
from datetime import date
import pytesseract as pt
from PIL import Image
import io

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
        
        text = pt.image_to_string(image, lang='eng')
        return {
            'success': True,
            'text': text
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }