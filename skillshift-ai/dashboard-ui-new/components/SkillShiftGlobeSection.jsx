"use client";

import Globe3D from "./Globe3D";

const SkillShiftGlobeSection = () => {
  // Office locations for the globe
  const offices = [
    {
      city: "San Francisco",
      coordinates: "37.7749° N, 122.4194° W",
      lat: 37.7749,
      lng: -122.4194,
    },
    {
      city: "New York",
      coordinates: "40.7128° N, 74.0060° W",
      lat: 40.7128,
      lng: -74.006,
    },
    {
      city: "Austin",
      coordinates: "30.2672° N, 97.7431° W",
      lat: 30.2672,
      lng: -97.7431,
    },
  ];

  return (
    <section className="mb-20">
      <div className="mb-8">
        <p className="text-xs text-muted-foreground tracking-wider mb-4 uppercase">
          [ GLOBAL REACH ]
        </p>
        <h2 className="h3 font-display mb-8">
          Connecting MLBB Players Worldwide
        </h2>
        <p className="text-large text-muted-foreground leading-relaxed mb-12 max-w-3xl">
          Our AI coaching platform serves players across the globe, with offices
          in major gaming hubs and a community that spans every continent.
          Experience the future of MLBB coaching, no matter where you are.
        </p>
      </div>

      {/* Globe Container */}
      <div className="relative">
        <div className="h-[600px] w-full rounded-lg overflow-hidden border border-border bg-card">
          <Globe3D offices={offices} rotationSpeed={0.002} />
        </div>

        {/* Overlay Stats */}
        <div className="absolute top-6 right-6 bg-card/90 backdrop-blur-sm border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-2">
            Active Players
          </div>
          <div className="text-2xl font-display text-foreground">50,000+</div>
        </div>

        <div className="absolute bottom-6 left-6 bg-card/90 backdrop-blur-sm border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-2">Countries</div>
          <div className="text-2xl font-display text-foreground">120+</div>
        </div>
      </div>

      {/* Office Details */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
        {offices.map((office, index) => (
          <div key={index} className="text-center">
            <div className="w-3 h-3 bg-primary rounded-full mx-auto mb-3"></div>
            <h3 className="h5 font-display mb-2">{office.city}</h3>
            <p className="text-sm text-muted-foreground">
              {office.coordinates}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default SkillShiftGlobeSection;
