import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Check, Zap, ArrowRight, Sparkles } from "lucide-react";

const CTA = () => {
  const benefits = [
    "Setup in under 5 minutes",
    "No technical knowledge required", 
    "14-day free trial included",
    "Cancel anytime, no commitment"
  ];

  return (
    <section className="py-24 bg-gradient-hero relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:50px_50px]"></div>
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <Card className="max-w-4xl mx-auto border-0 shadow-brand bg-white/95 backdrop-blur">
          <CardContent className="p-12 text-center space-y-8">
            {/* Header */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 bg-brand-light px-4 py-2 rounded-full">
                <Sparkles className="w-4 h-4 text-brand-primary" />
                <span className="text-sm font-medium text-brand-primary">Limited Time Offer</span>
              </div>
              
              <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
                Ready to Transform Your
                <span className="bg-gradient-primary bg-clip-text text-transparent"> Store Search?</span>
              </h2>
              
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Join thousands of Shopify stores already using Findly to increase their conversions 
                and provide better customer experiences.
              </p>
            </div>

            {/* Benefits */}
            <div className="grid sm:grid-cols-2 gap-4 max-w-lg mx-auto">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-center gap-3 text-left">
                  <div className="flex-shrink-0 w-5 h-5 bg-green-100 rounded-full flex items-center justify-center">
                    <Check className="w-3 h-3 text-green-600" />
                  </div>
                  <span className="text-sm text-muted-foreground">{benefit}</span>
                </div>
              ))}
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="brand" size="lg" className="text-lg px-8 py-6">
                <Zap className="w-5 h-5 mr-2" />
                Start Your Free Trial
              </Button>
              <Button variant="brand-outline" size="lg" className="text-lg px-8 py-6">
                Schedule Demo
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>

            {/* Testimonial */}
            <div className="pt-8 border-t border-border">
              <blockquote className="text-lg italic text-muted-foreground mb-4">
                "Findly increased our search conversions by 73% in the first month. 
                Our customers can finally find exactly what they're looking for."
              </blockquote>
              <div className="flex items-center justify-center gap-4">
                <div className="w-12 h-12 bg-gradient-primary rounded-full flex items-center justify-center text-white font-semibold">
                  SJ
                </div>
                <div className="text-left">
                  <div className="font-semibold text-foreground">Sarah Johnson</div>
                  <div className="text-sm text-muted-foreground">Owner, Bella Fashion</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default CTA;