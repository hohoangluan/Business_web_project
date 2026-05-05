"""URL config cho stats_reports app."""
from django.urls import path
from stats_reports.views import (
    statistics_view,
    statistics_export_csv_view,
    statistics_print_view,
)

urlpatterns = [
    path('statistics/', statistics_view, name='statistics'),
    path('statistics/export-csv/', statistics_export_csv_view, name='statistics_export_csv'),
    path('statistics/print/', statistics_print_view, name='statistics_print'),
]
