"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import ClientOnly from "@/components/ClientOnly";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import CoachingFeedback from "@/components/coaching/CoachingFeedback";
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

// Helper function to normalize backend responses - MUST be at module level for fusion callback access
const normalizeResultHelper = (r) => {
  const hero = r.hero || r?.analysis?.performance?.hero || r?.match_data?.hero || r?.__raw?.data?.hero || null;
  const rawKda = r?.data?.kda ?? r?.__raw?.data?.kda ?? r.kda ?? (r?.analysis?.performance?.kda !== "N/A" ? r?.analysis?.performance?.kda : null) ?? r?.match_data?.kda ?? r?.parsed_data?.kda ?? null;
  const kdaBreakdown = (rawKda && typeof rawKda === "object" ? rawKda : null) || r?.data?.kda_breakdown || r?.__raw?.data?.kda_breakdown || r?.kda_breakdown || r?.match_data?.kda_breakdown || r?.parsed_data?.kda_breakdown || r?.__raw?.kda_breakdown || r?.__raw?.match_data?.kda_breakdown || null;
  
  let kda = kdaBreakdown || rawKda;
  if (kda && typeof kda === 'object' && 'k' in kda) {
    console.log("🔄 [KDA DEBUG] Converting KDA from short format:", kda);
    kda = { kills: kda.k, deaths: kda.d, assists: kda.a };
    console.log("✅ [KDA DEBUG] Converted to long format:", kda);
  }
  
  if (!kda || kda === "N/A") {
    const kills = r?.data?.kills ?? r?.__raw?.data?.kills ?? r?.kills ?? r?.match_data?.kills ?? r?.parsed_data?.kills ?? null;
    const deaths = r?.data?.deaths ?? r?.__raw?.data?.deaths ?? r?.deaths ?? r?.match_data?.deaths ?? r?.parsed_data?.deaths ?? null;
    const assists = r?.data?.assists ?? r?.__raw?.data?.assists ?? r?.assists ?? r?.match_data?.assists ?? r?.parsed_data?.assists ?? null;
    if (kills !== null && deaths !== null && assists !== null) kda = { kills, deaths, assists };
  }

  const gpmRaw = r.gpm ?? r?.analysis?.performance?.gpm ?? r?.match_data?.gpm ?? r?.parsed_data?.gpm ?? r?.__raw?.data?.gpm ?? null;
  const gpm = gpmRaw === 0 ? null : gpmRaw;
  const role = r.role || r?.analysis?.performance?.role || r?.__raw?.data?.role || null;
  const heroDamage = r?.data?.hero_damage ?? r?.data?.damage ?? r?.__raw?.data?.hero_damage ?? r?.hero_damage ?? r?.damage ?? (r?.analysis?.performance?.hero_damage !== "N/A" ? r?.analysis?.performance?.hero_damage : null) ?? r?.match_data?.hero_damage ?? r?.parsed_data?.hero_damage ?? null;
  const damageTaken = r?.data?.damage_taken ?? r?.__raw?.data?.damage_taken ?? r?.damage_taken ?? (r?.analysis?.performance?.damage_taken !== "N/A" ? r?.analysis?.performance?.damage_taken : null) ?? r?.match_data?.damage_taken ?? r?.parsed_data?.damage_taken ?? null;
  const turretDamage = r?.data?.turret_damage ?? r?.__raw?.data?.turret_damage ?? r?.turret_damage ?? (r?.analysis?.performance?.turret_damage !== "N/A" ? r?.analysis?.performance?.turret_damage : null) ?? r?.match_data?.turret_damage ?? r?.parsed_data?.turret_damage ?? null;
  const teamfightParticipation = r?.data?.teamfight_participation ?? r?.__raw?.data?.teamfight_participation ?? r?.teamfight_participation ?? (r?.analysis?.performance?.teamfight_participation !== "N/A" ? r?.analysis?.performance?.teamfight_participation : null) ?? r?.match_data?.teamfight_participation ?? r?.parsed_data?.teamfight_participation ?? null;

  let confidence = 0;
  if (typeof r?.overall_confidence === "number") confidence = r.overall_confidence;
  else if (typeof r?.confidence_score === "number") confidence = r.confidence_score;
  else if (typeof r?.analysis?.quality?.overall_confidence === "number") confidence = r.analysis.quality.overall_confidence;
  else if (typeof r?.diagnostics?.confidence_score === "number") confidence = r.diagnostics.confidence_score;
  else if (typeof r?.__raw?.data?.overall_confidence === "number") confidence = r.__raw.data.overall_confidence;
  else if (typeof r?.__raw?.data?.confidence_score === "number") confidence = r.__raw.data.confidence_score;
  if (confidence > 1) confidence = confidence / 100;
  if (!Number.isFinite(confidence)) confidence = 0;
  confidence = Math.max(0, Math.min(1, confidence));

  const feedbackArray = Array.isArray(r?.coaching_feedback) ? r.coaching_feedback : Array.isArray(r?.analysis?.statistical_feedback) ? r.analysis.statistical_feedback.map((f) => typeof f === "string" ? f : f?.message || JSON.stringify(f)) : [];
  const fusionStatus = r?.fusion_status || r?.data?.fusion_status || r?.__raw?.fusion_status || r?.__raw?.data?.fusion_status || null;
  const sessionStatus = r?.session_status || r?.data?.session_status || r?.__raw?.session_status || r?.__raw?.data?.session_status || null;
  const matchDuration = r.match_duration ?? r?.data?.match_duration ?? r?.analysis?.performance?.match_duration ?? r?.match_data?.match_duration ?? r?.parsed_data?.match_duration ?? r?.__raw?.match_duration ?? r?.__raw?.match_data?.match_duration ?? r?.__raw?.data?.match_duration ?? r?.__raw?.data?.match_duration_minutes ?? null;
  const confidenceBreakdown = r?.confidence_breakdown || r?.data?.confidence_breakdown || r?.__raw?.confidence_breakdown || r?.__raw?.data?.confidence_breakdown || {};

  return {
    success: r?.success ?? true,
    confidence_score: confidence,
    hero,
    kda,
    kda_string: r?.kda_string || (typeof rawKda === "string" ? rawKda : null),
    gpm,
    role,
    match_duration: matchDuration,
    hero_damage: heroDamage,
    damage_taken: damageTaken,
    turret_damage: turretDamage,
    teamfight_participation: teamfightParticipation,
    fusion_status: fusionStatus,
    session_status: sessionStatus,
    confidence_breakdown: confidenceBreakdown,
    coaching_feedback: feedbackArray,
    __raw: r,
  };
};

