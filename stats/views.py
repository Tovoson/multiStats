from django.http import JsonResponse
from stats.utils import calculer_delta_journalier, extract_text_from_image
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

    def post(self, request, format=None):
        #serializer = KpiDailySerializer(data=request.data)
        
        uploaded_image = request.FILES.get('image_kpi')
            
        if not uploaded_image:
            return Response({'error': 'No image uploaded'}, status=status.HTTP_400_BAD_REQUEST)
            
            
        print('Uploaded image:', uploaded_image.name)
        resultat = extract_text_from_image(uploaded_image)
        print('Extraction result:', resultat)
        
        if not resultat['success']:
            return Response({'error': 'Text extraction failed', 'details':resultat['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({'success': True,'text': resultat['text']}, status=status.HTTP_200_OK)

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