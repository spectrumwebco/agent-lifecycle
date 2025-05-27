"""
Django API endpoints for the Veigar cybersecurity agent.

This module provides Django REST Framework API endpoints for the Veigar agent,
allowing external systems to trigger security reviews and retrieve results.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from apps.agent.veigar.django_models.security_models import (
    SecurityReview, SecurityVulnerability, ComplianceIssue
)
from apps.agent.veigar.django_integration.django_integration import (
    create_security_runtime, load_security_config
)

logger = logging.getLogger(__name__)


class SecurityReviewViewSet(viewsets.ModelViewSet):
    """API viewset for security reviews."""
    
    queryset = SecurityReview.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def trigger_review(self, request):
        """Trigger a security review for a pull request."""
        try:
            repository = request.data.get('repository')
            branch = request.data.get('branch')
            pr_id = request.data.get('pr_id')
            pr_title = request.data.get('pr_title', '')
            pr_author = request.data.get('pr_author', '')
            files = request.data.get('files', [])
            
            if not repository or not branch or not pr_id:
                return Response({
                    'status': 'error',
                    'message': 'Missing required fields: repository, branch, pr_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            security_review = SecurityReview.objects.create(
                repository=repository,
                branch=branch,
                pr_id=pr_id,
                pr_title=pr_title,
                pr_author=pr_author,
                status='running'
            )
            
            try:
                runtime = create_security_runtime()
                
                pr_data = {
                    'repository': repository,
                    'branch': branch,
                    'pr_id': pr_id,
                    'files': files
                }
                
                config = load_security_config()
                result = runtime.run_security_review(config, pr_data)
                
                if result.get('status') == 'success':
                    
                    security_review.mark_completed(
                        severity_level=result.get('severity_level', 'none'),
                        summary=result.get('security_report', '')
                    )
                    
                    return Response({
                        'status': 'success',
                        'message': 'Security review completed successfully',
                        'review_id': security_review.id,
                        'severity_level': security_review.severity_level
                    })
                else:
                    security_review.mark_failed(result.get('error', 'Unknown error'))
                    return Response({
                        'status': 'error',
                        'message': f"Security review failed: {result.get('error', 'Unknown error')}",
                        'review_id': security_review.id
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except Exception as e:
                logger.exception(f"Error running security review: {e}")
                security_review.mark_failed(str(e))
                return Response({
                    'status': 'error',
                    'message': f"Error running security review: {str(e)}",
                    'review_id': security_review.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Error processing security review request: {e}")
            return Response({
                'status': 'error',
                'message': f"Error processing security review request: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get the status of a security review."""
        try:
            security_review = self.get_object()
            
            return Response({
                'status': 'success',
                'review_status': security_review.status,
                'severity_level': security_review.severity_level,
                'total_vulnerabilities': security_review.total_vulnerabilities,
                'total_compliance_issues': security_review.total_compliance_issues,
                'is_compliant': security_review.is_compliant,
                'created_at': security_review.created_at.isoformat(),
                'updated_at': security_review.updated_at.isoformat(),
                'completed_at': security_review.completed_at.isoformat() if security_review.completed_at else None
            })
        
        except Exception as e:
            logger.exception(f"Error getting security review status: {e}")
            return Response({
                'status': 'error',
                'message': f"Error getting security review status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a security review."""
        try:
            security_review = self.get_object()
            
            if security_review.status != 'completed':
                return Response({
                    'status': 'error',
                    'message': 'Cannot approve a security review that is not completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not security_review.is_compliant:
                return Response({
                    'status': 'error',
                    'message': 'Cannot approve a security review that is not compliant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response({
                'status': 'success',
                'message': 'Security review approved successfully',
                'review_id': security_review.id
            })
        
        except Exception as e:
            logger.exception(f"Error approving security review: {e}")
            return Response({
                'status': 'error',
                'message': f"Error approving security review: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a security review."""
        try:
            security_review = self.get_object()
            
            if security_review.status != 'completed':
                return Response({
                    'status': 'error',
                    'message': 'Cannot reject a security review that is not completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response({
                'status': 'success',
                'message': 'Security review rejected successfully',
                'review_id': security_review.id
            })
        
        except Exception as e:
            logger.exception(f"Error rejecting security review: {e}")
            return Response({
                'status': 'error',
                'message': f"Error rejecting security review: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for security vulnerabilities."""
    
    queryset = SecurityVulnerability.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_severity(self, request):
        """Get vulnerabilities grouped by severity."""
        try:
            critical = SecurityVulnerability.objects.filter(severity='critical').count()
            high = SecurityVulnerability.objects.filter(severity='high').count()
            medium = SecurityVulnerability.objects.filter(severity='medium').count()
            low = SecurityVulnerability.objects.filter(severity='low').count()
            info = SecurityVulnerability.objects.filter(severity='info').count()
            
            return Response({
                'status': 'success',
                'vulnerabilities': {
                    'critical': critical,
                    'high': high,
                    'medium': medium,
                    'low': low,
                    'info': info,
                    'total': critical + high + medium + low + info
                }
            })
        
        except Exception as e:
            logger.exception(f"Error getting vulnerabilities by severity: {e}")
            return Response({
                'status': 'error',
                'message': f"Error getting vulnerabilities by severity: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComplianceIssueViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for compliance issues."""
    
    queryset = ComplianceIssue.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_framework(self, request):
        """Get compliance issues grouped by framework."""
        try:
            frameworks = {}
            
            for issue in ComplianceIssue.objects.all():
                framework_name = issue.framework.name
                if framework_name not in frameworks:
                    frameworks[framework_name] = {
                        'total': 0,
                        'critical': 0,
                        'high': 0,
                        'medium': 0,
                        'low': 0,
                        'info': 0
                    }
                
                frameworks[framework_name]['total'] += 1
                frameworks[framework_name][issue.severity.lower()] += 1
            
            return Response({
                'status': 'success',
                'frameworks': frameworks
            })
        
        except Exception as e:
            logger.exception(f"Error getting compliance issues by framework: {e}")
            return Response({
                'status': 'error',
                'message': f"Error getting compliance issues by framework: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
