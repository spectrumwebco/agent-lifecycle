"""
Django views for the Veigar cybersecurity agent.

This module provides Django views for displaying security review results
and managing security configurations.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
import json
import logging

from apps.agent.veigar.django_models.security_models import (
    SecurityFramework, SecurityTool, SecurityVulnerability,
    ComplianceIssue, SecurityReview
)
from apps.agent.veigar.django_integration.django_integration import (
    create_security_runtime, load_security_config
)

logger = logging.getLogger(__name__)


class SecurityReviewListView(LoginRequiredMixin, ListView):
    """View for listing security reviews."""
    
    model = SecurityReview
    template_name = 'veigar/security_review_list.html'
    context_object_name = 'security_reviews'
    paginate_by = 10
    
    def get_queryset(self):
        """Get the queryset for the view."""
        queryset = SecurityReview.objects.all().order_by('-created_at')
        
        repository = self.request.GET.get('repository')
        if repository:
            queryset = queryset.filter(repository__icontains=repository)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity_level=severity)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        context['repositories'] = SecurityReview.objects.values_list(
            'repository', flat=True
        ).distinct()
        context['statuses'] = dict(SecurityReview.STATUS_CHOICES)
        context['severities'] = dict(SecurityReview.SEVERITY_LEVELS)
        return context


class SecurityReviewDetailView(LoginRequiredMixin, DetailView):
    """View for displaying security review details."""
    
    model = SecurityReview
    template_name = 'veigar/security_review_detail.html'
    context_object_name = 'security_review'
    
    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        
        security_review = self.get_object()
        vulnerabilities = security_review.vulnerabilities.all()
        context['critical_vulnerabilities'] = vulnerabilities.filter(severity='critical')
        context['high_vulnerabilities'] = vulnerabilities.filter(severity='high')
        context['medium_vulnerabilities'] = vulnerabilities.filter(severity='medium')
        context['low_vulnerabilities'] = vulnerabilities.filter(severity='low')
        
        compliance_issues = security_review.compliance_issues.all()
        frameworks = SecurityFramework.objects.filter(
            complianceissue__in=compliance_issues
        ).distinct()
        
        context['frameworks'] = []
        for framework in frameworks:
            context['frameworks'].append({
                'framework': framework,
                'issues': compliance_issues.filter(framework=framework)
            })
        
        return context


@require_http_methods(["POST"])
@login_required
def trigger_security_review(request):
    """Trigger a security review for a pull request."""
    try:
        data = json.loads(request.body)
        repository = data.get('repository')
        branch = data.get('branch')
        pr_id = data.get('pr_id')
        pr_title = data.get('pr_title', '')
        pr_author = data.get('pr_author', '')
        files = data.get('files', [])
        
        if not repository or not branch or not pr_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields: repository, branch, pr_id'
            }, status=400)
        
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
                for vuln in result.get('vulnerabilities', []):
                    tool, _ = SecurityTool.objects.get_or_create(
                        name=vuln.get('scanner', 'unknown'),
                        defaults={
                            'description': f"Security scanner: {vuln.get('scanner', 'unknown')}",
                            'tool_type': 'static' if vuln.get('scanner') in ['semgrep', 'bandit'] else 'dependency'
                        }
                    )
                    
                    vulnerability = SecurityVulnerability.objects.create(
                        title=vuln.get('title', 'Unknown vulnerability'),
                        description=vuln.get('description', ''),
                        severity=vuln.get('severity', 'medium'),
                        cve=vuln.get('cve'),
                        cwe=vuln.get('cwe'),
                        file_path=vuln.get('file', ''),
                        line_number=vuln.get('line', ''),
                        evidence=vuln.get('evidence', ''),
                        remediation=vuln.get('remediation', ''),
                        tool=tool
                    )
                    
                    security_review.vulnerabilities.add(vulnerability)
                
                for framework_name, framework_data in result.get('compliance', {}).get('frameworks', {}).items():
                    framework, _ = SecurityFramework.objects.get_or_create(
                        name=framework_name,
                        defaults={'description': f"{framework_name} security framework"}
                    )
                    
                    for issue in framework_data.get('issues', []):
                        compliance_issue = ComplianceIssue.objects.create(
                            title=issue.get('title', 'Unknown issue'),
                            description=issue.get('description', ''),
                            severity=issue.get('severity', 'medium'),
                            category=issue.get('category', ''),
                            issue_id=issue.get('id', ''),
                            remediation=issue.get('remediation', ''),
                            framework=framework
                        )
                        
                        security_review.compliance_issues.add(compliance_issue)
                
                security_review.mark_completed(
                    severity_level=result.get('severity_level', 'none'),
                    summary=result.get('security_report', '')
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Security review completed successfully',
                    'review_id': security_review.id,
                    'severity_level': security_review.severity_level
                })
            else:
                security_review.mark_failed(result.get('error', 'Unknown error'))
                return JsonResponse({
                    'status': 'error',
                    'message': f"Security review failed: {result.get('error', 'Unknown error')}",
                    'review_id': security_review.id
                }, status=500)
        
        except Exception as e:
            logger.exception(f"Error running security review: {e}")
            security_review.mark_failed(str(e))
            return JsonResponse({
                'status': 'error',
                'message': f"Error running security review: {str(e)}",
                'review_id': security_review.id
            }, status=500)
    
    except Exception as e:
        logger.exception(f"Error processing security review request: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f"Error processing security review request: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
@login_required
def security_review_status(request, review_id):
    """Get the status of a security review."""
    try:
        security_review = get_object_or_404(SecurityReview, id=review_id)
        
        return JsonResponse({
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
        return JsonResponse({
            'status': 'error',
            'message': f"Error getting security review status: {str(e)}"
        }, status=500)


@require_http_methods(["POST"])
@login_required
def approve_security_review(request, review_id):
    """Approve a security review."""
    try:
        security_review = get_object_or_404(SecurityReview, id=review_id)
        
        if security_review.status != 'completed':
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot approve a security review that is not completed'
            }, status=400)
        
        if not security_review.is_compliant:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot approve a security review that is not compliant'
            }, status=400)
        
        
        return JsonResponse({
            'status': 'success',
            'message': 'Security review approved successfully',
            'review_id': security_review.id
        })
    
    except Exception as e:
        logger.exception(f"Error approving security review: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f"Error approving security review: {str(e)}"
        }, status=500)


@require_http_methods(["POST"])
@login_required
def reject_security_review(request, review_id):
    """Reject a security review."""
    try:
        security_review = get_object_or_404(SecurityReview, id=review_id)
        
        if security_review.status != 'completed':
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot reject a security review that is not completed'
            }, status=400)
        
        
        return JsonResponse({
            'status': 'success',
            'message': 'Security review rejected successfully',
            'review_id': security_review.id
        })
    
    except Exception as e:
        logger.exception(f"Error rejecting security review: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f"Error rejecting security review: {str(e)}"
        }, status=500)
