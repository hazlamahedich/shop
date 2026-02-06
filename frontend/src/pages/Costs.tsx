import React from 'react';
import { DollarSign, TrendingUp, AlertCircle, Save } from 'lucide-react';

const Costs = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Costs & Budget</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Today's Cost</p>
          <h3 className="text-3xl font-bold text-gray-900 mt-2">$1.23</h3>
          <p className="text-xs text-green-600 mt-1 flex items-center">
            <TrendingUp size={12} className="mr-1" /> -5% vs yesterday
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Month-to-Date</p>
          <h3 className="text-3xl font-bold text-gray-900 mt-2">$18.45</h3>
          <p className="text-xs text-gray-500 mt-1">37% of monthly budget</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Projected</p>
          <h3 className="text-3xl font-bold text-gray-900 mt-2">$42.00</h3>
          <p className="text-xs text-green-600 mt-1">Well under $50 cap</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart Section (Mocked) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-gray-900">Daily Spend</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span className="w-3 h-3 bg-primary rounded-full"></span>
              <span>Spend</span>
              <span className="w-3 h-3 border border-gray-400 border-dashed rounded-full ml-2"></span>
              <span>Budget Cap</span>
            </div>
          </div>
          {/* Mock Chart Area */}
          <div className="h-64 bg-gray-50 rounded-lg flex items-end justify-between p-4 px-8 relative overflow-hidden">
            {/* Budget Cap Line */}
            <div className="absolute top-1/4 left-0 w-full border-t-2 border-dashed border-gray-300 pointer-events-none"></div>
            <span className="absolute top-[22%] right-2 text-xs text-gray-400">Cap $50</span>

            {/* Bars/Line Mock */}
            {[10, 15, 8, 12, 20, 25, 22, 30, 28, 35, 32, 40].map((h, i) => (
              <div
                key={i}
                className="w-1/2 bg-blue-100 rounded-t-sm relative group"
                style={{ height: `${h}%` }}
              >
                <div
                  className="absolute bottom-0 w-full bg-primary rounded-t-sm"
                  style={{ height: '100%' }}
                ></div>
                {/* Tooltip mock */}
                <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-gray-900 text-white text-xs py-1 px-2 rounded whitespace-nowrap z-10">
                  ${(h * 0.05).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Savings & Budget Settings */}
        <div className="space-y-6">
          {/* Comparison Widget */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-4">Cost Comparison</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium text-gray-700">Shop (You)</span>
                  <span className="font-bold text-success">$18.45</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-4">
                  <div className="bg-success h-4 rounded-full" style={{ width: '20%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium text-gray-700">ManyChat (Est.)</span>
                  <span className="font-bold text-danger">~$65.00</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-4">
                  <div className="bg-danger h-4 rounded-full" style={{ width: '75%' }}></div>
                </div>
              </div>
            </div>
            <div className="mt-6 p-3 bg-green-50 rounded-lg border border-green-100">
              <p className="text-sm text-green-800 font-medium text-center">
                You saved ~$46.55 this month!
              </p>
            </div>
          </div>

          {/* Budget Settings */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-4">Budget Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Cost Cap
                </label>
                <div className="relative">
                  <DollarSign
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                    size={16}
                  />
                  <input
                    type="number"
                    defaultValue="50.00"
                    className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1 flex items-center">
                  <AlertCircle size={12} className="mr-1" /> Hard stop when reached
                </p>
              </div>
              <button className="w-full py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center">
                <Save size={16} className="mr-2" /> Save Cap
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Costs;
