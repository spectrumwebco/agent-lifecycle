#!/bin/bash
echo "Removing cert-manager Helm release..."
helm uninstall cert-manager -n cert-manager 2>/dev/null || true

echo "Deleting ClusterRoles..."
kubectl delete clusterrole cert-manager-cluster-view 2>/dev/null || true
kubectl delete clusterrole cert-manager-cainjector 2>/dev/null || true
kubectl delete clusterrole cert-manager-controller-issuers 2>/dev/null || true
kubectl delete clusterrole cert-manager-controller-clusterissuers 2>/dev/null || true
kubectl delete clusterrole cert-manager-controller-certificates 2>/dev/null || true
kubectl delete clusterrole cert-manager-controller-orders 2>/dev/null || true
kubectl delete clusterrole cert-manager-controller-challenges 2>/dev/null || true
kubectl delete clusterrole cert-manager-view 2>/dev/null || true
kubectl delete clusterrole cert-manager-edit 2>/dev/null || true
kubectl delete clusterrole cert-manager-webhook:webhook-requester 2>/dev/null || true

echo "Deleting ClusterRoleBindings..."
kubectl get clusterrolebindings | grep cert-manager | awk '{print }' | xargs -r kubectl delete clusterrolebinding

echo "Deleting CRDs..."
kubectl get crd | grep cert-manager.io | awk '{print }' | xargs -r kubectl delete crd

echo "Deleting cert-manager namespace..."
kubectl delete namespace cert-manager --wait=false

echo "Cleanup completed"
