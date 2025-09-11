"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Clock,
  Target,
  Users,
  Brain,
  TrendingUp,
  MapPin,
  Activity,
  Zap,
  Eye,
  Download,
  Settings,
  Library,
  Upload,
  Calendar,
  Star,
  Filter,
  Search,
  FileVideo,
} from "lucide-react";

export default function VideoAnalysisPage() {
  // Video player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  // Analysis state
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Video file state
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  // Tab state
  const [activeTab, setActiveTab] = useState("upload");

  // Video library state
  const [videoLibrary, setVideoLibrary] = useState([
    {
      id: "VL-001",
      title: "Mythic Rank Push - Ling Gameplay",
      hero: "Ling",
      role: "Assassin",
      uploadDate: "2025-01-17T10:30:00Z",
      duration: "18:45",
      result: "Victory",
      score: 92,
      kda: "15/3/8",
      badges: ["MVP", "SAVAGE"],
      thumbnailUrl: "/thumbnails/video_001.jpg",
      videoUrl: "/videos/ling_mythic_push.mp4",
      coachingFeedback: {
        strengths: ["Excellent jungle timing", "Perfect team fight engagement"],
        improvements: ["Early game farm optimization", "Vision control"],
        overallScore: 92,
      },
    },
    {
      id: "VL-002",
      title: "Chang'e Mid Lane Analysis",
      hero: "Chang'e",
      role: "Mage",
      uploadDate: "2025-01-16T15:20:00Z",
      duration: "22:30",
      result: "Victory",
      score: 78,
      kda: "8/4/12",
      badges: ["LEGENDARY"],
      thumbnailUrl: "/thumbnails/video_002.jpg",
      videoUrl: "/videos/change_midlane.mp4",
      coachingFeedback: {
        strengths: ["Good spell rotation", "Effective roaming"],
        improvements: ["Positioning vs assassins", "Mana management"],
        overallScore: 78,
      },
    },
    {
      id: "VL-003",
      title: "Granger Team Fight Study",
      hero: "Granger",
      role: "Marksman",
      uploadDate: "2025-01-15T20:15:00Z",
      duration: "25:12",
      result: "Defeat",
      score: 65,
      kda: "6/7/11",
      badges: [],
      thumbnailUrl: "/thumbnails/video_003.jpg",
      videoUrl: "/videos/granger_teamfight.mp4",
      coachingFeedback: {
        strengths: ["Good item builds", "Decent positioning"],
        improvements: [
          "Target prioritization",
          "Escape timing",
          "Map awareness",
        ],
        overallScore: 65,
      },
    },
  ]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const videoRef = useRef(null);

  // Mock analysis results for demonstration
  const mockAnalysisResults = {
    playerIGN: "Lesz XVII",
    videoDuration: 847, // seconds
    gamePhases: {
      early: { start: 0, end: 300, performance: 85 },
      mid: { start: 300, end: 600, performance: 72 },
      late: { start: 600, end: 847, performance: 91 },
    },
    events: [
      {
        timestamp: 45,
        type: "first_blood",
        player: "Lesz XVII",
        confidence: 0.95,
      },
      { timestamp: 127, type: "tower_destroy", team: "ally", confidence: 0.89 },
      {
        timestamp: 234,
        type: "lord_attempt",
        result: "success",
        confidence: 0.92,
      },
      {
        timestamp: 456,
        type: "team_fight",
        outcome: "victory",
        confidence: 0.88,
      },
      { timestamp: 678, type: "turtle_secure", team: "ally", confidence: 0.94 },
      { timestamp: 789, type: "maniac", player: "Lesz XVII", confidence: 0.97 },
    ],
    behavioralInsights: {
      playstyle: "aggressive-roamer",
      riskProfile: "calculated",
      gameTempo: "early-game-focused",
      teamCoordination: 0.87,
      positioningScore: 0.82,
      reactionTime: 0.91,
    },
    heatmapData: {
      kills: [
        [100, 150],
        [250, 300],
        [400, 200],
      ],
      deaths: [
        [180, 280],
        [350, 150],
      ],
      assists: [
        [120, 200],
        [280, 250],
        [380, 320],
        [450, 180],
      ],
    },
  };

  const handleVideoUpload = useCallback((event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("video/")) {
      setVideoFile(file);
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
    }
  }, []);

  const handleAnalyzeVideo = useCallback(async () => {
    if (!videoFile) return;

    setIsAnalyzing(true);
    setAnalysisProgress(0);

    // Simulate analysis progress
    const interval = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsAnalyzing(false);
          setAnalysisResults(mockAnalysisResults);
          return 100;
        }
        return prev + 2;
      });
    }, 100);
  }, [videoFile]);

  const handleTimelineSeek = useCallback((timestamp) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      setCurrentTime(timestamp);
    }
  }, []);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getPhaseColor = (phase) => {
    switch (phase) {
      case "early":
        return "bg-primary";
      case "mid":
        return "bg-secondary";
      case "late":
        return "bg-muted";
      default:
        return "bg-muted";
    }
  };

  const filteredVideoLibrary = videoLibrary.filter((video) => {
    const matchesSearch =
      video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      video.hero.toLowerCase().includes(searchTerm.toLowerCase()) ||
      video.role.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      selectedFilter === "all" ||
      (selectedFilter === "victory" && video.result === "Victory") ||
      (selectedFilter === "defeat" && video.result === "Defeat") ||
      (selectedFilter === "recent" &&
        new Date(video.uploadDate) >
          new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-foreground">
              Video Analysis Laboratory
            </h1>
            <p className="text-muted-foreground mt-2">
              Temporal Intelligence • Behavioral Flow Mapping • Strategic
              Analysis
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export Analysis
            </Button>
            <Button variant="outline">
              <Settings className="w-4 h-4 mr-2" />
              Pipeline Settings
            </Button>
          </div>
        </div>

        {/* Video Library Section */}
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-foreground">
                <Library className="w-5 h-5" />
                Video Match Library ({videoLibrary.length})
              </CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search videos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground text-sm"
                  />
                </div>
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredVideoLibrary.map((video) => (
                <div
                  key={video.id}
                  className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <FileVideo className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium text-foreground">
                        {video.hero} • {video.role}
                      </span>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        video.result === "Victory"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {video.result}
                    </span>
                  </div>

                  <h4 className="font-medium text-foreground mb-2 line-clamp-2">
                    {video.title}
                  </h4>

                  <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                    <span>{video.duration}</span>
                    <span>KDA {video.kda}</span>
                    <span
                      className={`font-medium ${
                        video.score >= 80
                          ? "text-green-600"
                          : video.score >= 60
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}
                    >
                      {video.score}%
                    </span>
                  </div>

                  <div className="flex items-center gap-1 mb-3">
                    {video.badges.map((badge) => (
                      <span
                        key={badge}
                        className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-800 rounded"
                      >
                        {badge}
                      </span>
                    ))}
                  </div>

                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Play className="w-3 h-3 mr-1" />
                      Watch
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <Eye className="w-3 h-3 mr-1" />
                      Analysis
                    </Button>
                  </div>

                  <p className="text-xs text-muted-foreground mt-2">
                    {new Date(video.uploadDate).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>

            {filteredVideoLibrary.length === 0 && (
              <div className="text-center py-8">
                <FileVideo className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">
                  No videos found matching your search
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Video Upload Section */}
        {!videoFile && (
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-foreground">
                <Play className="w-5 h-5" />
                Upload Match Replay
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleVideoUpload}
                  className="hidden"
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="cursor-pointer">
                  <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                    <Play className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium text-foreground mb-2">
                    Upload MLBB Match Video
                  </h3>
                  <p className="text-muted-foreground">
                    Supports MP4, AVI, MOV formats • Max 2GB
                  </p>
                </label>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Video Player & Analysis Interface */}
        {videoFile && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Main Video Player */}
            <div className="xl:col-span-2">
              <Card className="border-border bg-card">
                <CardContent className="p-0">
                  <div className="relative">
                    <video
                      ref={videoRef}
                      src={videoUrl}
                      className="w-full h-64 sm:h-80 object-cover rounded-t-lg"
                      onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
                      onLoadedMetadata={(e) => setDuration(e.target.duration)}
                    />

                    {/* Video Controls Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 bg-black/80 p-4">
                      <div className="flex items-center gap-4">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            if (isPlaying) {
                              videoRef.current?.pause();
                            } else {
                              videoRef.current?.play();
                            }
                            setIsPlaying(!isPlaying);
                          }}
                        >
                          {isPlaying ? (
                            <Pause className="w-4 h-4" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>

                        <div className="flex-1">
                          <Slider
                            value={[currentTime]}
                            max={duration}
                            step={1}
                            onValueChange={([value]) =>
                              handleTimelineSeek(value)
                            }
                            className="w-full"
                          />
                        </div>

                        <span className="text-sm text-muted-foreground min-w-20">
                          {formatTime(currentTime)} / {formatTime(duration)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Timeline with Events */}
                  {analysisResults && (
                    <div className="p-4 border-t border-border">
                      <h3 className="text-sm font-medium text-foreground mb-3">
                        Match Timeline
                      </h3>
                      <div className="relative h-8 bg-muted rounded-lg overflow-hidden">
                        {/* Game Phase Backgrounds */}
                        {Object.entries(analysisResults.gamePhases).map(
                          ([phase, data]) => (
                            <div
                              key={phase}
                              className={`absolute top-0 h-full ${getPhaseColor(
                                phase
                              )} opacity-30`}
                              style={{
                                left: `${(data.start / duration) * 100}%`,
                                width: `${
                                  ((data.end - data.start) / duration) * 100
                                }%`,
                              }}
                            />
                          )
                        )}

                        {/* Event Markers */}
                        {analysisResults.events.map((event, index) => (
                          <div
                            key={index}
                            className="absolute top-1 w-1.5 h-6 bg-primary rounded-full cursor-pointer hover:bg-primary/80 transition-colors"
                            style={{
                              left: `${(event.timestamp / duration) * 100}%`,
                            }}
                            onClick={() => handleTimelineSeek(event.timestamp)}
                            title={`${event.type} at ${formatTime(
                              event.timestamp
                            )}`}
                          />
                        ))}

                        {/* Current Time Indicator */}
                        <div
                          className="absolute top-0 w-0.5 h-full bg-foreground"
                          style={{ left: `${(currentTime / duration) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Analysis Button */}
              {!analysisResults && !isAnalyzing && (
                <Card className="border-border bg-card mt-4">
                  <CardContent className="p-4">
                    <Button onClick={handleAnalyzeVideo} className="w-full">
                      <Brain className="w-4 h-4 mr-2" />
                      Analyze Video with AI
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Analysis Progress */}
              {isAnalyzing && (
                <Card className="border-border bg-card mt-4">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <Activity className="w-5 h-5 text-foreground animate-pulse" />
                      <span className="text-foreground font-medium">
                        Analyzing Video... {analysisProgress}%
                      </span>
                    </div>
                    <Progress value={analysisProgress} className="w-full" />
                    <p className="text-sm text-muted-foreground mt-2">
                      Processing temporal events, behavioral patterns, and
                      strategic insights...
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Analysis Sidebar */}
            <div className="space-y-6">
              {/* Quick Stats */}
              {analysisResults && (
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle className="text-foreground text-lg">
                      Analysis Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Player:</span>
                      <Badge
                        variant="outline"
                        className="border-border text-foreground"
                      >
                        {analysisResults.playerIGN}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="text-foreground">
                        {formatTime(analysisResults.videoDuration)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Events:</span>
                      <span className="text-foreground">
                        {analysisResults.events.length}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Game Phases */}
              {analysisResults && (
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle className="text-foreground text-lg flex items-center gap-2">
                      <Clock className="w-5 h-5" />
                      Game Phases
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {Object.entries(analysisResults.gamePhases).map(
                      ([phase, data]) => (
                        <div key={phase} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-muted-foreground capitalize">
                              {phase} Game:
                            </span>
                            <span className="text-foreground">
                              {data.performance}%
                            </span>
                          </div>
                          <Progress
                            value={data.performance}
                            className="w-full h-2"
                          />
                        </div>
                      )
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Behavioral Insights */}
              {analysisResults && (
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle className="text-foreground text-lg flex items-center gap-2">
                      <Brain className="w-5 h-5" />
                      Behavioral Profile
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Playstyle:</span>
                      <Badge className="bg-primary text-primary-foreground">
                        {analysisResults.behavioralInsights.playstyle}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">
                        Risk Profile:
                      </span>
                      <span className="text-foreground">
                        {analysisResults.behavioralInsights.riskProfile}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">
                        Team Coordination:
                      </span>
                      <span className="text-foreground">
                        {Math.round(
                          analysisResults.behavioralInsights.teamCoordination *
                            100
                        )}
                        %
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Detailed Analysis Tabs */}
        {analysisResults && (
          <Card className="border-border bg-card">
            <CardContent className="p-0">
              <Tabs defaultValue="events" className="w-full">
                <TabsList className="grid w-full grid-cols-4 bg-muted">
                  <TabsTrigger
                    value="events"
                    className="flex items-center gap-2"
                  >
                    <Target className="w-4 h-4" />
                    Events
                  </TabsTrigger>
                  <TabsTrigger
                    value="heatmap"
                    className="flex items-center gap-2"
                  >
                    <MapPin className="w-4 h-4" />
                    Heatmap
                  </TabsTrigger>
                  <TabsTrigger
                    value="behavior"
                    className="flex items-center gap-2"
                  >
                    <TrendingUp className="w-4 h-4" />
                    Behavior
                  </TabsTrigger>
                  <TabsTrigger
                    value="coaching"
                    className="flex items-center gap-2"
                  >
                    <Brain className="w-4 h-4" />
                    Coaching
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="events" className="p-6 space-y-4">
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    Key Events Timeline
                  </h3>
                  {analysisResults.events.map((event, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-muted/50 rounded-lg cursor-pointer hover:bg-muted/80 transition-colors"
                      onClick={() => handleTimelineSeek(event.timestamp)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-primary rounded-full"></div>
                        <span className="text-foreground font-medium">
                          {event.type.replace("_", " ")}
                        </span>
                        <span className="text-muted-foreground">
                          {formatTime(event.timestamp)}
                        </span>
                      </div>
                      <Badge
                        variant="outline"
                        className="border-border text-foreground"
                      >
                        {Math.round(event.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="heatmap" className="p-6">
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    Position Heatmap
                  </h3>
                  <div className="bg-muted rounded-lg p-6 h-64 flex items-center justify-center">
                    <p className="text-muted-foreground">
                      Heatmap visualization will be rendered here
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="behavior" className="p-6">
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    Behavioral Analysis
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="border-border bg-card">
                      <CardHeader>
                        <CardTitle className="text-foreground">
                          Decision Making
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Progress value={85} className="w-full mb-2" />
                        <p className="text-sm text-muted-foreground">
                          Strong tactical decisions in team fights
                        </p>
                      </CardContent>
                    </Card>
                    <Card className="border-border bg-card">
                      <CardHeader>
                        <CardTitle className="text-foreground">
                          Positioning
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Progress value={82} className="w-full mb-2" />
                        <p className="text-sm text-muted-foreground">
                          Excellent map awareness and spacing
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="coaching" className="p-6">
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    AI Coaching Insights
                  </h3>
                  <div className="space-y-4">
                    <Card className="border-border bg-card">
                      <CardContent className="p-4">
                        <h4 className="text-foreground font-medium mb-2">
                          ✓ Strengths
                        </h4>
                        <p className="text-muted-foreground">
                          Excellent early game aggression and objective control
                        </p>
                      </CardContent>
                    </Card>
                    <Card className="border-border bg-card">
                      <CardContent className="p-4">
                        <h4 className="text-foreground font-medium mb-2">
                          ⚠ Areas for Improvement
                        </h4>
                        <p className="text-muted-foreground">
                          Late game positioning could be more conservative
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
