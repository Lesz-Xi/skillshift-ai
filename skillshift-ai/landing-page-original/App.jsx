import { useState, useEffect } from "react";
import {
  Search,
  ChevronRight,
  Target,
  Brain,
  BarChart3,
  Trophy,
  Zap,
  Users,
  ArrowRight,
} from "lucide-react";
import "./App.css";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    // Handle search functionality here
    console.log("Search query:", searchQuery);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <div className="text-2xl font-bold font-display">
                <span className="text-primary">SkillShift</span>
                <span className="text-muted-foreground">AI</span>
              </div>
              <div className="hidden md:flex items-center space-x-6 text-sm font-medium">
                <a
                  href="#features"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  FEATURES
                </a>
                <a
                  href="#api"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  API
                </a>
                <a
                  href="#about"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  ABOUT
                </a>
                <a
                  href="#pricing"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  PRICING
                </a>
                <a
                  href="#contact"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  CONTACT
                </a>
              </div>
            </div>
            <button className="bg-primary text-primary-foreground px-6 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors">
              TRY SKILLSHIFT
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="pt-20">
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/20">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent_50%)]"></div>
            {/* Floating Elements */}
            <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-primary/30 rounded-full animate-pulse"></div>
            <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-accent/40 rounded-full animate-pulse delay-1000"></div>
            <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-muted/20 rounded-full animate-pulse delay-500"></div>
          </div>

          <div
            className={`relative z-10 text-center max-w-6xl mx-auto px-6 transition-all duration-1000 ${
              isVisible
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-10"
            }`}
          >
            {/* Main Title */}
            <h1 className="text-8xl md:text-9xl lg:text-[12rem] font-bold font-display leading-none mb-8 tracking-tight">
              <span className="bg-gradient-to-r from-foreground via-foreground to-muted-foreground bg-clip-text text-transparent">
                skillshift
              </span>
            </h1>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="mb-12 max-w-2xl mx-auto">
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask SkillShift anything about your gameplay..."
                  className="w-full pl-12 pr-16 py-4 bg-card border border-border rounded-xl text-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-primary text-primary-foreground p-2 rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </form>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed">
              We are thrilled to unveil SkillShift AI, our most advanced gaming
              performance analysis platform yet, blending superior coaching with
              extensive competitive knowledge.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <button className="bg-primary text-primary-foreground px-8 py-4 rounded-xl font-semibold text-lg hover:bg-primary/90 transition-all transform hover:scale-105 flex items-center gap-2">
                BUILD WITH SKILLSHIFT
                <ChevronRight className="w-5 h-5" />
              </button>
              <button className="border border-border text-foreground px-8 py-4 rounded-xl font-semibold text-lg hover:bg-accent transition-all transform hover:scale-105">
                LEARN MORE
              </button>
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
              <div className="w-6 h-10 border-2 border-muted-foreground rounded-full flex justify-center">
                <div className="w-1 h-3 bg-muted-foreground rounded-full mt-2 animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <section id="features" className="py-24 bg-card/50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold font-display mb-6">
                Advanced Gaming Intelligence
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                Harness the power of AI to analyze your gameplay, identify
                improvement areas, and accelerate your competitive journey.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                {
                  icon: <Brain className="w-8 h-8" />,
                  title: "AI Coach",
                  description:
                    "Real-time analysis and personalized coaching recommendations based on your gameplay patterns.",
                },
                {
                  icon: <BarChart3 className="w-8 h-8" />,
                  title: "Performance Analytics",
                  description:
                    "Deep insights into your gaming performance with comprehensive statistics and trend analysis.",
                },
                {
                  icon: <Target className="w-8 h-8" />,
                  title: "Skill Tracking",
                  description:
                    "Monitor your improvement across different game mechanics and competitive scenarios.",
                },
                {
                  icon: <Trophy className="w-8 h-8" />,
                  title: "Competitive Edge",
                  description:
                    "Stay ahead of the competition with advanced meta analysis and strategic insights.",
                },
                {
                  icon: <Zap className="w-8 h-8" />,
                  title: "Real-time Feedback",
                  description:
                    "Instant feedback during gameplay to help you make better decisions in the moment.",
                },
                {
                  icon: <Users className="w-8 h-8" />,
                  title: "Team Analysis",
                  description:
                    "Comprehensive team performance analysis and coordination improvement suggestions.",
                },
              ].map((feature, index) => (
                <div
                  key={index}
                  className="bg-card border border-border rounded-xl p-6 hover:shadow-lg transition-all transform hover:scale-105"
                >
                  <div className="text-primary mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-background border-t border-border py-12">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="text-2xl font-bold font-display mb-4 md:mb-0">
                <span className="text-primary">SkillShift</span>
                <span className="text-muted-foreground">AI</span>
              </div>
              <div className="flex space-x-6 text-sm text-muted-foreground">
                <a
                  href="#privacy"
                  className="hover:text-foreground transition-colors"
                >
                  Privacy
                </a>
                <a
                  href="#terms"
                  className="hover:text-foreground transition-colors"
                >
                  Terms
                </a>
                <a
                  href="#support"
                  className="hover:text-foreground transition-colors"
                >
                  Support
                </a>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-border text-center text-muted-foreground">
              <p>
                &copy; 2025 SkillShift AI. Elevating gaming performance through
                artificial intelligence.
              </p>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;
