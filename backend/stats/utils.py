# stats/utils.py

from csv import reader
from .models import KpiDaily, StatsPeriod
from datetime import date
import easyocr
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os
import re

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

def extract_kpi_with_easyocr(image_file):
    """
    Extrait les KPIs avec EasyOCR en utilisant les positions géographiques
    """
    try:
        images = image_file.read()
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(images, detail=1)
        
        # Analyser par zones géographiques
        kpi_data = parse_by_geographic_zones(results)
        print(f'donnée extraire: {kpi_data}')
        
        """ return {
            'success': True,
            'data': kpi_data,
            'detections_count': len(results)
        } """
        
    except Exception as e:
        print(f'erreur : {str(e)}')
        return {
            'success': False,
            'error': str(e)
        }


def parse_by_geographic_zones(results):
    """
    Parse les KPIs en divisant l'écran en 4 zones :
    - Zone 1 (haut-gauche) : Messages
    - Zone 2 (haut-droite) : Gifts
    - Zone 3 (bas-gauche) : Photos
    - Zone 4 (bas-droite) : Response Speed
    """
    
    # Séparer les détections par position
    zones = {
        'messages': [],      # x < 480, y < 500
        'gifts': [],         # x >= 480, y < 500
        'photos': [],        # x < 480, y >= 500
        'speeds': [],         # x >= 480, y >= 500
        'meta': []           # Total KPI, KPI Effect (très bas)
    }
    
    for (bbox, text, confidence) in results:
        # Position du centre du texte
        x_center = (bbox[0][0] + bbox[2][0]) / 2
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        
        #print(f" x_centre : {x_center}, y_centre: {y_center}, texte : {text}")
        
        text_clean = text.strip()
        #print(f'text cleaned : {text_clean} avec confidence {confidence} x_centre : {x_center}, y_centre: {y_center}')
        
        # Ignorer texte trop court ou trop peu confiant
        if len(text_clean) < 2 or confidence < 0.3:
            print(f'text court : {text_clean}, len: {len(text_clean)}, and confidence : {confidence}')
            continue
        
        if text_clean =="This week":
            print(text_clean)
        
        # === DÉTECTER LA ZONE ===
        
        # Métadonnées (très bas dans l'image, y > 800)
        if y_center <= 200:
            zones['meta'].append({
                'text': text_clean,
                'x': x_center,
                'y': y_center,
                'confidence': confidence
            })
        # Messages (haut-gauche)
        elif y_center < 500 and  y_center > 300 and x_center < 480:
            zones['messages'].append({
                'text': text_clean,
                'x': x_center,
                'y': y_center,
                'confidence': confidence
            })
        # Gifts (haut-droite)
        elif y_center < 500 and y_center > 300 and x_center >= 480:
            zones['gifts'].append({
                'text': text_clean,
                'x': x_center,
                'y': y_center,
                'confidence': confidence
            })
        # Photos (bas-gauche)
        elif y_center >= 600 and y_center < 800 and x_center < 480:
            zones['photos'].append({
                'text': text_clean,
                'x': x_center,
                'y': y_center,
                'confidence': confidence
            })
        # Response Speed (bas-droite)
        elif y_center >= 600 and y_center < 800 and x_center >= 480:
            zones['speeds'].append({
                'text': text_clean,
                'x': x_center,
                'y': y_center,
                'confidence': confidence
            })
    
    print("********* message")
    for message in zones['messages']:
        print(f'les zones : {message["text"]}')
        
    print("********* gift")
    for gift in zones['gifts']:
        print(f'texte : {gift['text']}')
        
    print("********* photo")
    for photo in zones['photos']:
        print(f'texte : {photo['text']}')
        
    print("********* speed")
    for speed in zones['speeds']:
        print(f'texte : {speed['text']}')
        
    print("********* metadata")
    for meta in zones['meta']:
        print(f'texte : {meta['text']}')
    
    # Parser chaque zone
    kpi_data = {}
    
    # Messages
    msg_data = extract_sent_and_rr(zones['messages'])
    if msg_data:
        kpi_data['msg_sent'] = msg_data.get('sent')
        kpi_data['msg_rr'] = msg_data.get('rr')
    
    # Gifts
    gift_data = extract_sent_and_rr_for_gift_and_photos(zones['gifts'])
    if gift_data:
        kpi_data['gift_sent'] = gift_data.get('sent')
        kpi_data['gift_rr'] = gift_data.get('rr')
    
    # Photos
    photo_data = extract_sent_and_rr_for_gift_and_photos(zones['photos'])
    if photo_data:
        kpi_data['photo_sent'] = photo_data.get('sent')
        kpi_data['photo_rr'] = photo_data.get('rr')
    
    # Response Speed
    """ speed = extract_speed(zones['speeds'])
    if speed:
        kpi_data['speed_rr'] = speed """
    
    # Meta
    meta = extract_meta(zones['meta'])
    kpi_data.update(meta)
    
    #print(f'Zones détectées: {zones}')
    return kpi_data


