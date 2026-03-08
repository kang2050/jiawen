// Design: Tech-Warmth Futurism - 佳文宠物永生数字生命主页
import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import SpecsSection from "@/components/SpecsSection";
import TechnologySection from "@/components/TechnologySection";
import GallerySection from "@/components/GallerySection";
import EcosystemSection from "@/components/EcosystemSection";
import GuideSection from "@/components/GuideSection";
import StorySection from "@/components/StorySection";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <HeroSection />
      <SpecsSection />
      <TechnologySection />
      <GallerySection />
      <EcosystemSection />
      <GuideSection />
      <StorySection />
      <CTASection />
      <Footer />
    </div>
  );
}
