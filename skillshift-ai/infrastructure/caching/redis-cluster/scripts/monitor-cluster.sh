#!/bin/bash

# Redis Cluster Monitoring Script
# Continuously monitors cluster health and performance

echo "🔍 Redis Cluster Monitor Starting..."
echo "=================================="

while true; do
    echo ""
    echo "📊 Cluster Status - $(date)"
    echo "=========================="
    
    # Check cluster info
    echo "🔧 Cluster Info:"
    redis-cli -h redis-node-1 -p 6379 -a mlbb-redis-cluster-2025 --no-auth-warning cluster info | grep -E "(cluster_state|cluster_slots_assigned|cluster_known_nodes)"
    
    echo ""
    echo "📈 Cluster Nodes:"
    redis-cli -h redis-node-1 -p 6379 -a mlbb-redis-cluster-2025 --no-auth-warning cluster nodes | awk '{print $1" "$2" "$3" "$8}'
    
    echo ""
    echo "💾 Memory Usage:"
    for port in 7000 7001 7002 7003 7004 7005; do
        memory=$(redis-cli -h localhost -p $port -a mlbb-redis-cluster-2025 --no-auth-warning info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        echo "  Node $port: $memory"
    done
    
    echo ""
    echo "⚡ Performance Stats:"
    ops=$(redis-cli -h redis-node-1 -p 6379 -a mlbb-redis-cluster-2025 --no-auth-warning info stats | grep instantaneous_ops_per_sec | cut -d: -f2 | tr -d '\r')
    echo "  Operations/sec: $ops"
    
    connections=$(redis-cli -h redis-node-1 -p 6379 -a mlbb-redis-cluster-2025 --no-auth-warning info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
    echo "  Connected clients: $connections"
    
    # Check for any failing nodes
    failing_nodes=$(redis-cli -h redis-node-1 -p 6379 -a mlbb-redis-cluster-2025 --no-auth-warning cluster nodes | grep -c "fail")
    if [ "$failing_nodes" -gt 0 ]; then
        echo "⚠️  WARNING: $failing_nodes node(s) are failing!"
    else
        echo "✅ All nodes are healthy"
    fi
    
    echo "=================================="
    sleep 30
done