export default function ScreenshotAnalysisPage() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [processingFiles, setProcessingFiles] = useState(new Set());
  const [analysisResults, setAnalysisResults] = useState({});
  const [selectedResultFile, setSelectedResultFile] = useState(null);
  const [fusedResult, setFusedResult] = useState(null); // Store fused result separately
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
      id: Math.random().toString(36).substring(2, 11),
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
      e.stopPropagation();
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileUpload(files);
      }
    },
    [handleFileUpload]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
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
      const sessionId =
        typeof crypto !== "undefined" && crypto.randomUUID
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
        // FIXED: Handle null values properly instead of coercing to "N/A"
        // Use module-level helper function for scoping (needed for fusion callback)
        const normalized = normalizeResultHelper(result);
        results.push({
          fileId: fileData.id,
          fileName: fileData.name,
          result: normalized,
        });

        // Mark as analyzed
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileData.id ? { ...f, status: "analyzed" } : f
          )
        );
        setProcessingFiles((prev) => {
          const next = new Set(prev);
          next.delete(fileData.id);
          return next;
        });
      }

      // Store analysis results
      const resultsMap = {};
      results.forEach(({ fileId, result }) => {
        // Use coaching feedback directly from backend response
        resultsMap[fileId] = result;
      });

      setAnalysisResults(resultsMap);

      // 🔥 FUSION INTEGRATION: Check if we have both KDA and damage data across ALL results
      // This triggers after ALL screenshots in the batch have been analyzed
      // We check if ANY result has KDA data AND ANY result has damage data
      // If both exist, we trigger fusion to merge them into a single comprehensive analysis
      const allResults = Object.values(resultsMap);

      console.log("🔍 [FUSION DEBUG] Analyzing all results for fusion eligibility:", {
        totalResults: allResults.length,
        sessionId: sessionId,
      });

      // Check if we have at least one KDA screenshot (scoreboard view)
      // CRITICAL FIX: Check ALL possible paths where backend may return KDA data
      const hasKDA = allResults.some((result, idx) => {
        // Try multiple extraction paths in priority order:
        const kills = 
          result?.data?.kills ??              // Primary: result.data.kills (backend structure)
          result?.kda?.kills ??               // KDA object
          result?.__raw?.data?.kills ??       // Raw data nested
          result?.kills ??                    // Top-level fallback
          result?.match_data?.kills ??        // Match data path
          result?.parsed_data?.kills ??       // Parsed data path
          null;
        
        const deaths = 
          result?.data?.deaths ??             // Primary: result.data.deaths (backend structure)
          result?.kda?.deaths ??              // KDA object
          result?.__raw?.data?.deaths ??      // Raw data nested
          result?.deaths ??                   // Top-level fallback
          result?.match_data?.deaths ??       // Match data path
          result?.parsed_data?.deaths ??      // Parsed data path
          null;
        
        console.log(`🔍 [FUSION DEBUG] Result ${idx} KDA check:`, {
          kills,
          deaths,
          hasKDA: kills !== null && deaths !== null,
          checkedPaths: {
            'data.kills': result?.data?.kills,
            'kda.kills': result?.kda?.kills,
            '__raw.data.kills': result?.__raw?.data?.kills,
            'kills': result?.kills,
          },
          fullResult: result,
        });
        return kills !== null && deaths !== null;
      });

      const hasDamageData = allResults.some((result, idx) => {
        // CRITICAL FIX: Check ALL possible paths where backend may return damage data
        const paths = {
          data_hero_damage: result?.data?.hero_damage,     // PRIMARY: result.data.hero_damage (backend structure)
          data_damage: result?.data?.damage,               // result.data.damage alternative
          hero_damage: result?.hero_damage,
          damage: result?.damage,
          analysis_perf: result?.analysis?.performance?.hero_damage,
          match_data: result?.match_data?.hero_damage,
          raw_data: result?.__raw?.data?.hero_damage,
          raw_damage_stats: result?.__raw?.damage_stats?.hero_damage,
          parsed_data: result?.parsed_data?.hero_damage,
        };
        const damage =
          paths.data_hero_damage ??          // Try primary backend path first
          paths.data_damage ??
          paths.hero_damage ??
          paths.damage ??
          paths.analysis_perf ??
          paths.match_data ??
          paths.raw_data ??
          paths.raw_damage_stats ??
          paths.parsed_data ??
          null;
        console.log(`🔍 [FUSION DEBUG] Result ${idx} Damage check:`, {
          allPaths: paths,
          finalDamage: damage,
          hasDamageData: damage !== null && damage > 0,
        });
        return damage !== null && damage > 0;
      });

      console.log(`📊 [FUSION DEBUG] Upload batch analysis:`, {
        hasKDA,
        hasDamageData,
        sessionId,
        willTriggerFusion: hasKDA && hasDamageData && sessionId,
      });

      // Only trigger fusion if we have BOTH data types
      // This ensures we don't try to fuse with incomplete data
      if (hasKDA && hasDamageData && sessionId) {
        console.log(`🔄 Triggering fusion for session ${sessionId} with IGN=${playerIGN || "Lesz XVII"}...`);

        // Update UI to show fusion in progress
        setUploadedFiles((prev) =>
          prev.map((file) => ({
            ...file,
            status: "fusing",
          }))
        );

        try {
          // Call Next.js API route which proxies to:
          // Backend POST /api/session/{session_id}/fuse
          // This triggers the fusion engine to merge KDA + Damage data
          const fusionResponse = await fetch("/api/fused", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              ign: playerIGN || "Lesz XVII",
              session_id: sessionId,
            }),
            signal: AbortSignal.timeout(10000), // 10s timeout for fusion request
          });

          if (fusionResponse.ok) {
            const fusionData = await fusionResponse.json();

            console.log("🔍 [FUSION DEBUG] Fusion response received:", {
              status: fusionData.status,
              session_id: fusionData.session_id,
              fusion_status: fusionData.fusion_status || fusionData.data?.fusion_status,
              has_data: !!fusionData.data,
              data_keys: fusionData.data ? Object.keys(fusionData.data) : [],
              raw_response: fusionData,
            });

            if (fusionData.status === "fused") {
              console.log("✅ [FUSION DEBUG] Session fused successfully, normalizing result...");

              // Normalize the fused data into our UI schema
              // This contains merged KDA + Damage data with comprehensive coaching
              const fusedResult = normalizeResultHelper(fusionData.data);

              console.log("🔍 [FUSION DEBUG] Normalized fused result:", {
                hero: fusedResult.hero,
                kda: fusedResult.kda,
                hero_damage: fusedResult.hero_damage,
                damage_taken: fusedResult.damage_taken,
                confidence_score: fusedResult.confidence_score,
                fusion_status: fusedResult.fusion_status,
                has_raw: !!fusedResult.__raw,
                raw_keys: fusedResult.__raw ? Object.keys(fusedResult.__raw) : [],
              });

              // IMPORTANT: Store the fused result separately
              // This ensures ALL tabs display the same fused data
              console.log("🔍 [FUSION DEBUG] Storing fused result:", {
                fused_kda: fusedResult.kda,
                fused_hero_damage: fusedResult.hero_damage,
                fused_confidence: fusedResult.confidence_score,
              });
              
              setFusedResult(fusedResult);
              console.log("✅ [FUSION DEBUG] Fused result stored - all tabs will now show fused data");
            } else if (fusionData.status === "partial") {
              console.log("⏳ [FUSION DEBUG] Session still partial:", fusionData.message);
              // Keep individual results - fusion will retry when more screenshots added
            }
          } else {
            const errorText = await fusionResponse.text();
            console.error(`❌ [FUSION DEBUG] Fusion request failed:`, {
              status: fusionResponse.status,
              statusText: fusionResponse.statusText,
              errorBody: errorText,
            });
          }
        } catch (fusionError) {
          console.warn("⚠️ Fusion polling failed (non-critical):", fusionError instanceof Error ? fusionError.message : String(fusionError));
          // Keep individual results as fallback
        } finally {
          // Reset status to "analyzed" after fusion attempt
          setUploadedFiles((prev) =>
            prev.map((file) => ({
              ...file,
              status: "analyzed",
            }))
          );
        }
      } else {
        console.log(`ℹ️ Skipping fusion: hasKDA=${hasKDA}, hasDamageData=${hasDamageData}, sessionId=${sessionId}`);
      }

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
                <Label
                  htmlFor="heroOverride"
                  className="text-sm font-medium text-foreground"
                >
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
                  <Badge
                    variant="outline"
                    className="bg-muted text-muted-foreground text-xs"
                  >
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
              onClick={(e) => {
                // FIXED: Removed e.preventDefault() which was blocking file input trigger
                // Keep e.stopPropagation() to prevent event bubbling to parent elements
                e.stopPropagation();
                if (fileInputRef.current) {
                  fileInputRef.current.click();
                }
              }}
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
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileUpload(e.target.files);
                    // Reset the input value to allow re-uploading the same file
                    e.target.value = '';
                  }
                }}
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

                  {/* Enhanced Coaching Feedback */}
                  {/* MANUS FIX: Use fusedResult if available, otherwise show individual result */}
                  {(fusedResult || analysisResults[selectedResultFile]) && (
                    <CoachingFeedback 
                      analysisResult={fusedResult || analysisResults[selectedResultFile]} 
                    />
                  )}
                </div>
              </DialogContent>
            </Dialog>
          )}
      </div>
    </>
  );
}
