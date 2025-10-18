import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { useState } from "react";
import { trpc } from "@/lib/trpc";

export default function Home() {
  const { user, isAuthenticated, logout } = useAuth();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<{ summary: string; churnRate: number; customerCount: number } | null>(null);
  
  const queryMutation = trpc.churn.queryChurnRate.useMutation({
    onSuccess: (data) => {
      setResponse(data);
    },
    onError: (error) => {
      console.error("Error processing query:", error);
      setResponse(null);
    },
  });

  const handleQuery = async () => {
    if (!query.trim()) return;
    queryMutation.mutate({ query });
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Customer Churn Prediction Agent</CardTitle>
            <CardDescription>Powered by Google Gemini & XGBoost</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600">Sign in to access the churn prediction dashboard and analyze customer data.</p>
            <Button 
              onClick={() => window.location.href = getLoginUrl()} 
              className="w-full"
            >
              Sign In with Manus
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-6 flex justify-between items-center">
          <div className="flex items-center gap-3">
            {APP_LOGO && <img src={APP_LOGO} alt="Logo" className="h-8 w-8" />}
            <h1 className="text-2xl font-bold text-gray-900">{APP_TITLE}</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Welcome, {user?.name || "User"}</span>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Query Panel */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle>Ask About Churn</CardTitle>
                <CardDescription>Query the AI agent to analyze customer churn</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Your Question</label>
                  <Input
                    placeholder="e.g., What is the current rate of customer churn?"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleQuery()}
                    disabled={queryMutation.isPending}
                  />
                </div>
                <Button 
                  onClick={handleQuery} 
                  disabled={queryMutation.isPending || !query.trim()}
                  className="w-full"
                >
                  {queryMutation.isPending ? "Analyzing..." : "Analyze"}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {response ? (
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Results</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Churn Rate</p>
                      <p className="text-3xl font-bold text-blue-600">{response.churnRate.toFixed(2)}%</p>
                    </div>
                    <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Customers Analyzed</p>
                      <p className="text-3xl font-bold text-indigo-600">{response.customerCount}</p>
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
                    <p className="text-gray-700 leading-relaxed">{response.summary}</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-gray-500">Ask a question about customer churn to see analysis results here.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

