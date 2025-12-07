from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator
from cloudinary.models import CloudinaryField


class KpiDaily(models.Model):
    
    MOMENT_CHOICES = [
        ('debut', 'Début de capture'),
        ('fin', 'Fin de capture'),
    ]
    
    date = models.DateField()
    moment = models.CharField(max_length=10, choices=MOMENT_CHOICES) # Moment : début ou fin
    msg_sent = models.PositiveIntegerField(default=0)  # Nombre de messages envoyés
    msg_rr = models.FloatField()  # Taux de réponse aux messages
    photos_sent = models.PositiveIntegerField(default=0)  # Nombre de photos envoyées
    photos_rr = models.FloatField()
    gifts_sent = models.PositiveIntegerField(default=0)  # Nombre de cadeaux envoyés
    gifts_rr = models.FloatField()
    speed_rr = models.FloatField()  # Vitesse de réponse
    image_kpi = CloudinaryField('image_kpi', blank=True, null=True)  # Image associée au KPI
    note = models.CharField(max_length=255, blank=True, null=True)  # Note optionnelle
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"KpiDaily {self.date} - {self.moment}"
    
    class Meta:
        db_table = 'kpi_daily'
        verbose_name = 'KPI Journalier'
        verbose_name_plural = 'KPIs Journaliers'
        ordering = ['-date', 'moment'] # Ordre par date décroissante, puis moment croissant
        unique_together = [['date', 'moment']] # Une seule mesure "debut" ou "fin" par date
        
class StatsPeriod(models.Model):
    """Stocke les statistiques par semaine ou mois"""
    PERIOD_CHOICES = [
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ]
    
    MOMENT_CHOICES = [
        ('debut', 'Début de capture'),
        ('fin', 'Fin de capture'),
    ]
    
    kpi_daily = models.ForeignKey(KpiDaily, on_delete=models.CASCADE, related_name='stats_periods')
    moment = models.CharField(max_length=10, choices=MOMENT_CHOICES) # Moment : début ou fin
    
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    responses = models.PositiveIntegerField(default=0)
    kpi_effect = models.IntegerField(default=0)
    extra_benefits = models.IntegerField(default=0)
    penalites = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(0)]
    )
    image_stats = CloudinaryField('image_stats', null=True)  # Image associée aux statistiques
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"StatsPeriod: {self.period_type} for {self.kpi_daily.date} - {self.moment}"
    
    def total(self):
        return (
            ((self.responses+ 
            self.kpi_effect  + 
            self.extra_benefits)* 0.03) - 
            self.penalites
        )
        
    class Meta:
        db_table = 'stats_period'
        verbose_name = 'Statistique Périodique'
        verbose_name_plural = 'Statistiques Périodiques'
        ordering = ['-kpi_daily__date']
        unique_together = [['kpi_daily', 'moment', 'period_type']] # Une seule mesure "debut" ou "fin" par date
        indexes = [
            models.Index(fields=['period_type']),
            models.Index(fields=['kpi_daily', 'period_type']),
        ]