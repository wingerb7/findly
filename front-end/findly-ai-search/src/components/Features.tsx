import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Brain, 
  Zap, 
  BarChart3, 
  ShoppingBag, 
  Settings,
  Users,
  TrendingUp,
  MessageSquare
} from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Understanding",
      description: "Natural language processing understands complex search queries like 'blue dress under $50 for summer'",
      badge: "Core Feature"
    },
    {
      icon: Zap,
      title: "Instant Results",
      description: "Lightning-fast vector search delivers relevant products in under 0.2 seconds",
      badge: "Performance"
    },
    {
      icon: ShoppingBag,
      title: "Seamless Integration",
      description: "One-click installation with your Shopify store. Import all products automatically",
      badge: "Easy Setup"
    },
    {
      icon: BarChart3,
      title: "Smart Analytics",
      description: "Track search patterns, zero-result queries, and conversion metrics in real-time",
      badge: "Insights"
    },
    {
      icon: Search,
      title: "Contextual Search",
      description: "Understands product relationships, color matching, and style compatibility",
      badge: "AI Feature"
    },
    {
      icon: Settings,
      title: "Customizable Widget",
      description: "Match your store's design with customizable search interface and results display",
      badge: "Branding"
    }
  ];

  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
            Everything You Need for
            <span className="bg-gradient-primary bg-clip-text text-transparent"> Perfect Search</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Powerful AI features designed to transform how customers discover products in your store
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="border-0 shadow-soft hover:shadow-medium transition-all duration-300 group hover:-translate-y-1"
            >
              <CardHeader className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="p-3 bg-brand-light rounded-lg group-hover:bg-gradient-primary group-hover:text-white transition-all duration-300">
                    <feature.icon className="w-6 h-6 text-brand-primary group-hover:text-white" />
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {feature.badge}
                  </Badge>
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stats Section */}
        <div className="bg-gradient-subtle rounded-2xl p-8 lg:p-12">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2">
                <TrendingUp className="w-8 h-8 text-brand-primary" />
                <span className="text-4xl font-bold text-foreground">85%</span>
              </div>
              <p className="text-muted-foreground">Average conversion increase</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2">
                <Users className="w-8 h-8 text-brand-primary" />
                <span className="text-4xl font-bold text-foreground">10k+</span>
              </div>
              <p className="text-muted-foreground">Happy store owners</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2">
                <MessageSquare className="w-8 h-8 text-brand-primary" />
                <span className="text-4xl font-bold text-foreground">50M+</span>
              </div>
              <p className="text-muted-foreground">Searches processed</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;