def extract_sent_and_rr(zone_items):
    """
    Extrait "X Sent" et "Y% RR" d'une zone
    Cherche les patterns peu importe l'ordre
    """
    result = {}
    
    # Combiner tous les textes de la zone
    all_text = ' '.join([item['text'] for item in zone_items])
    print(f'all text joined : {all_text}')
    
    # === CHERCHER "SENT" ===
    # Patterns de référence :
    # - "2520 Sent"
    # - "2250 Sent"
    # - "0 Sent"
    matches = re.findall(r'(\d+)\s*Sent', all_text, re.IGNORECASE)
    if matches:
        # Prendre le PREMIER nombre trouvé avec "Sent"
        # (les badges sont généralement les premiers)
        for match in matches:
            if match != '2520' and match !="2250" and match !="0":
                print(f' matches : {match}')
                result['sent'] = int(match)
            else:
                result['sent'] = 0
    
    # === CHERCHER "RR" (Response Rate) ===
    # Patterns possibles :
    # - "90% RR"
    # - "78%RR" (sans espace)
    # - "0% RR"
    matches = re.findall(r'([\d.]+)\s*RR', all_text, re.IGNORECASE)
    print(matches)
    rr_cleaned = []
    if matches:
        # Prendre le PREMIER pourcentage avec RR
        for match in matches:
            rr_cleaned.append(match[:-2])
        
        for rr in rr_cleaned:
            if rr != '90' and rr !="78" and rr !="0":
                print(f'rr matches : {rr}')
                result['rr'] = float(rr)
            else:
                print("RR pris par defaut 90, développement de l'algo en cours")
                result['rr'] = 90
    
    return result


def extract_sent_and_rr_for_gift_and_photos(zone_items):
    """
    Extrait "X Sent" et "Y% RR" d'une zone
    Cherche les patterns peu importe l'ordre
    """
    result = {}
    
    # Combiner tous les textes de la zone
    all_text = ' '.join([item['text'] for item in zone_items])
    print(f'all text joined : {all_text}')
    
    # === CHERCHER "SENT" ===
    # Patterns de référence :
    # - "540 Sent"
    # - "125 Sent"
    # - "0 Sent"
    matches = re.findall(r'(\d+)\s*Sent', all_text, re.IGNORECASE)
    if matches:
        # Prendre le PREMIER nombre trouvé avec "Sent"
        # (les badges sont généralement les premiers)
        for match in matches:
            if match != '540' and match !="125" and match !="0":
                print(f' sent gift : {match}')
                result['sent'] = int(match)
            else:
                result['sent'] = 0
                print("valeur prise par defaut 0")
    
    # === CHERCHER "RR" (Response Rate) ===
    # Patterns possibles :
    # - "90% RR"
    # - "78%RR" (sans espace)
    # - "0% RR"
    matches = re.findall(r'([\d.]+)\s*RR', all_text, re.IGNORECASE)
    rr_cleaned = []
    if matches:
        for match in matches:
            
            rr_cleaned.append(match[:-2])
            print(f'rr cleaned for gift and photos {len(match)}, {match}, {rr_cleaned}')
        
        for rr in rr_cleaned:
            if rr != '90' and rr !="78" and rr !="0" and rr !="":
                print(f'rr matches : {rr}')
                result['rr'] = float(rr) #Provoque un erreur : could not convert string to float: ''
            else:
                print("valeur prise par defaut : 90")
                result['rr'] = 90
    return result

def extract_speed(zone_items):
    """
    Extrait le pourcentage de Response Speed
    Pattern : "XX.X% Messages answered within 1 minute"
    """
    all_text = ' '.join([item['text'] for item in zone_items])
    
    # Chercher pourcentage avant "Messages answered" ou "answered"
    match = re.search(r'([\d.]+)\s*%.*?answered', all_text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Fallback : chercher juste un pourcentage dans la zone Speed
    match = re.search(r'([\d.]+)\s*%', all_text)
    if match:
        return float(match.group(1))
    
    return None


def extract_meta(zone_items):
    """
    Extrait Total KPI et KPI Effect
    """
    meta = {}
    all_text = ' '.join([item['text'] for item in zone_items])
    
    # Total KPI: -2.5
    match = re.search(r'Total\s*KPI[:\s]*(-?[\d.]+)', all_text, re.IGNORECASE)
    if match:
        meta['total_kpi'] = float(match.group(1))
    
    # KPI Effect: -3%
    match = re.search(r'KPI\s*Effect[:\s]*(-?[\d.]+)', all_text, re.IGNORECASE)
    if match:
        meta['kpi_effect'] = float(match.group(1))
    
    return meta