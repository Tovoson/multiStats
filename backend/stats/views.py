from django.http import JsonResponse
from stats.utils import calculer_delta_journalier, extract_kpi_with_easyocr
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import KpiDailySerializer, StatsPeriodSerializer
from .models import KpiDaily, StatsPeriod
from rest_framework import status

class KPIDailyView(APIView):
    def get(self, request, format=None):
        kpi = KpiDaily.objects.all()
        serializer = KpiDailySerializer(kpi, many=True)
        return Response(serializer.data)

    """
    Extraction 100% automatique - Gère les badges à position variable
    """
    def post(self, request, format=None):
        # 1. Vérifier l'image
        uploaded_image = request.FILES.get('image_kpi')
        
        if not uploaded_image:
            return Response({
                'success': False,
                'error': 'Aucune image téléchargée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Extraire avec EasyOCR
        """ 
        Response = {success, data, detections_count}
        """
        result = extract_kpi_with_easyocr(uploaded_image)
        print(result['data'])
        #return Response({"data": result['data']})
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        kpi_data = result['data']
        
        # 3. Ajouter date, moment, note
        kpi_data['date'] = request.data.get('date', str(date.today())) # cherche "date" (reçu par l'api rest), si ça n'existe pas il utilise date.today ( par defaut )
        kpi_data['moment'] = request.data.get('moment', 'debut')
        
        print(f"{kpi_data['date']},{kpi_data['moment']}")
        
        note = request.data.get('note')
        if note:
            kpi_data['note'] = note
        
        # 4. Vérifier complétude
        required_fields = ['msg_sent', 'msg_rr', 'photo_sent', 'photo_rr', 
                          'gift_sent', 'gift_rr', 'speed_rr']
        missing_fields = [f for f in required_fields if f not in kpi_data or kpi_data[f] is None]
        
        if missing_fields:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
            return Response({
                'success': False,
                'error': 'Données incomplètes',
                'extracted_data': kpi_data,
                'missing_fields': missing_fields,
                'detections': result.get('detections_count', 0),
                'suggestion': 'Vérifiez la qualité/résolution de l\'image'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "data": kpi_data
        })
        # 5. Valider et sauvegarder
        """ serializer = KpiDailySerializer(data=kpi_data)
        
        if serializer.is_valid():
            kpi = serializer.save()
            
            return Response({
                'success': True,
                'message': 'KPI créé automatiquement ! ✅',
                'kpi': serializer.data,
                'detections': result.get('detections_count', 0)
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': 'Validation échouée',
            'extracted_data': kpi_data,
            'validation_errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) """

def index(request):
    # Calculer le delta d'aujourd'hui
    resultat = calculer_delta_journalier(date(2025, 12, 2))

    if resultat['success']:
        # Retourner en JSON (plus pratique)
        return JsonResponse({
            'status': 'success',
            'data': {
                'delta_kpi': resultat['delta_kpi'],
                'delta_stats': resultat['delta_stats']
            }
        })
    else:
        # Retourner une erreur en JSON
        return JsonResponse({
            'status': 'error',
            'message': resultat.get('error', 'Données non trouvées')
        }, status=404)