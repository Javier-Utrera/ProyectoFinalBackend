import django_filters
from django_filters import rest_framework as filters
from .models import Relato

class RelatoFilter(filters.FilterSet):
    # Búsqueda específica por título o descripción (co-existentes al SearchFilter)
    titulo__icontains      = filters.CharFilter(field_name='titulo', lookup_expr='icontains')
    descripcion__icontains = filters.CharFilter(field_name='descripcion', lookup_expr='icontains')

    # Rango de fechas
    fecha_desde = filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_hasta = filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')

    # Idioma exacto
    idioma = filters.CharFilter(field_name='idioma', lookup_expr='exact')

    # Generos
    generos = django_filters.CharFilter(field_name='generos', lookup_expr='icontains')

    # Número de escritores: exacto, >= y <=
    num_escritores        = filters.NumberFilter(field_name='num_escritores', lookup_expr='exact')
    num_escritores__gte   = filters.NumberFilter(field_name='num_escritores', lookup_expr='gte')
    num_escritores__lte   = filters.NumberFilter(field_name='num_escritores', lookup_expr='lte')

    # Busqueda por autor
    autor = filters.CharFilter(
        field_name='participacionrelato__usuario__username',
        lookup_expr='icontains',
        label='Usuario participante'
    )

    class Meta:
        model = Relato
        fields = [
            'titulo__icontains',
            'descripcion__icontains',
            'idioma',
            'generos',
            'num_escritores',
            'num_escritores__gte',
            'num_escritores__lte',
            'fecha_desde',
            'fecha_hasta',
            'autor',
        ]