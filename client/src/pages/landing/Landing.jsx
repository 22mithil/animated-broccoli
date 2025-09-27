import React from 'react';
import Hero from '@/components/landing/Hero';
import { LandingNavbar } from '@/components/landing/Navbar';

function Landing() {
  return (
    <div className="min-h-screen">
      <LandingNavbar />
      <Hero />
    </div>
  );
}

export default Landing;
