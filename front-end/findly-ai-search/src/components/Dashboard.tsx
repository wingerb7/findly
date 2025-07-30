import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  BarChart3, 
  Search, 
  TrendingUp, 
  Users, 
  Eye,
  Settings,
  Plus,
  ArrowRight
} from "lucide-react";

const Dashboard = () => {
  const topSearches = [
    { query: "blue summer dress", results: 24, conversions: 8 },
    { query: "wireless headphones", results: 15, conversions: 12 },
    { query: "running shoes for women", results: 31, conversions: 6 },
    { query: "organic skincare set", results: 18, conversions: 9 }
  ];

  const zeroResults = [
    "vintage leather jacket size small",
    "waterproof phone case clear",
    "sustainable yoga mat purple"
  ];

  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
            Powerful Analytics
            <span className="bg-gradient-primary bg-clip-text text-transparent"> Dashboard</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Get deep insights into customer search behavior and optimize your product catalog
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Main Dashboard Card */}
          <Card className="shadow-large border-0 overflow-hidden">
            <CardHeader className="bg-gradient-primary text-white">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl text-white">Search Analytics</CardTitle>
                  <CardDescription className="text-white/80">
                    Real-time insights from your Findly search
                  </CardDescription>
                </div>
                <Button variant="secondary" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>
              </div>
            </CardHeader>

            <CardContent className="p-6">
              {/* Key Metrics */}
              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <Card className="border-0 bg-brand-light/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <Search className="w-5 h-5 text-brand-primary" />
                      <span className="text-2xl font-bold text-foreground">1,247</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Total Searches Today</p>
                    <Badge variant="outline" className="mt-2 text-green-600 border-green-600">
                      +23% vs yesterday
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 bg-brand-light/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <TrendingUp className="w-5 h-5 text-brand-primary" />
                      <span className="text-2xl font-bold text-foreground">68%</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Conversion Rate</p>
                    <Badge variant="outline" className="mt-2 text-green-600 border-green-600">
                      +12% vs last week
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 bg-brand-light/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <Eye className="w-5 h-5 text-brand-primary" />
                      <span className="text-2xl font-bold text-foreground">0.18s</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Avg Response Time</p>
                    <Badge variant="outline" className="mt-2 text-blue-600 border-blue-600">
                      Excellent
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 bg-brand-light/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <Users className="w-5 h-5 text-brand-primary" />
                      <span className="text-2xl font-bold text-foreground">89%</span>
                    </div>
                    <p className="text-sm text-muted-foreground">User Satisfaction</p>
                    <Badge variant="outline" className="mt-2 text-green-600 border-green-600">
                      Outstanding
                    </Badge>
                  </CardContent>
                </Card>
              </div>

              <div className="grid lg:grid-cols-2 gap-8">
                {/* Top Searches */}
                <Card className="border-0 shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-brand-primary" />
                      Top Search Queries
                    </CardTitle>
                    <CardDescription>Most popular searches this week</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {topSearches.map((search, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium text-sm">{search.query}</p>
                          <div className="flex items-center gap-4 mt-1">
                            <span className="text-xs text-muted-foreground">
                              {search.results} results
                            </span>
                            <span className="text-xs text-green-600">
                              {search.conversions} conversions
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {Math.round((search.conversions / search.results) * 100)}%
                          </div>
                          <Progress 
                            value={(search.conversions / search.results) * 100} 
                            className="w-16 h-2 mt-1"
                          />
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                {/* Zero Results */}
                <Card className="border-0 shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Search className="w-5 h-5 text-orange-500" />
                      Zero Result Queries
                    </CardTitle>
                    <CardDescription>Searches that need attention</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {zeroResults.map((query, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium text-sm text-orange-900">{query}</p>
                          <p className="text-xs text-orange-600 mt-1">No products found</p>
                        </div>
                        <Button variant="outline" size="sm">
                          <Plus className="w-4 h-4 mr-1" />
                          Add Products
                        </Button>
                      </div>
                    ))}
                    
                    <div className="pt-4 border-t">
                      <Button variant="brand-ghost" className="w-full">
                        View All Zero Results
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;