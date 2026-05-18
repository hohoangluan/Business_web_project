"""URL config cho reports_interactions app."""
from django.urls import path
from reports_interactions.views import (
    report_view,
    report_inbox_view,
    report_detail_view,
    ticket_list_view,
    ticket_process_view,
)

urlpatterns = [
    path('reports/', report_view, name='reports'),
    path('reports/inbox/', report_inbox_view, name='report_inbox'),
    path('reports/<int:pk>/', report_detail_view, name='report_detail'),
    path('tickets/', ticket_list_view, name='tickets'),
    path('tickets/process/', ticket_process_view, name='ticket_process'),
]
