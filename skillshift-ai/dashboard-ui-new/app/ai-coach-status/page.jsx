"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Server,
  Database,
  Shield,
  Wifi,
  HardDrive,
  Cpu,
  Activity,
  AlertTriangle,
  CheckCircle,
  Settings,
  Brain,
  Camera,
  MessageCircle,
  Eye,
  RefreshCw,
  Power,
  Trash2,
} from "lucide-react";

export default function AiCoachStatusPage() {
  const [selectedSystem, setSelectedSystem] = useState(null);

  const systems = [
    {
      id: "SYS-001",
      name: "SCREENSHOT PROCESSOR",
      type: "Image Processing",
      status: "online",
      health: 98,
      cpu: 45,
      memory: 67,
      storage: 34,
      uptime: "247 days",
      location: "Processing Node 1",
      lastMaintenance: "2025-01-15",
      errors: [],
    },
    {
      id: "SYS-002",
      name: "PLAYER HISTORY DB",
      type: "Database",
      status: "online",
      health: 95,
      cpu: 72,
      memory: 84,
      storage: 78,
      uptime: "189 days",
      location: "Database Cluster",
      lastMaintenance: "2025-01-10",
      errors: [],
    },
    {
      id: "SYS-003",
      name: "FEEDBACK GENERATOR",
      type: "AI Model",
      status: "warning",
      health: 87,
      cpu: 89,
      memory: 92,
      storage: 45,
      uptime: "156 days",
      location: "LLM Cluster",
      lastMaintenance: "2025-01-05",
      errors: ["High Memory Usage", "Response Time Elevated"],
    },
    {
      id: "SYS-004",
      name: "FEEDBACK DELIVERY MODULE",
      type: "Communication",
      status: "online",
      health: 92,
      cpu: 38,
      memory: 52,
      storage: 23,
      uptime: "203 days",
      location: "Communication Hub",
      lastMaintenance: "2025-01-12",
      errors: [],
    },
    {
      id: "SYS-005",
      name: "YOLO DETECTION SERVICE",
      type: "AI Detection",
      status: "maintenance",
      health: 76,
      cpu: 15,
      memory: 28,
      storage: 89,
      uptime: "0 days",
      location: "Detection Cluster",
      lastMaintenance: "2025-01-17",
      errors: ["System Under Maintenance"],
    },
    {
      id: "SYS-006",
      name: "OCR PROCESSING ENGINE",
      type: "Text Recognition",
      status: "online",
      health: 94,
      cpu: 76,
      memory: 68,
      storage: 42,
      uptime: "134 days",
      location: "OCR Cluster",
      lastMaintenance: "2025-01-08",
      errors: [],
    },
    {
      id: "SYS-007",
      name: "BEHAVIORAL ANALYSIS",
      type: "AI Analysis",
      status: "warning",
      health: 82,
      cpu: 85,
      memory: 89,
      storage: 56,
      uptime: "98 days",
      location: "Analysis Node 2",
      lastMaintenance: "2025-01-03",
      errors: ["OCR Confidence < Threshold", "Model Timeout Detected"],
    },
    {
      id: "SYS-008",
      name: "MEDAL DETECTOR",
      type: "AI Detection",
      status: "online",
      health: 91,
      cpu: 52,
      memory: 71,
      storage: 38,
      uptime: "167 days",
      location: "Detection Cluster",
      lastMaintenance: "2025-01-14",
      errors: [],
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "online":
        return "bg-primary text-primary-foreground";
      case "warning":
        return "bg-secondary text-secondary-foreground";
      case "maintenance":
        return "bg-muted text-muted-foreground";
      case "offline":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "online":
        return <CheckCircle className="w-4 h-4" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4" />;
      case "maintenance":
        return <Settings className="w-4 h-4" />;
      case "offline":
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getSystemIcon = (type) => {
    switch (type) {
      case "Image Processing":
        return <Camera className="w-6 h-6" />;
      case "Database":
        return <Database className="w-6 h-6" />;
      case "AI Model":
        return <Brain className="w-6 h-6" />;
      case "Communication":
        return <MessageCircle className="w-6 h-6" />;
      case "AI Detection":
        return <Eye className="w-6 h-6" />;
      case "Text Recognition":
        return <HardDrive className="w-6 h-6" />;
      case "AI Analysis":
        return <Activity className="w-6 h-6" />;
      default:
        return <Server className="w-6 h-6" />;
    }
  };

  const getHealthColor = (health) => {
    if (health >= 95) return "text-foreground";
    if (health >= 85) return "text-foreground";
    if (health >= 70) return "text-muted-foreground";
    return "text-muted-foreground";
  };

  const handleRestartSystem = (systemId) => {
    console.log(`Restarting system: ${systemId}`);
    // Implementation would trigger system restart
  };

  const handleClearCache = (systemId) => {
    console.log(`Clearing cache for system: ${systemId}`);
    // Implementation would clear system cache
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-wider">
            AI COACH STATUS
          </h1>
          <p className="text-sm text-muted-foreground">
            Monitor AI system health and performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh All
          </Button>
          <Button variant="outline">System Health Check</Button>
        </div>
      </div>

      {/* System Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  SYSTEMS ONLINE
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  6/8
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  WARNINGS
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  2
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  AVG HEALTH
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  89.4%
                </p>
              </div>
              <Activity className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  MAINTENANCE
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  1
                </p>
              </div>
              <Settings className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Systems Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {systems.map((system) => (
          <Card
            key={system.id}
            className="bg-card border-border hover:border-primary/50 transition-colors cursor-pointer"
            onClick={() => setSelectedSystem(system)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getSystemIcon(system.type)}
                  <div>
                    <CardTitle className="text-sm font-bold text-foreground tracking-wider">
                      {system.name}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {system.type}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(system.status)}
                  <Badge className={getStatusColor(system.status)}>
                    {system.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  SYSTEM HEALTH
                </span>
                <span
                  className={`text-sm font-bold font-mono ${getHealthColor(
                    system.health
                  )}`}
                >
                  {system.health}%
                </span>
              </div>
              <Progress value={system.health} className="h-2" />

              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <div className="text-muted-foreground mb-1">CPU</div>
                  <div className="text-foreground font-mono">{system.cpu}%</div>
                  <div className="w-full bg-muted rounded-full h-1 mt-1">
                    <div
                      className="bg-primary h-1 rounded-full transition-all duration-300"
                      style={{ width: `${system.cpu}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">MEMORY</div>
                  <div className="text-foreground font-mono">
                    {system.memory}%
                  </div>
                  <div className="w-full bg-muted rounded-full h-1 mt-1">
                    <div
                      className="bg-primary h-1 rounded-full transition-all duration-300"
                      style={{ width: `${system.memory}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">STORAGE</div>
                  <div className="text-foreground font-mono">
                    {system.storage}%
                  </div>
                  <div className="w-full bg-muted rounded-full h-1 mt-1">
                    <div
                      className="bg-primary h-1 rounded-full transition-all duration-300"
                      style={{ width: `${system.storage}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="space-y-1 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Uptime:</span>
                  <span className="text-foreground font-mono">
                    {system.uptime}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Location:</span>
                  <span className="text-foreground">{system.location}</span>
                </div>
              </div>

              {system.errors.length > 0 && (
                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground font-medium">
                    ERRORS:
                  </div>
                  {system.errors.map((error, index) => (
                    <div
                      key={index}
                      className="text-xs text-muted-foreground bg-muted/50 p-1 rounded"
                    >
                      {error}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRestartSystem(system.id);
                  }}
                  className="flex-1"
                >
                  <Power className="w-3 h-3 mr-1" />
                  Restart
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearCache(system.id);
                  }}
                  className="flex-1"
                >
                  <Trash2 className="w-3 h-3 mr-1" />
                  Clear Cache
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System Detail Modal */}
      {selectedSystem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="bg-card border-border w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                {getSystemIcon(selectedSystem.type)}
                <div>
                  <CardTitle className="text-xl font-bold text-foreground tracking-wider">
                    {selectedSystem.name}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {selectedSystem.id} • {selectedSystem.type}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                onClick={() => setSelectedSystem(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      SYSTEM STATUS
                    </h3>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(selectedSystem.status)}
                      <Badge className={getStatusColor(selectedSystem.status)}>
                        {selectedSystem.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      SYSTEM INFORMATION
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Type:</span>
                        <span className="text-foreground">
                          {selectedSystem.type}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Location:</span>
                        <span className="text-foreground">
                          {selectedSystem.location}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Uptime:</span>
                        <span className="text-foreground font-mono">
                          {selectedSystem.uptime}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          Last Maintenance:
                        </span>
                        <span className="text-foreground font-mono">
                          {selectedSystem.lastMaintenance}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          Health Score:
                        </span>
                        <span
                          className={`font-mono ${getHealthColor(
                            selectedSystem.health
                          )}`}
                        >
                          {selectedSystem.health}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      RESOURCE USAGE
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-muted-foreground">
                            CPU Usage
                          </span>
                          <span className="text-foreground font-mono">
                            {selectedSystem.cpu}%
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all duration-300"
                            style={{ width: `${selectedSystem.cpu}%` }}
                          ></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-muted-foreground">
                            Memory Usage
                          </span>
                          <span className="text-foreground font-mono">
                            {selectedSystem.memory}%
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all duration-300"
                            style={{ width: `${selectedSystem.memory}%` }}
                          ></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-muted-foreground">
                            Storage Usage
                          </span>
                          <span className="text-foreground font-mono">
                            {selectedSystem.storage}%
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all duration-300"
                            style={{ width: `${selectedSystem.storage}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {selectedSystem.errors.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                    SYSTEM ERRORS
                  </h3>
                  <div className="space-y-2">
                    {selectedSystem.errors.map((error, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 p-2 bg-muted/50 rounded"
                      >
                        <AlertTriangle className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">
                          {error}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t border-border">
                <Button onClick={() => handleRestartSystem(selectedSystem.id)}>
                  <Power className="w-4 h-4 mr-2" />
                  Restart System
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleClearCache(selectedSystem.id)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear Cache
                </Button>
                <Button variant="outline">View Logs</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
