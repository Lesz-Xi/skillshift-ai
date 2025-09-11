#!/bin/bash

# MLBB Coach AI - Service Monitoring Script
# This script monitors the health and performance of microservices

set -e

echo "📊 MLBB Coach AI - Service Monitoring"
echo "====================================="

# Configuration
NAMESPACE="mlbb-coach-ai"
SERVICES=("api-gateway" "ocr-service" "detection-service" "analysis-service")
PORTS=(8000 8001 8002 8003)

# Check deployment type
if command -v kubectl &> /dev/null && kubectl get namespace "$NAMESPACE" &> /dev/null; then
    DEPLOYMENT_TYPE="kubernetes"
    echo "🔍 Detected Kubernetes deployment"
elif command -v docker-compose &> /dev/null && docker-compose ps &> /dev/null 2>&1; then
    DEPLOYMENT_TYPE="docker-compose"
    echo "🐳 Detected Docker Compose deployment"
else
    echo "❌ No deployment detected. Please deploy first."
    exit 1
fi

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    
    if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        # Kubernetes health check
        local pod_status=$(kubectl get pods -n "$NAMESPACE" -l app="$service_name" -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
        local ready_status=$(kubectl get pods -n "$NAMESPACE" -l app="$service_name" -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
        
        if [ "$pod_status" = "Running" ] && [ "$ready_status" = "True" ]; then
            echo "✅ $service_name: Running and Ready"
            
            # Try to get metrics if available
            if kubectl port-forward service/"$service_name" "$port:$port" -n "$NAMESPACE" &> /dev/null &
            then
                local pf_pid=$!
                sleep 2
                
                if curl -s "http://localhost:$port/health" &> /dev/null; then
                    echo "   🔗 Health endpoint: OK"
                    
                    # Get metrics if available
                    local metrics=$(curl -s "http://localhost:$port/metrics" 2>/dev/null || echo "")
                    if [ -n "$metrics" ]; then
                        echo "   📈 Metrics: Available"
                    fi
                else
                    echo "   ⚠️  Health endpoint: Not responding"
                fi
                
                kill $pf_pid 2>/dev/null || true
            fi
        else
            echo "❌ $service_name: $pod_status (Ready: $ready_status)"
        fi
        
    elif [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        # Docker Compose health check
        local container_status=$(docker-compose ps -q "$service_name" | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        local health_status=$(docker-compose ps -q "$service_name" | xargs docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no_health_check{{end}}' 2>/dev/null || echo "unknown")
        
        if [ "$container_status" = "running" ]; then
            echo "✅ $service_name: Running ($health_status)"
            
            # Direct health check
            if curl -s "http://localhost:$port/health" &> /dev/null; then
                echo "   🔗 Health endpoint: OK"
                
                # Get metrics if available
                local metrics=$(curl -s "http://localhost:$port/metrics" 2>/dev/null || echo "")
                if [ -n "$metrics" ]; then
                    echo "   📈 Metrics: Available"
                fi
            else
                echo "   ⚠️  Health endpoint: Not responding"
            fi
        else
            echo "❌ $service_name: $container_status"
        fi
    fi
}

# Function to get resource usage
get_resource_usage() {
    echo ""
    echo "📊 Resource Usage:"
    echo "=================="
    
    if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        # Kubernetes resource usage
        echo "Memory and CPU usage by pod:"
        kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics server not available"
        
        echo ""
        echo "Node resource usage:"
        kubectl top nodes 2>/dev/null || echo "Metrics server not available"
        
    elif [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        # Docker Compose resource usage
        echo "Container resource usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker-compose ps -q) 2>/dev/null || echo "Unable to get container stats"
    fi
}

# Function to show logs
show_recent_logs() {
    echo ""
    echo "📝 Recent Logs (last 10 lines per service):"
    echo "==========================================="
    
    for service in "${SERVICES[@]}"; do
        echo ""
        echo "--- $service ---"
        
        if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
            kubectl logs --tail=10 deployment/"$service" -n "$NAMESPACE" 2>/dev/null || echo "No logs available"
        elif [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
            docker-compose logs --tail=10 "$service" 2>/dev/null || echo "No logs available"
        fi
    done
}

# Main monitoring loop
echo ""
echo "🔍 Checking service health..."
echo "============================="

for i in "${!SERVICES[@]}"; do
    check_service_health "${SERVICES[$i]}" "${PORTS[$i]}"
    echo ""
done

# Show resource usage
get_resource_usage

# Show recent logs
show_recent_logs

echo ""
echo "🎯 Summary:"
echo "==========="

# Count healthy services
healthy_count=0
for i in "${!SERVICES[@]}"; do
    if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        pod_status=$(kubectl get pods -n "$NAMESPACE" -l app="${SERVICES[$i]}" -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
        ready_status=$(kubectl get pods -n "$NAMESPACE" -l app="${SERVICES[$i]}" -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
        
        if [ "$pod_status" = "Running" ] && [ "$ready_status" = "True" ]; then
            ((healthy_count++))
        fi
    elif [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        container_status=$(docker-compose ps -q "${SERVICES[$i]}" | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        
        if [ "$container_status" = "running" ]; then
            ((healthy_count++))
        fi
    fi
done

echo "✅ Healthy services: $healthy_count/${#SERVICES[@]}"

if [ $healthy_count -eq ${#SERVICES[@]} ]; then
    echo "🎉 All services are healthy!"
else
    echo "⚠️  Some services need attention"
fi

echo ""
echo "🔧 Useful commands:"
if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
    echo "   View pods: kubectl get pods -n $NAMESPACE"
    echo "   Describe pod: kubectl describe pod [pod-name] -n $NAMESPACE"
    echo "   View logs: kubectl logs -f deployment/[service-name] -n $NAMESPACE"
    echo "   Port forward: kubectl port-forward service/[service-name] [port]:[port] -n $NAMESPACE"
elif [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
    echo "   View containers: docker-compose ps"
    echo "   View logs: docker-compose logs -f [service-name]"
    echo "   Restart service: docker-compose restart [service-name]"
    echo "   Scale service: docker-compose up -d --scale [service-name]=3"
fi
