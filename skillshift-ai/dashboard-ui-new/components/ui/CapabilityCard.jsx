import React from 'react';

export function CapabilityCard({ icon: Icon, title, description, isNew = false }) {
  return (
    <div className="group relative p-8 border border-border rounded-lg hover:border-primary/50 transition-all duration-300 hover:bg-card/80 overflow-hidden">
      {/* Corner brackets that appear on hover */}
      <div className="absolute top-2 left-2 w-4 h-4 border-l-2 border-t-2 border-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      <div className="absolute top-2 right-2 w-4 h-4 border-r-2 border-t-2 border-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      <div className="absolute bottom-2 left-2 w-4 h-4 border-l-2 border-b-2 border-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      <div className="absolute bottom-2 right-2 w-4 h-4 border-r-2 border-b-2 border-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {isNew && (
        <div className="absolute top-4 right-4 bg-primary text-primary-foreground text-xs font-medium px-2 py-1 rounded">
          New
        </div>
      )}
      
      <div className="mb-6">
        <Icon 
          className="w-8 h-8 text-foreground group-hover:text-primary transition-colors duration-300" 
          strokeWidth={1.5}
        />
      </div>
      
      <h3 className="text-xl font-semibold text-foreground mb-3 group-hover:text-primary transition-colors duration-300">
        {title}
      </h3>
      
      <p className="text-muted-foreground leading-relaxed text-sm group-hover:text-foreground transition-colors duration-300">
        {description}
      </p>
    </div>
  );
}