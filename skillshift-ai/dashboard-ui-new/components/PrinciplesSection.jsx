"use client";

import { CapabilityCard } from "./ui/CapabilityCard";
import { 
  Users, 
  Heart, 
  Home, 
  Calendar, 
  Globe, 
  PiggyBank 
} from "lucide-react";

const principles = [
  {
    icon: Users,
    title: "Competitive compensation",
    description: "Competitive cash and equity-based compensation packages to attract top talent.",
    isNew: false,
  },
  {
    icon: Heart,
    title: "Health and wellness",
    description: "Comprehensive health insurance including medical, dental, vision, and disability coverage.",
    isNew: false,
  },
  {
    icon: Home,
    title: "Life and family",
    description: "Life and AD&D insurance and fertility benefits to ensure our team's well-being and peace of mind.",
    isNew: false,
  },
  {
    icon: Calendar,
    title: "Flexible vacation",
    description: "We work hard but avoid burn out. Take time off when you need it.",
    isNew: false,
  },
  {
    icon: Globe,
    title: "Visa sponsorship",
    description: "We support international talent with visa sponsorship to join our team.",
    isNew: true,
  },
  {
    icon: PiggyBank,
    title: "401(k) plan",
    description: "Retirement savings plan to secure your financial future.",
    isNew: false,
  },
];

const PrinciplesSection = () => {
  return (
    <section className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-16 grid lg:grid-cols-2 gap-16 items-start">
          <div>
            <p className="text-xs text-muted-foreground tracking-wider mb-8 uppercase">
              [ OUR PRINCIPLES ]
            </p>
            <h2 className="text-5xl lg:text-6xl font-light tracking-tight text-foreground leading-tight">
              Coding ≥ x ∀ x
            </h2>
          </div>
          
          <div className="lg:pt-16">
            <p className="text-lg text-muted-foreground leading-relaxed">
              We are driven by ambitious goals, fast execution, and a strong sense of urgency. 
              Join us if you want to shape the next generation of AI models and products.
            </p>
          </div>
        </div>

        {/* Principles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {principles.map((principle, index) => (
            <CapabilityCard
              key={index}
              icon={principle.icon}
              title={principle.title}
              description={principle.description}
              isNew={principle.isNew}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default PrinciplesSection;