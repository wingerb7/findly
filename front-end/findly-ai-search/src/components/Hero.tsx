import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Search, Sparkles, Zap, BarChart3 } from "lucide-react";
import heroImage from "@/assets/hero-search.jpg";

const Hero = () => {
  return (
    <div className="relative min-h-screen bg-gradient-subtle overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-hero opacity-5"></div>
      <div className="absolute top-20 left-10 w-72 h-72 bg-brand-accent/20 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-brand-secondary/20 rounded-full blur-3xl animate-float" style={{animationDelay: '1s'}}></div>
      
      <div className="container mx-auto px-6 pt-20 pb-16 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center min-h-[80vh]">
          {/* Left Content */}
          <div className="space-y-8 animate-fade-in">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 bg-brand-light px-4 py-2 rounded-full border border-brand-accent/30">
                <Sparkles className="w-4 h-4 text-brand-primary" />
                <span className="text-sm font-medium text-brand-primary">AI-Powered Search</span>
              </div>
              
              <h1 className="text-5xl lg:text-6xl font-bold text-foreground leading-tight">
                Transform Your
                <span className="bg-gradient-primary bg-clip-text text-transparent"> Shopify Search</span>
              </h1>
              
              <p className="text-xl text-muted-foreground leading-relaxed max-w-lg">
                Empower your customers to find exactly what they want with natural language AI search. 
                Increase conversions and reduce bounce rates instantly.
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <Button variant="brand" size="lg" className="text-lg px-8 py-6">
                Start Free Trial
                <Zap className="w-5 h-5 ml-2" />
              </Button>
              <Button variant="brand-outline" size="lg" className="text-lg px-8 py-6">
                View Demo
              </Button>
            </div>
            
            <div className="flex items-center gap-8 pt-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">50%</div>
                <div className="text-sm text-muted-foreground">Faster Search</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">3x</div>
                <div className="text-sm text-muted-foreground">More Conversions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">1-Click</div>
                <div className="text-sm text-muted-foreground">Installation</div>
              </div>
            </div>
          </div>
          
          {/* Right Content */}
          <div className="relative animate-fade-in" style={{animationDelay: '0.3s'}}>
            <div className="relative">
              <img 
                src={heroImage} 
                alt="AI Search Interface" 
                className="w-full h-auto rounded-2xl shadow-large"
              />
              
              {/* Floating Search Widget */}
              <Card className="absolute -top-4 -left-4 p-4 shadow-brand bg-white/95 backdrop-blur">
                <div className="flex items-center gap-3">
                  <Search className="w-5 h-5 text-brand-primary" />
                  <span className="text-sm font-medium">Smart Search Active</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                </div>
              </Card>
              
              {/* Floating Results */}
              <Card className="absolute -bottom-4 -right-4 p-4 shadow-brand bg-white/95 backdrop-blur">
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-5 h-5 text-brand-primary" />
                  <div>
                    <div className="text-sm font-medium">Search Results</div>
                    <div className="text-xs text-muted-foreground">10 products found in 0.2s</div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;