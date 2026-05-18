"""URL config cho stats_reports app."""
from django.urls import path
from stats_reports.views import (
    statistics_view,
    statistics_export_excel_view,
    statistics_print_view,
)

urlpatterns = [
    path('statistics/', statistics_view, name='statistics'),
    path('statistics/export-excel/', statistics_export_excel_view, name='statistics_export_excel'),
    path('statistics/print/', statistics_print_view, name='statistics_print'),
]
