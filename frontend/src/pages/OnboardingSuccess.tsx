import React from 'react';
import { CheckCircle, ArrowRight, Play } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

const OnboardingSuccess = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <Card className="max-w-md w-full text-center">
        <div style={{ padding: 'var(--card-padding)' }}>
          <div className="w-16 h-16 bg-green-50 text-success rounded-full flex items-center justify-center mx-auto mb-6 relative">
            <CheckCircle size={32} />
            <div className="absolute inset-0 bg-green-400 rounded-full animate-ping opacity-20"></div>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">You&apos;re All Set!</h1>
          <p className="text-gray-500 mb-8">
            Your shopping assistant bot is live and ready to help your customers.
          </p>

          <div className="space-y-3">
            <Button
              className="w-full bg-primary hover:bg-blue-700 text-white font-medium transition-colors"
              size="lg"
              onClick={() => (window.location.pathname = '/dashboard')}
            >
              Go to Dashboard <ArrowRight size={18} className="ml-2" />
            </Button>

            <Button
              variant="outline"
              size="lg"
              className="w-full text-gray-700 font-medium transition-colors"
            >
              <Play size={18} className="mr-2 text-gray-400" /> Test Bot on Messenger
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default OnboardingSuccess;
