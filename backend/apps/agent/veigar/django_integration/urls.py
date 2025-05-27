"""
URL configuration for the Veigar cybersecurity agent.

This module provides URL patterns for the Veigar agent's Django views and API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.agent.veigar.django_views import security_views
from apps.agent.veigar.django_integration import api

router = DefaultRouter()
router.register(r'security-reviews', api.SecurityReviewViewSet)
router.register(r'vulnerabilities', api.VulnerabilityViewSet)
router.register(r'compliance-issues', api.ComplianceIssueViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    
    path('security-reviews/', security_views.SecurityReviewListView.as_view(), name='security_review_list'),
    path('security-reviews/<int:pk>/', security_views.SecurityReviewDetailView.as_view(), name='security_review_detail'),
    path('security-reviews/trigger/', security_views.trigger_security_review, name='trigger_security_review'),
    path('security-reviews/<int:review_id>/status/', security_views.security_review_status, name='security_review_status'),
    path('security-reviews/<int:review_id>/approve/', security_views.approve_security_review, name='approve_security_review'),
    path('security-reviews/<int:review_id>/reject/', security_views.reject_security_review, name='reject_security_review'),
]
