#!/bin/bash

# MLBB Coach AI - Kubernetes Deployment Script
# This script deploys the microservices architecture to Kubernetes

set -e

echo "🚀 MLBB Coach AI - Microservices Deployment (Kubernetes)"
echo "========================================================"

# Configuration
K8S_DIR="$(dirname "$0")/../k8s"
ISTIO_DIR="$(dirname "$0")/../istio"
NAMESPACE="mlbb-coach-ai"

# Check if kubectl is installed and configured
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "🔧 Creating namespace..."
kubectl apply -f "$K8S_DIR/namespace.yaml"

echo "🔑 Creating secrets..."
echo "⚠️  Please update the secrets in $K8S_DIR/secrets.yaml with your actual values"
read -p "Press Enter to continue after updating secrets..."
kubectl apply -f "$K8S_DIR/secrets.yaml"

echo "📦 Deploying Redis..."
kubectl apply -f "$K8S_DIR/redis-deployment.yaml"

echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/redis -n "$NAMESPACE"

echo "🧠 Deploying OCR Service..."
kubectl apply -f "$K8S_DIR/ocr-service-deployment.yaml"

echo "🔍 Deploying Detection Service..."
kubectl apply -f "$K8S_DIR/detection-service-deployment.yaml"

echo "📊 Deploying Analysis Service..."
kubectl apply -f "$K8S_DIR/analysis-service-deployment.yaml"

echo "🌐 Deploying API Gateway..."
kubectl apply -f "$K8S_DIR/api-gateway-deployment.yaml"

echo "⏳ Waiting for all services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ocr-service -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/detection-service -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/analysis-service -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway -n "$NAMESPACE"

# Optional: Deploy Istio service mesh
if command -v istioctl &> /dev/null; then
    echo "🕸️  Deploying Istio service mesh..."
    
    # Check if Istio is installed
    if kubectl get namespace istio-system &> /dev/null; then
        echo "📡 Configuring Istio gateway and virtual service..."
        kubectl apply -f "$ISTIO_DIR/gateway.yaml"
        kubectl apply -f "$ISTIO_DIR/destination-rules.yaml"
        
        # Enable Istio sidecar injection
        kubectl label namespace "$NAMESPACE" istio-injection=enabled --overwrite
        
        # Restart deployments to inject sidecars
        kubectl rollout restart deployment -n "$NAMESPACE"
        
        echo "⏳ Waiting for rollout to complete..."
        kubectl rollout status deployment/api-gateway -n "$NAMESPACE"
        kubectl rollout status deployment/ocr-service -n "$NAMESPACE"
        kubectl rollout status deployment/detection-service -n "$NAMESPACE"
        kubectl rollout status deployment/analysis-service -n "$NAMESPACE"
    else
        echo "⚠️  Istio is not installed. Skipping service mesh configuration."
    fi
else
    echo "⚠️  istioctl not found. Skipping Istio configuration."
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service Status:"
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get services -n "$NAMESPACE"

echo ""
echo "🔧 Useful commands:"
echo "   View pods: kubectl get pods -n $NAMESPACE"
echo "   View logs: kubectl logs -f deployment/[service-name] -n $NAMESPACE"
echo "   Port forward API: kubectl port-forward service/api-gateway 8000:8000 -n $NAMESPACE"
echo "   Scale service: kubectl scale deployment [service-name] --replicas=5 -n $NAMESPACE"
echo "   Delete all: kubectl delete namespace $NAMESPACE"

# Get external IP if LoadBalancer is used
EXTERNAL_IP=$(kubectl get service api-gateway -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$EXTERNAL_IP" ]; then
    echo ""
    echo "🌐 External Access:"
    echo "   API Gateway: http://$EXTERNAL_IP:8000"
else
    echo ""
    echo "🔗 Local Access (use port-forward):"
    echo "   kubectl port-forward service/api-gateway 8000:8000 -n $NAMESPACE"
fi
