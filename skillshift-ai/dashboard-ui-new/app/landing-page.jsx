"use client";

import { useState } from "react";
import { CapabilityCard } from "../components/ui/CapabilityCard";
import SkillShiftGlobeSection from "../components/SkillShiftGlobeSection";
import PrinciplesSection from "../components/PrinciplesSection";
import { Camera, Video, Target, Brain, Bot, BarChart3 } from "lucide-react";

const SkillShiftLanding = () => {
  const [activeSection, setActiveSection] = useState("home");

  const features = [
    {
      icon: Camera,
      title: "Screenshot Analysis",
      description:
        "Advanced AI analysis of MLBB post-match screenshots with hero detection, KDA extraction, performance metrics, and medal recognition.",
      isNew: false,
    },
    {
      icon: Video,
      title: "Video Analysis",
      description:
        "Comprehensive gameplay video analysis with temporal event detection, behavioral patterns, and positioning heatmaps for strategic improvement.",
      isNew: false,
    },
    {
      icon: Target,
      title: "Counter-Pick Analysis",
      description:
        "Strategic draft phase assistance with enemy team composition analysis, counter-pick recommendations, and ban suggestions.",
      isNew: true,
    },
    {
      icon: Brain,
      title: "Player Insights",
      description:
        "Deep performance trend analysis with behavioral pattern recognition, mental coaching feedback, and personalized improvement roadmaps.",
      isNew: false,
    },
    {
      icon: Bot,
      title: "AI Coaching",
      description:
        "Real-time performance feedback with confidence adjustment, statistical analysis, and motivational support for consistent improvement.",
      isNew: true,
    },
    {
      icon: BarChart3,
      title: "Performance Analytics",
      description:
        "Comprehensive match statistics, ranking insights, hero mastery tracking, and competitive performance monitoring.",
      isNew: false,
    },
  ];

  const principles = [
    {
      title: "Data-Driven Excellence",
      description:
        "We believe every MLBB player deserves coaching backed by comprehensive data analysis, not just generic advice.",
    },
    {
      title: "Personalized Growth",
      description:
        "Every player is unique. Our AI adapts to individual playstyles, learning patterns, and competitive goals.",
    },
    {
      title: "Continuous Innovation",
      description:
        "We constantly evolve our AI models to stay ahead of meta changes, new heroes, and competitive strategies.",
    },
    {
      title: "Real-Time Intelligence",
      description:
        "From screenshot analysis to live coaching feedback, we provide actionable insights when you need them most.",
    },
    {
      title: "Community First",
      description:
        "Built by MLBB players, for MLBB players. We understand the game because we live and breathe it.",
    },
    {
      title: "Performance Focus",
      description:
        "Every feature is designed with one goal: helping you climb ranks and achieve your competitive potential.",
    },
  ];

  const news = [
    {
      date: "February 19, 2025",
      title: "SkillShift MLBB Coach 3.0 — Advanced Video Analysis Released",
      description:
        "Introducing temporal event detection, behavioral pattern analysis, and real-time positioning heatmaps for competitive players.",
    },
    {
      date: "January 15, 2025",
      title: "Counter-Pick Analysis 2.0 — Draft Phase Revolution",
      description:
        "Enhanced team composition analysis with meta-aware recommendations and strategic win condition mapping.",
    },
    {
      date: "December 12, 2024",
      title: "Screenshot Analysis Upgrade — 95% Hero Detection Accuracy",
      description:
        "Improved KDA extraction, medal recognition, and performance metrics analysis with real-time confidence scoring.",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Header */}
      <header className="flex justify-between items-center px-8 py-6 border-b border-border">
        <div className="flex items-center space-x-8">
          <div className="h2 font-display flex items-center">SkillShift</div>
          <nav className="flex space-x-8 text-sm tracking-wider">
            <a
              href="#home"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "home"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("home")}
            >
              SKILLSHIFT
            </a>
            <a
              href="#price"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "price"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("price")}
            >
              PRICE
            </a>
            <a
              href="#features"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "features"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("features")}
            >
              FEATURES
            </a>
            <a
              href="#coaching"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "coaching"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("coaching")}
            >
              COACHING
            </a>
            <a
              href="#about"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "about"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("about")}
            >
              ABOUT
            </a>
            <a
              href="#updates"
              className={`hover:text-foreground/80 transition-colors ${
                activeSection === "updates"
                  ? "text-foreground border-b-2 border-primary"
                  : "text-muted-foreground"
              }`}
              onClick={() => setActiveSection("updates")}
            >
              UPDATES
            </a>
          </nav>
        </div>
        <a href="/dashboard">
          <button className="border border-border px-6 py-3 text-sm tracking-wider hover:bg-accent hover:text-accent-foreground transition-colors btn-text rounded-full">
            START COACHING
          </button>
        </a>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-8 py-16">
        {/* Home/Hero Section */}
        {activeSection === "home" && (
          <>
            {/* Company Description */}
            <div className="mb-20">
              <p className="text-large text-muted-foreground leading-relaxed">
                SkillShift-AI is a company building artificial intelligence to
                revolutionize Mobile Legends: Bang Bang coaching and performance
                analysis. We are guided by our mission to help every MLBB player
                reach their competitive potential through advanced AI insights.
              </p>
            </div>

            {/* Mission Section */}
            <section className="mb-20">
              <div className="mb-8">
                <p className="text-xs text-muted-foreground tracking-wider mb-4 uppercase">
                  [ OUR MISSION ]
                </p>
                <h1 className="h1 font-display leading-tight mb-8">
                  Master MLBB
                  <br />
                  <span className="text-muted-foreground">
                    with AI Coaching
                  </span>
                </h1>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                <div>
                  <p className="text-large text-muted-foreground leading-relaxed mb-6">
                    Every MLBB player deserves personalized, intelligent
                    coaching. We build AI specifically to analyze gameplay,
                    identify improvement opportunities, and accelerate
                    competitive growth through data-driven insights.
                  </p>
                </div>

                {/* Visual Element - representing career growth */}
                <div className="relative h-64 flex items-center justify-center">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-secondary/10 to-accent/10 rounded-full"></div>
                  <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-secondary opacity-80 animate-pulse"></div>
                  <div className="absolute w-48 h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-60"></div>
                  <div className="absolute w-40 h-1 bg-gradient-to-r from-transparent via-secondary to-transparent opacity-60 rotate-45"></div>
                  <div className="absolute w-36 h-1 bg-gradient-to-r from-transparent via-accent to-transparent opacity-60 -rotate-45"></div>
                </div>
              </div>
            </section>

            {/* Features Section */}
            <section className="mb-20">
              <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
                [ CAPABILITIES ]
              </p>
              <h2 className="h3 font-display mb-12">
                Elevate Your MLBB Game with AI
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
                {features.map((feature, index) => (
                  <CapabilityCard
                    key={index}
                    icon={feature.icon}
                    title={feature.title}
                    description={feature.description}
                    isNew={feature.isNew}
                  />
                ))}
              </div>
            </section>

            {/* Globe Section */}
            <SkillShiftGlobeSection />

            {/* Principles Section */}
            <PrinciplesSection />
          </>
        )}

        {/* Features Section */}
        {activeSection === "features" && (
          <>
            <div className="mb-20">
              <p className="text-large text-muted-foreground leading-relaxed">
                Discover the powerful AI-driven features that make SkillShift
                the most advanced MLBB coaching platform. Our cutting-edge
                technology analyzes every aspect of your gameplay to provide
                personalized insights and recommendations.
              </p>
            </div>

            {/* Core Features Section */}
            <section className="mb-20">
              <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
                [ CORE FEATURES ]
              </p>

              <div className="space-y-8">
                {principles.map((principle, index) => (
                  <div key={index} className="border-l border-border pl-6">
                    <h3 className="h5 text-foreground mb-2">
                      {principle.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {principle.description}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* Offices Section */}
            <section className="mb-20">
              <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
                [ OFFICES ]
              </p>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                <div>
                  <p className="text-large text-muted-foreground leading-relaxed mb-6">
                    We are hiring across all our offices in{" "}
                    <span className="text-foreground">San Francisco</span>,
                    <span className="text-foreground"> New York</span>, and{" "}
                    <span className="text-foreground"> Austin</span>. We
                    prioritize in-person work to support our fast-paced,
                    collaborative projects.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-2 h-2 bg-foreground rounded-full"></div>
                    <span className="text-muted-foreground">
                      San Francisco, CA
                    </span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="w-2 h-2 bg-foreground rounded-full"></div>
                    <span className="text-muted-foreground">New York, NY</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="w-2 h-2 bg-foreground rounded-full"></div>
                    <span className="text-muted-foreground">Austin, TX</span>
                  </div>
                </div>
              </div>
            </section>
          </>
        )}

        {/* Price Section */}
        {activeSection === "price" && (
          <section className="mb-20">
            <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
              [ PRICING ]
            </p>
            <h2 className="h2 font-display mb-8">Choose Your Coaching Plan</h2>
            <p className="text-large text-muted-foreground leading-relaxed mb-12">
              Select the perfect plan for your MLBB coaching journey. From
              casual players to competitive teams, we have options for every
              skill level.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="border border-border rounded-lg p-6 bg-card">
                <h3 className="h5 font-display mb-4">Starter</h3>
                <div className="h3 font-display mb-4">
                  $29
                  <span className="text-base text-muted-foreground">
                    /month
                  </span>
                </div>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• 1,000 screenshot analyses/month</li>
                  <li>• Basic hero & KDA detection</li>
                  <li>• Email support</li>
                </ul>
              </div>

              <div className="border border-primary rounded-lg p-6 bg-primary/5">
                <h3 className="h5 font-display mb-4">Professional</h3>
                <div className="h3 font-display mb-4">
                  $99
                  <span className="text-base text-muted-foreground">
                    /month
                  </span>
                </div>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• 10,000 analyses/month</li>
                  <li>• Video analysis included</li>
                  <li>• Counter-pick recommendations</li>
                  <li>• Priority support</li>
                </ul>
              </div>

              <div className="border border-border rounded-lg p-6 bg-card">
                <h3 className="h5 font-display mb-4">Enterprise</h3>
                <div className="h3 font-display mb-4">Custom</div>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Unlimited analyses</li>
                  <li>• Team coaching features</li>
                  <li>• Custom AI models</li>
                  <li>• SLA guarantees</li>
                </ul>
              </div>
            </div>
          </section>
        )}

        {/* Coaching Section */}
        {activeSection === "coaching" && (
          <section className="mb-20">
            <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
              [ COACHING PROGRAMS ]
            </p>
            <h2 className="h2 font-display mb-8">Personalized MLBB Coaching</h2>
            <p className="text-large text-muted-foreground leading-relaxed mb-12">
              Transform your MLBB gameplay with our AI-powered coaching
              programs. From beginner fundamentals to advanced competitive
              strategies, our personalized approach adapts to your skill level
              and goals.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="border border-border rounded-lg p-6 bg-card">
                <h3 className="h5 font-display mb-4">SkillShift Basic</h3>
                <p className="text-muted-foreground mb-4">
                  Essential MLBB performance analysis and coaching
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Screenshot analysis</li>
                  <li>• Hero detection & KDA</li>
                  <li>• Basic performance insights</li>
                </ul>
              </div>

              <div className="border border-secondary rounded-lg p-6 bg-secondary/5">
                <h3 className="h5 font-display mb-4">SkillShift Pro</h3>
                <p className="text-muted-foreground mb-4">
                  Advanced MLBB coaching with comprehensive AI analysis
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Video gameplay analysis</li>
                  <li>• Counter-pick recommendations</li>
                  <li>• Player insights & mental coaching</li>
                  <li>• Performance trend tracking</li>
                </ul>
              </div>

              <div className="border border-border rounded-lg p-6 bg-card">
                <h3 className="h5 font-display mb-4">SkillShift Enterprise</h3>
                <p className="text-muted-foreground mb-4">
                  Professional esports team coaching solutions
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Team composition analysis</li>
                  <li>• Multi-player video analysis</li>
                  <li>• Strategic coaching programs</li>
                  <li>• Tournament preparation</li>
                </ul>
              </div>
            </div>
          </section>
        )}

        {/* About Section */}
        {activeSection === "about" && (
          <section className="mb-20">
            <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
              [ ABOUT SKILLSHIFT ]
            </p>
            <h2 className="h2 font-display mb-8">
              Revolutionizing MLBB Coaching
            </h2>
            <p className="text-large text-muted-foreground leading-relaxed mb-12">
              SkillShift AI is pioneering the future of esports coaching through
              advanced artificial intelligence. We combine deep MLBB expertise
              with cutting-edge AI technology to help players reach their full
              competitive potential.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              <div>
                <h3 className="h3 font-display mb-6">Our Process</h3>
                <div className="space-y-6">
                  <div className="border-l border-border pl-6">
                    <h4 className="h5 font-display mb-2">Application Review</h4>
                    <p className="text-muted-foreground">
                      A thorough review of your background and assessment of
                      role fit.
                    </p>
                  </div>
                  <div className="border-l border-border pl-6">
                    <h4 className="h5 font-display mb-2">
                      Technical Interviews
                    </h4>
                    <p className="text-muted-foreground">
                      Deep dives into your technical expertise and
                      problem-solving approach.
                    </p>
                  </div>
                  <div className="border-l border-border pl-6">
                    <h4 className="h5 font-display mb-2">Cultural Fit</h4>
                    <p className="text-muted-foreground">
                      Understanding how you work and align with our
                      mission-driven culture.
                    </p>
                  </div>
                  <div className="border-l border-border pl-6">
                    <h4 className="h5 font-display mb-2">Offer</h4>
                    <p className="text-muted-foreground">
                      Join our team pushing the boundaries of AI for career
                      transformation.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="h3 font-display mb-6">Benefits</h3>
                <ul className="space-y-3 text-muted-foreground">
                  <li>• Competitive salary and equity</li>
                  <li>• Comprehensive health coverage</li>
                  <li>• Professional development budget</li>
                  <li>• Flexible working arrangements</li>
                  <li>• Mission-driven culture</li>
                </ul>
              </div>
            </div>
          </section>
        )}

        {/* Updates Section */}
        {activeSection === "updates" && (
          <section className="mb-20">
            <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
              [ PLATFORM UPDATES ]
            </p>
            <h2 className="h2 font-display mb-12">Latest Platform Updates</h2>

            <div className="space-y-8">
              {news.map((item, index) => (
                <div
                  key={index}
                  className="border border-border rounded-lg p-6 hover:border-border/60 transition-colors bg-card"
                >
                  <div className="text-sm text-muted-foreground mb-2">
                    {item.date}
                  </div>
                  <h3 className="h5 font-display mb-3">{item.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-8 py-8">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            © 2025 SkillShift-AI. All rights reserved.
          </div>
          <div className="flex space-x-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-foreground transition-colors">
              Terms of Service
            </a>
            <a href="#" className="hover:text-foreground transition-colors">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default SkillShiftLanding;
