"use client";

import Globe3D from "./Globe3D";

const offices = [
  {
    city: "MANILA",
    country: "Philippines",
    lat: 14.5995,
    lng: 120.9842,
    coordinates: "14.5995°N, 120.9842°E",
  },
  {
    city: "JAKARTA",
    country: "Indonesia",
    lat: -6.2088,
    lng: 106.8456,
    coordinates: "6.2088°S, 106.8456°E",
  },
  {
    city: "YANGON",
    country: "Myanmar",
    lat: 16.8661,
    lng: 96.1951,
    coordinates: "16.8661°N, 96.1951°E",
  },
  {
    city: "PHNOM PENH",
    country: "Cambodia",
    lat: 11.5564,
    lng: 104.9282,
    coordinates: "11.5564°N, 104.9282°E",
  },
  {
    city: "NEW YORK",
    country: "USA",
    lat: 40.7128,
    lng: -74.006,
    coordinates: "40.7128°N, 74.0060°W",
  },
  {
    city: "SINGAPORE",
    country: "Singapore",
    lat: 1.3521,
    lng: 103.8198,
    coordinates: "1.3521°N, 103.8198°E",
  },
];

const SkillShiftGlobeSection = () => {
  return (
    <section className="py-20 px-6">
      <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-16 items-center">
        {/* Left Content */}
        <div className="space-y-8">
          <div className="space-y-6">
            <div className="text-muted-foreground text-sm font-medium tracking-wider">
              [ GLOBAL REACH ]
            </div>

            <h2 className="text-5xl lg:text-6xl font-light tracking-tight text-foreground leading-tight">
              Connecting
              <br />
              MLBB Players
            </h2>

            <p className="text-lg text-muted-foreground leading-relaxed max-w-md">
              Our AI coaching platform serves Mobile Legends players across the
              globe, providing personalized insights and strategic guidance in
              Philippines, Indonesia, Myanmar, Cambodia, USA, and Singapore.
            </p>
          </div>
        </div>

        {/* Right Globe */}
        <div className="relative h-[600px] lg:h-[700px]">
          <Globe3D offices={offices} rotationSpeed={0.0008} />
        </div>
      </div>
    </section>
  );
};

export default SkillShiftGlobeSection;
