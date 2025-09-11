"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import ClientOnly from "@/components/ClientOnly";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Upload,
  Image,
  FileText,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  Download,
  X,
  Brain,
  Target,
  Zap,
  Camera,
  Award,
  Loader2,
  Activity,
  TrendingUp,
  RefreshCw,
  WifiOff,
} from "lucide-react";

export default function ScreenshotAnalysisPage() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [processingFiles, setProcessingFiles] = useState(new Set());
  const [analysisResults, setAnalysisResults] = useState({});
  const [selectedResultFile, setSelectedResultFile] = useState(null);
  const [showResultModal, setShowResultModal] = useState(false);
  const [playerIGN, setPlayerIGN] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("checking");
  const [lastHealthCheck, setLastHealthCheck] = useState(null);
  const fileInputRef = useRef(null);
  const [heroOverride, setHeroOverride] = useState("");

  // Allow the client-side analysis timeout to be configured via env.
  // Defaults to 5 minutes to avoid premature AbortError when server-side analysis takes longer.
  const CLIENT_ANALYZE_TIMEOUT_MS = Number(
    process.env.NEXT_PUBLIC_ANALYZE_TIMEOUT_MS ?? "300000"
  );

  // Backend health checking
  const checkBackendHealth = useCallback(async () => {
    try {
      const response = await fetch("/api/health");
      const healthData = await response.json();

      if (response.ok && healthData.status === "healthy") {
        setIsConnected(true);
        setConnectionStatus("healthy");
        setLastHealthCheck(new Date());
      } else {
        setIsConnected(false);
        setConnectionStatus("degraded");
      }
    } catch (error) {
      console.error("Health check failed:", error);
      setIsConnected(false);
      setConnectionStatus("offline");
    }
  }, []);

  // Check backend health on mount and periodically
  useEffect(() => {
    // Always do an immediate check on mount or when analyzer stops
    checkBackendHealth();
    // While analyzing, skip periodic checks to reduce backend noise
    if (isAnalyzing) return;
    const interval = setInterval(checkBackendHealth, 10000); // every 10s when idle
    return () => clearInterval(interval);
  }, [checkBackendHealth, isAnalyzing]);

  const handleFileUpload = useCallback((files) => {
    const newFiles = Array.from(files).map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      uploadedAt: new Date(),
      status: "uploaded",
    }));
    setUploadedFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const files = e.dataTransfer.files;
      handleFileUpload(files);
    },
    [handleFileUpload]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  const removeFile = (fileId) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    setProcessingFiles((prev) => {
      const newSet = new Set(prev);
      newSet.delete(fileId);
      return newSet;
    });
  };

  const handleAnalyze = async () => {
    if (uploadedFiles.length < 2) {
      alert("Please upload at least 2 screenshots to begin analysis");
      return;
    }

    setIsAnalyzing(true);

    try {
      // Generate a session id to merge multi-screenshot data on the backend
      const sessionId = (typeof crypto !== "undefined" && crypto.randomUUID)
        ? crypto.randomUUID()
        : Math.random().toString(36).slice(2);
      // Process each uploaded file SEQUENTIALLY to avoid CPU contention
      const results = [];
      for (const fileData of uploadedFiles) {
        // Mark as processing
        setProcessingFiles((prev) => new Set(prev).add(fileData.id));

        const formData = new FormData();
        formData.append("file", fileData.file);
        formData.append("ign", playerIGN || "Lesz XVII");
        formData.append("session_id", sessionId);
        if (heroOverride.trim()) {
          formData.append("hero_override", heroOverride.trim());
        }

        const response = await fetch("/api/analyze", {
          method: "POST",
          body: formData,
          // Use a configurable timeout; ensure it is >= server timeout
          signal: AbortSignal.timeout(CLIENT_ANALYZE_TIMEOUT_MS),
        });

        if (!response.ok) {
          throw new Error(
            `Analysis failed for ${fileData.name}: ${response.statusText}`
          );
        }

        const result = await response.json();

        // Normalize various backend/proxy result shapes into the UI schema
        const normalizeResult = (r) => {
          const hero =
            r.hero ||
            r?.analysis?.performance?.hero ||
            r?.match_data?.hero ||
            "N/A";

          const kda =
            r.kda ||
            r?.analysis?.performance?.kda ||
            r?.match_data?.kda ||
            "N/A";

          const gpm =
            r.gpm ||
            r?.analysis?.performance?.gpm ||
            r?.match_data?.gpm ||
            "N/A";

          const role = r.role || r?.analysis?.performance?.role || "N/A";

          let confidence = 0;
          if (typeof r?.confidence_score === "number") {
            confidence = r.confidence_score; // already 0-1
          } else if (
            typeof r?.analysis?.quality?.overall_confidence === "number"
          ) {
            // convert 0-100 to 0-1
            confidence = r.analysis.quality.overall_confidence / 100;
          } else if (typeof r?.diagnostics?.confidence_score === "number") {
            confidence = r.diagnostics.confidence_score;
          }
          if (!Number.isFinite(confidence)) confidence = 0;
          confidence = Math.max(0, Math.min(1, confidence));

          const feedbackArray = Array.isArray(r?.coaching_feedback)
            ? r.coaching_feedback
            : Array.isArray(r?.analysis?.statistical_feedback)
            ? r.analysis.statistical_feedback.map((f) =>
                typeof f === "string" ? f : f?.message || JSON.stringify(f)
              )
            : [];

          return {
            success: r?.success ?? true,
            confidence_score: confidence,
            hero,
            kda,
            gpm,
            role,
            coaching_feedback: feedbackArray,
            // keep full raw for debugging/advanced UI
            __raw: r,
          };
        };

        const normalized = normalizeResult(result);
        results.push({ fileId: fileData.id, fileName: fileData.name, result: normalized });

        // Mark as analyzed
        setUploadedFiles((prev) =>
          prev.map((f) => (f.id === fileData.id ? { ...f, status: "analyzed" } : f))
        );
        setProcessingFiles((prev) => {
          const next = new Set(prev);
          next.delete(fileData.id);
          return next;
        });
      }

      // Store results
      const resultsMap = {};
      results.forEach(({ fileId, result }) => {
        resultsMap[fileId] = result; // already normalized
      });
      setAnalysisResults(resultsMap);

      // Show results modal for the first file
      if (results.length > 0) {
        setSelectedResultFile(results[0].fileId);
        setShowResultModal(true);
      }

      // Update file statuses
      setUploadedFiles((prev) =>
        prev.map((file) => ({
          ...file,
          status: "analyzed",
        }))
      );
    } catch (error) {
      if (error?.name === "AbortError") {
        console.warn("Analysis request timed out on the client");
        alert(
          "Analysis took longer than expected and was canceled. You can increase NEXT_PUBLIC_ANALYZE_TIMEOUT_MS and retry."
        );
      } else {
        console.error("Analysis failed:", error);
        alert(`Analysis failed: ${error.message}`);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "analyzed":
        return "bg-muted text-muted-foreground";
      case "processing":
        return "bg-primary text-primary-foreground";
      case "queued":
        return "bg-secondary text-secondary-foreground";
      case "uploaded":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "analyzed":
        return <CheckCircle className="w-4 h-4" />;
      case "processing":
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case "queued":
        return <Clock className="w-4 h-4" />;
      case "uploaded":
        return <Upload className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <>
      <style jsx>{`
        @keyframes wave {
          0%,
          40%,
          100% {
            transform: translateY(0);
          }
          20% {
            transform: translateY(-10px);
          }
        }

        .wave-text {
          display: inline-block;
        }

        .wave-text span {
          display: inline-block;
          animation: wave 2.5s ease-in-out infinite;
        }

        .wave-text span:nth-child(1) {
          animation-delay: 0s;
        }
        .wave-text span:nth-child(2) {
          animation-delay: 0.15s;
        }
        .wave-text span:nth-child(3) {
          animation-delay: 0.3s;
        }
        .wave-text span:nth-child(4) {
          animation-delay: 0.45s;
        }
        .wave-text span:nth-child(5) {
          animation-delay: 0.6s;
        }
        .wave-text span:nth-child(6) {
          animation-delay: 0.75s;
        }
        .wave-text span:nth-child(7) {
          animation-delay: 0.9s;
        }
        .wave-text span:nth-child(8) {
          animation-delay: 1.05s;
        }
        .wave-text span:nth-child(9) {
          animation-delay: 1.2s;
        }
        .wave-text span:nth-child(10) {
          animation-delay: 1.35s;
        }
        .wave-text span:nth-child(11) {
          animation-delay: 1.5s;
        }
        .wave-text span:nth-child(12) {
          animation-delay: 1.65s;
        }
        .wave-text span:nth-child(13) {
          animation-delay: 1.8s;
        }
        .wave-text span:nth-child(14) {
          animation-delay: 1.95s;
        }
        .wave-text span:nth-child(15) {
          animation-delay: 2.1s;
        }
        .wave-text span:nth-child(16) {
          animation-delay: 2.25s;
        }
        .wave-text span:nth-child(17) {
          animation-delay: 2.4s;
        }
        .wave-text span:nth-child(18) {
          animation-delay: 2.55s;
        }
        .wave-text span:nth-child(19) {
          animation-delay: 2.7s;
        }
        .wave-text span:nth-child(20) {
          animation-delay: 2.85s;
        }
        .wave-text span:nth-child(21) {
          animation-delay: 3s;
        }
      `}</style>

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Screenshot Analysis
            </h1>
            <p className="text-muted-foreground">
              Upload MLBB screenshots for instant performance analysis • KDA
              Detection • Medal Recognition • Hero Identification
            </p>
          </div>
          <div className="flex gap-2">
            <Badge
              variant="outline"
              className={
                connectionStatus === "healthy"
                  ? "bg-green-50 text-green-700 border-green-200"
                  : connectionStatus === "checking"
                  ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                  : "bg-red-50 text-red-700 border-red-200"
              }
            >
              {connectionStatus === "healthy" ? (
                <CheckCircle className="w-4 h-4 mr-1" />
              ) : connectionStatus === "checking" ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <AlertCircle className="w-4 h-4 mr-1" />
              )}
              Backend {connectionStatus}
              {lastHealthCheck &&
                connectionStatus === "healthy" &&
                ` (${Math.floor((new Date() - lastHealthCheck) / 1000)}s ago)`}
            </Badge>
            <Badge variant="outline" className="bg-muted text-muted-foreground">
              {Object.keys(analysisResults).length} Analyzed
            </Badge>
            <Badge variant="outline" className="bg-muted text-muted-foreground">
              {processingFiles.size} Processing
            </Badge>
            <Badge variant="outline" className="bg-muted text-muted-foreground">
              0 Queued
            </Badge>
          </div>
        </div>

        {/* Connection Status - Only show when there's an issue */}
        {!isConnected && (
          <Card className="bg-red-50/50 border-red-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <WifiOff className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="font-medium text-red-700">
                      Backend Connection Issue
                    </p>
                    <p className="text-sm text-red-600">
                      Analysis services are {connectionStatus}. Some features
                      may be limited.
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={checkBackendHealth}
                    className="border-red-200 text-red-700 hover:bg-red-50"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Reconnect
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-red-200 text-red-700 hover:bg-red-50"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reset Queue
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Player Configuration - Centered */}
        <Card className="bg-card border-border">
          <CardHeader className="text-center">
            <CardTitle className="text-lg font-semibold text-foreground flex items-center justify-center gap-2">
              <Target className="w-5 h-5" />
              Player Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="w-full max-w-md space-y-6">
              <div className="text-center">
                <Label
                  htmlFor="ign"
                  className="text-sm font-medium text-foreground"
                >
                  In-Game Name (IGN)
                </Label>
                <Input
                  id="ign"
                  placeholder="Enter your MLBB in-game name..."
                  value={playerIGN}
                  onChange={(e) => setPlayerIGN(e.target.value)}
                  className="mt-1 text-center"
                />
                <div className="flex items-center justify-center gap-2 mt-2">
                  <CheckCircle className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    Required for player profile mapping and MVP/medal detection
                    accuracy
                  </span>
                  <Badge
                    variant="outline"
                    className="bg-muted text-muted-foreground text-xs"
                  >
                    Saved automatically
                  </Badge>
                </div>
              </div>
              <div className="text-center">
                <Label htmlFor="heroOverride" className="text-sm font-medium text-foreground">
                  Optional Hero Override
                </Label>
                <Input
                  id="heroOverride"
                  placeholder="e.g., Kagura"
                  value={heroOverride}
                  onChange={(e) => setHeroOverride(e.target.value)}
                  className="mt-1 text-center"
                />
                <div className="flex items-center justify-center gap-2 mt-2">
                  <Badge variant="outline" className="bg-muted text-muted-foreground text-xs">
                    Use to lock hero when OCR misreads
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Upload Section */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Upload Screenshots
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <Upload className="w-8 h-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-lg font-medium text-foreground">
                    Drop Screenshots Here or Click to Browse
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Supports PNG, JPG, JPEG • Post-match screens, KDA displays,
                    medal ceremonies
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Unique IDs generated • No phantom entries • Backend
                    synchronized
                  </p>
                </div>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
              />
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="mt-6 space-y-3">
                <h3 className="font-medium text-foreground">
                  Uploaded Files ({uploadedFiles.length}/2 minimum required)
                </h3>
                <div className="space-y-2">
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border"
                    >
                      <div className="flex items-center gap-3">
                        <Image className="w-5 h-5 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            {file.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {(file.size / 1024 / 1024).toFixed(2)} MB •{" "}
                            {file.uploadedAt.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={getStatusColor(file.status)}
                        >
                          {getStatusIcon(file.status)}
                          <span className="ml-1">{file.status}</span>
                        </Badge>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFile(file.id)}
                          className="w-8 h-8"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Analysis Section - Centered - Only show when 2+ files uploaded */}
        {uploadedFiles.length >= 2 && (
          <Card className="bg-card border-border">
            <CardContent className="p-8">
              <div className="flex flex-col items-center justify-center space-y-6">
                {!isAnalyzing ? (
                  <Button
                    onClick={handleAnalyze}
                    className="px-8 py-3 text-lg font-semibold"
                    size="lg"
                    disabled={!isConnected}
                  >
                    <Brain className="w-5 h-5 mr-2" />
                    Analyze Screenshots
                    {!isConnected && (
                      <span className="ml-2 text-sm opacity-70">
                        (Backend {connectionStatus})
                      </span>
                    )}
                  </Button>
                ) : (
                  <div className="text-center">
                    <div className="wave-text text-2xl font-bold text-foreground mb-4">
                      <span>A</span>
                      <span>g</span>
                      <span>e</span>
                      <span>n</span>
                      <span>t</span>
                      <span>&nbsp;</span>
                      <span>i</span>
                      <span>s</span>
                      <span>&nbsp;</span>
                      <span>a</span>
                      <span>n</span>
                      <span>a</span>
                      <span>l</span>
                      <span>y</span>
                      <span>z</span>
                      <span>i</span>
                      <span>n</span>
                      <span>g</span>
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </div>
                    <div className="flex items-center justify-center">
                      <Loader2 className="w-6 h-6 animate-spin text-primary mr-2" />
                      <span className="text-muted-foreground">
                        Processing your screenshots
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Upload reminder when less than 2 files */}
        {uploadedFiles.length < 2 && uploadedFiles.length > 0 && (
          <Card className="bg-muted/30 border-muted">
            <CardContent className="p-6 text-center">
              <div className="flex flex-col items-center gap-3">
                <AlertCircle className="w-8 h-8 text-muted-foreground" />
                <div>
                  <p className="font-medium text-foreground">
                    Upload More Screenshots
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Please upload at least 2 screenshots to begin analysis
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis Results Modal */}
        {showResultModal &&
          selectedResultFile &&
          analysisResults[selectedResultFile] && (
            <Dialog open={showResultModal} onOpenChange={setShowResultModal}>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5" />
                    Analysis Results
                  </DialogTitle>
                </DialogHeader>

                <div className="space-y-6">
                  {/* File Selection */}
                  <div className="flex gap-2 flex-wrap">
                    {uploadedFiles.map((file) => (
                      <Button
                        key={file.id}
                        variant={
                          selectedResultFile === file.id ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() => setSelectedResultFile(file.id)}
                      >
                        {file.name}
                      </Button>
                    ))}
                  </div>

                  {/* Analysis Results */}
                  {analysisResults[selectedResultFile] && (
                    <div className="space-y-4">
                      {/* Success Status */}
                      {analysisResults[selectedResultFile].success ? (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-green-800">
                            <CheckCircle className="w-5 h-5" />
                            <span className="font-medium">
                              Analysis Complete
                            </span>
                          </div>
                          <p className="text-green-700 text-sm mt-1">
                            Confidence:{" "}
                            {Math.round(
                              analysisResults[selectedResultFile]
                                .confidence_score * 100
                            )}
                            %
                          </p>
                        </div>
                      ) : (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-red-800">
                            <AlertCircle className="w-5 h-5" />
                            <span className="font-medium">Analysis Failed</span>
                          </div>
                          <p className="text-red-700 text-sm mt-1">
                            {analysisResults[selectedResultFile].error ||
                              "Unknown error occurred"}
                          </p>
                        </div>
                      )}

                      {/* Analysis Details */}
                      {analysisResults[selectedResultFile].success && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Performance Metrics */}
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">
                                Performance Metrics
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between">
                                <span>KDA:</span>
                                <span className="font-medium">
                                  {analysisResults[selectedResultFile].kda ||
                                    "N/A"}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span>GPM:</span>
                                <span className="font-medium">
                                  {analysisResults[selectedResultFile].gpm ||
                                    "N/A"}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span>Hero:</span>
                                <span className="font-medium">
                                  {analysisResults[selectedResultFile].hero ||
                                    "N/A"}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span>Role:</span>
                                <span className="font-medium">
                                  {analysisResults[selectedResultFile].role ||
                                    "N/A"}
                                </span>
                              </div>
                            </CardContent>
                          </Card>

                          {/* Coaching Feedback */}
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">
                                Coaching Feedback
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {(
                                  (analysisResults[selectedResultFile]
                                    .coaching_feedback || []).length > 0
                                ) ? (
                                  analysisResults[
                                    selectedResultFile
                                  ].coaching_feedback.map((feedback, index) => (
                                    <div
                                      key={index}
                                      className="text-sm p-2 bg-muted rounded"
                                    >
                                      {feedback}
                                    </div>
                                  ))
                                ) : (
                                  <p className="text-muted-foreground text-sm">
                                    No specific feedback available
                                  </p>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      )}

                      {/* Warnings */}
                      {analysisResults[selectedResultFile].warnings &&
                        analysisResults[selectedResultFile].warnings.length >
                          0 && (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg text-yellow-600">
                                Warnings
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <ul className="space-y-1">
                                {analysisResults[
                                  selectedResultFile
                                ].warnings.map((warning, index) => (
                                  <li
                                    key={index}
                                    className="text-sm text-yellow-700"
                                  >
                                    • {warning}
                                  </li>
                                ))}
                              </ul>
                            </CardContent>
                          </Card>
                        )}
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          )}
      </div>
    </>
  );
}
