import { useState } from 'react';
import { 
  DollarSign, 
  Download, 
  CreditCard, 
  FileText, 
  Receipt,
  TrendingUp,
  Calendar,
  Settings,
  Mail,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Info,
  Wallet
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Alert, AlertDescription } from './components/ui/alert';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import backgroundImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

// Invoice data structure
interface Invoice {
  invoice_id: string;
  invoice_number: string;
  link_id: string;
  amount: number;
  platform_fee: number;
  mentor_portion: number;
  status: 'pending' | 'held' | 'released' | 'paid' | 'disputed';
  paid_date?: string;
  released_date?: string;
  created_date: string;
  service_description: string;
}

// TODO: Replace with actual API call
const fetchInvoicesFromBackend = async (): Promise<Invoice[]> => {
  // This should be replaced with actual API call to backend
  // Example: const response = await fetch('/api/mentorship/v1/invoices');
  // return response.json();
  return [];
};

export default function App() {
  const [selectedSection, setSelectedSection] = useState('earnings');
  const [taxYear, setTaxYear] = useState(new Date().getFullYear().toString());
  const [taxCountry, setTaxCountry] = useState('United Kingdom');
  const [stripeConnected] = useState(false); // TODO: Get from backend/session
  const [statusFilter, setStatusFilter] = useState<Invoice['status'][]>(['held', 'released']);

  // TODO: Replace with actual data fetching
  const allInvoices: Invoice[] = [];
  const paidInvoices = allInvoices.filter(inv => ['paid', 'held', 'released'].includes(inv.status));
  
  const totalGross = paidInvoices.reduce((sum, inv) => sum + inv.amount, 0);
  const totalPlatformFees = paidInvoices.reduce((sum, inv) => sum + inv.platform_fee, 0);
  const totalNet = paidInvoices.reduce((sum, inv) => sum + inv.mentor_portion, 0);
  const totalReleased = allInvoices.filter(inv => inv.status === 'released').reduce((sum, inv) => sum + inv.mentor_portion, 0);
  const totalPending = allInvoices.filter(inv => inv.status === 'held').reduce((sum, inv) => sum + inv.mentor_portion, 0);

  // Monthly breakdown
  const getMonthlyData = (invoices: Invoice[]) => {
    const monthly: { [key: string]: { gross: number; fees: number; net: number; count: number } } = {};
    
    invoices.forEach(inv => {
      if (inv.paid_date && ['paid', 'held', 'released'].includes(inv.status)) {
        const monthKey = inv.paid_date.substring(0, 7); // YYYY-MM
        if (!monthly[monthKey]) {
          monthly[monthKey] = { gross: 0, fees: 0, net: 0, count: 0 };
        }
        monthly[monthKey].gross += inv.amount;
        monthly[monthKey].fees += inv.platform_fee;
        monthly[monthKey].net += inv.mentor_portion;
        monthly[monthKey].count += 1;
      }
    });
    
    return monthly;
  };

  const monthlyData = getMonthlyData(allInvoices);
  const sortedMonths = Object.keys(monthlyData).sort().slice(-12);
  
  const chartData = sortedMonths.map(month => {
    const date = new Date(month + '-01');
    const monthName = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    return {
      month: monthName,
      earnings: monthlyData[month].net,
      fees: monthlyData[month].fees
    };
  });

  const currentMonth = new Date().toISOString().substring(0, 7);
  const currentMonthStats = monthlyData[currentMonth] || { gross: 0, fees: 0, net: 0, count: 0 };

  // Tax year filtering
  const taxYearInvoices = allInvoices.filter(inv => 
    inv.paid_date?.startsWith(taxYear) && ['paid', 'held', 'released'].includes(inv.status)
  );
  
  const taxYearGross = taxYearInvoices.reduce((sum, inv) => sum + inv.amount, 0);
  const taxYearFees = taxYearInvoices.reduce((sum, inv) => sum + inv.platform_fee, 0);
  const taxYearNet = taxYearInvoices.reduce((sum, inv) => sum + inv.mentor_portion, 0);

  const taxYearMonthly = getMonthlyData(taxYearInvoices);

  // Get available years
  const availableYears = Array.from(new Set(
    allInvoices
      .filter(inv => inv.paid_date)
      .map(inv => inv.paid_date!.substring(0, 4))
  )).sort().reverse();

  // If no years available, use current year
  if (availableYears.length === 0) {
    availableYears.push(new Date().getFullYear().toString());
  }

  // CSV download functions
  const downloadCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      alert('No data available to download');
      return;
    }
    
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row => Object.values(row).join(','));
    const csv = [headers, ...rows].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportPayoutHistory = () => {
    const releasedInvoices = allInvoices.filter(inv => inv.status === 'released');
    const data = releasedInvoices.map(inv => ({
      'Payout Date': inv.released_date || 'N/A',
      'Invoice': inv.invoice_number,
      'Amount': `£${inv.mentor_portion.toFixed(2)}`,
      'Method': 'Stripe Connect',
      'Reference': `PAY-${inv.invoice_id}`
    }));
    downloadCSV(data, `payout_history_${new Date().toISOString().split('T')[0]}.csv`);
  };

  const exportTaxSummary = () => {
    const data = Object.keys(taxYearMonthly).sort().map(month => {
      const stats = taxYearMonthly[month];
      const date = new Date(month + '-01');
      return {
        'Month': date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        'Gross Income': `£${stats.gross.toFixed(2)}`,
        'Platform Fees': `£${stats.fees.toFixed(2)}`,
        'Net Income': `£${stats.net.toFixed(2)}`,
        'Transactions': stats.count
      };
    });
    downloadCSV(data, `tax_summary_${taxYear}.csv`);
  };

  const exportFullLedger = () => {
    const data = allInvoices.map(inv => ({
      'Date': inv.paid_date || inv.created_date,
      'Invoice': inv.invoice_number,
      'Link ID': inv.link_id,
      'Description': inv.service_description,
      'Gross': `£${inv.amount.toFixed(2)}`,
      'Fee': `£${inv.platform_fee.toFixed(2)}`,
      'Net': `£${inv.mentor_portion.toFixed(2)}`,
      'Status': inv.status
    }));
    downloadCSV(data, `complete_ledger_${new Date().toISOString().split('T')[0]}.csv`);
  };

  // Filtered ledger
  const filteredLedger = statusFilter.length > 0 
    ? allInvoices.filter(inv => statusFilter.includes(inv.status))
    : allInvoices;

  return (
    <div className="min-h-screen relative" style={{ backgroundColor: '#2d2d2d' }}>
      {/* Background structure matching PNG - dark top bar, image center, dark bottom bar */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          background: `
            linear-gradient(to bottom, 
              #2d2d2d 0%, 
              #2d2d2d 20%, 
              transparent 20%, 
              transparent 80%, 
              #2d2d2d 80%, 
              #2d2d2d 100%
            ),
            url(${backgroundImage})
          `,
          backgroundSize: 'auto, cover',
          backgroundPosition: 'center, center',
          backgroundRepeat: 'no-repeat, no-repeat'
        }}
      />
      
      {/* Semi-transparent overlay for readability */}
      <div className="fixed inset-0 z-0 bg-slate-900/75" />
      
      {/* Content */}
      <div className="relative z-10 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <DollarSign className="w-10 h-10 text-emerald-400" />
              <div>
                <h1 className="text-white">Financial Dashboard</h1>
                <p className="text-slate-300">Track earnings, manage payouts, access tax documents</p>
              </div>
            </div>
          </div>

          <Separator className="bg-slate-600" />

          {/* Section Selector */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={selectedSection === 'earnings' ? 'default' : 'outline'}
                  onClick={() => setSelectedSection('earnings')}
                  className="flex items-center gap-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  Earnings Overview
                </Button>
                <Button
                  variant={selectedSection === 'payouts' ? 'default' : 'outline'}
                  onClick={() => setSelectedSection('payouts')}
                  className="flex items-center gap-2"
                >
                  <CreditCard className="w-4 h-4" />
                  Payout History & Stripe
                </Button>
                <Button
                  variant={selectedSection === 'tax' ? 'default' : 'outline'}
                  onClick={() => setSelectedSection('tax')}
                  className="flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Tax Documentation by Year
                </Button>
                <Button
                  variant={selectedSection === 'ledger' ? 'default' : 'outline'}
                  onClick={() => setSelectedSection('ledger')}
                  className="flex items-center gap-2"
                >
                  <Receipt className="w-4 h-4" />
                  Transaction Ledger
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* SECTION 1: EARNINGS OVERVIEW */}
          {selectedSection === 'earnings' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Earnings Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                      <div className="text-sm text-emerald-700 mb-1">Total Earnings (All Time)</div>
                      <div className="text-emerald-900">£{totalNet.toFixed(2)}</div>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-sm text-blue-700 mb-1">Released to You</div>
                      <div className="text-blue-900">£{totalReleased.toFixed(2)}</div>
                    </div>
                    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="text-sm text-amber-700 mb-1">Pending Release</div>
                      <div className="text-amber-900">£{totalPending.toFixed(2)}</div>
                      <div className="text-xs text-amber-600 mt-1">Held pending completion</div>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-sm text-slate-700 mb-1">Platform Fees Paid</div>
                      <div className="text-slate-900">£{totalPlatformFees.toFixed(2)}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Separator />

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Monthly Earnings Breakdown</CardTitle>
                    <CardDescription>Last 12 months</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip 
                            formatter={(value: number) => `£${value.toFixed(2)}`}
                            contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                          />
                          <Legend />
                          <Bar dataKey="earnings" name="Your Earnings (80%)" fill="#32CD32" stackId="a" />
                          <Bar dataKey="fees" name="Platform Fee (20%)" fill="#FFD700" stackId="a" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-64 text-slate-500">
                        <Info className="w-5 h-5 mr-2" />
                        No earnings data yet
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Current Month</CardTitle>
                    <CardDescription>{new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {currentMonthStats.count > 0 ? (
                      <>
                        <div>
                          <div className="text-sm text-slate-600">Gross Session Fees</div>
                          <div className="text-slate-900">£{currentMonthStats.gross.toFixed(2)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-600">Platform Fee (20%)</div>
                          <div className="text-slate-900">£{currentMonthStats.fees.toFixed(2)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-600">Your Net Earnings</div>
                          <div className="text-slate-900">£{currentMonthStats.net.toFixed(2)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-600">Transactions</div>
                          <div className="text-slate-900">{currentMonthStats.count}</div>
                        </div>
                      </>
                    ) : (
                      <div className="text-sm text-slate-500">No transactions this month</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* SECTION 2: PAYOUT HISTORY */}
          {selectedSection === 'payouts' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wallet className="w-5 h-5" />
                    Payout History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {allInvoices.filter(inv => inv.status === 'released').length > 0 ? (
                    <div className="space-y-4">
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2 text-sm text-slate-600">Payout Date</th>
                              <th className="text-left p-2 text-sm text-slate-600">Invoice</th>
                              <th className="text-right p-2 text-sm text-slate-600">Amount</th>
                              <th className="text-left p-2 text-sm text-slate-600">Method</th>
                              <th className="text-left p-2 text-sm text-slate-600">Reference</th>
                            </tr>
                          </thead>
                          <tbody>
                            {allInvoices.filter(inv => inv.status === 'released').slice(0, 10).map((inv) => (
                              <tr key={inv.invoice_id} className="border-b hover:bg-slate-50">
                                <td className="p-2 text-sm">{inv.released_date || 'N/A'}</td>
                                <td className="p-2 text-sm">{inv.invoice_number}</td>
                                <td className="p-2 text-sm text-right">£{inv.mentor_portion.toFixed(2)}</td>
                                <td className="p-2 text-sm">Stripe Connect</td>
                                <td className="p-2 text-sm text-slate-500">PAY-{inv.invoice_id}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={exportPayoutHistory} variant="outline" className="flex items-center gap-2">
                          <Download className="w-4 h-4" />
                          Download Statement (CSV)
                        </Button>
                        <div className="flex-1" />
                        <Badge variant="secondary" className="px-3 py-1">
                          Total released: £{totalReleased.toFixed(2)}
                        </Badge>
                      </div>
                    </div>
                  ) : (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        No payouts released yet. Funds are released after both you and the mentee confirm service completion.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Separator />

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="w-5 h-5" />
                    Stripe Connect Account
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {stripeConnected ? (
                    <div className="space-y-4">
                      <Alert className="bg-emerald-50 border-emerald-200">
                        <CheckCircle className="h-4 w-4 text-emerald-600" />
                        <AlertDescription className="text-emerald-900">
                          Your Stripe Express account is connected and active
                        </AlertDescription>
                      </Alert>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="mb-3 text-slate-900">Account Benefits</h4>
                          <ul className="space-y-2 text-sm text-slate-600">
                            <li className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span>Automated payouts after service completion</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span>Direct deposit to your bank account</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span>Real-time earnings tracking</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span>Secure payment processing</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span>Automatic payout records</span>
                            </li>
                          </ul>
                        </div>

                        <div className="space-y-2">
                          <Button className="w-full flex items-center justify-center gap-2">
                            <Settings className="w-4 h-4" />
                            Manage Stripe Account
                          </Button>
                          <Button variant="outline" className="w-full flex items-center justify-center gap-2">
                            <Mail className="w-4 h-4" />
                            Update Banking Details
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Alert className="bg-amber-50 border-amber-200">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <AlertDescription className="text-amber-900">
                          Stripe Connect account not yet set up
                        </AlertDescription>
                      </Alert>

                      <div className="space-y-3">
                        <h4 className="text-slate-900">Setup Required</h4>
                        <p className="text-sm text-slate-600">
                          To receive payouts, you need to complete your Stripe Connect onboarding:
                        </p>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-slate-600">
                          <li>Click the button below to start</li>
                          <li>Provide your banking information</li>
                          <li>Complete identity verification</li>
                          <li>Start receiving automated payouts!</li>
                        </ol>
                        <p className="text-sm text-slate-500">Processing time: Usually 5-10 minutes</p>
                        <Button className="w-full flex items-center justify-center gap-2">
                          <ExternalLink className="w-4 h-4" />
                          Connect Stripe Account
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* SECTION 3: TAX DOCUMENTATION */}
          {selectedSection === 'tax' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Tax Documentation & Earnings Summaries
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm mb-2 text-slate-700">Select Tax Year</label>
                      <Select value={taxYear} onValueChange={setTaxYear}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {availableYears.map(year => (
                            <SelectItem key={year} value={year}>{year}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="block text-sm mb-2 text-slate-700">Tax Jurisdiction</label>
                      <Select value={taxCountry} onValueChange={setTaxCountry}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="United Kingdom">United Kingdom</SelectItem>
                          <SelectItem value="United States">United States</SelectItem>
                          <SelectItem value="Canada">Canada</SelectItem>
                          <SelectItem value="Australia">Australia</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Alert className="bg-red-50 border-red-200">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-900">
                  <div className="space-y-2">
                    <p className="font-semibold">⚠️ IMPORTANT TAX DISCLAIMER</p>
                    <p><strong>IntelliCV is NOT responsible for your tax affairs.</strong></p>
                    <ul className="list-disc list-inside space-y-1 text-sm mt-2">
                      <li>This earnings summary is provided for YOUR RECORDS ONLY</li>
                      <li>We do NOT provide tax advice or tax filing services</li>
                      <li>Tax obligations vary by country, state/province, and individual circumstances</li>
                      <li>You are solely responsible for reporting income and paying taxes</li>
                      <li><strong>Consult a qualified tax professional</strong> for tax advice specific to your situation</li>
                    </ul>
                    <p className="text-sm mt-2">
                      This document is a summary of platform earnings only and should NOT be considered a tax document.
                    </p>
                  </div>
                </AlertDescription>
              </Alert>

              <Separator />

              <Card>
                <CardHeader>
                  <CardTitle>{taxYear} Earnings Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  {taxYearInvoices.length > 0 ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-slate-50 rounded-lg border">
                          <div className="text-sm text-slate-600 mb-1">Total Income (Gross)</div>
                          <div className="text-slate-900">£{taxYearGross.toFixed(2)}</div>
                        </div>
                        <div className="p-4 bg-slate-50 rounded-lg border">
                          <div className="text-sm text-slate-600 mb-1">Platform Fees Paid</div>
                          <div className="text-slate-900">£{taxYearFees.toFixed(2)}</div>
                        </div>
                        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                          <div className="text-sm text-emerald-700 mb-1">Net Mentorship Income</div>
                          <div className="text-emerald-900">£{taxYearNet.toFixed(2)}</div>
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <h4 className="mb-3 text-slate-900">Monthly Breakdown - {taxYear}</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left p-2 text-sm text-slate-600">Month</th>
                                <th className="text-right p-2 text-sm text-slate-600">Gross Income</th>
                                <th className="text-right p-2 text-sm text-slate-600">Platform Fees</th>
                                <th className="text-right p-2 text-sm text-slate-600">Net Income</th>
                                <th className="text-center p-2 text-sm text-slate-600">Transactions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.keys(taxYearMonthly).sort().map(month => {
                                const stats = taxYearMonthly[month];
                                const date = new Date(month + '-01');
                                const monthName = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
                                return (
                                  <tr key={month} className="border-b hover:bg-slate-50">
                                    <td className="p-2 text-sm">{monthName}</td>
                                    <td className="p-2 text-sm text-right">£{stats.gross.toFixed(2)}</td>
                                    <td className="p-2 text-sm text-right">£{stats.fees.toFixed(2)}</td>
                                    <td className="p-2 text-sm text-right">£{stats.net.toFixed(2)}</td>
                                    <td className="p-2 text-sm text-center">{stats.count}</td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <h4 className="mb-3 text-slate-900">Download {taxYear} Tax Summary</h4>
                        <div className="flex flex-wrap gap-2">
                          <Button onClick={exportTaxSummary} variant="outline" className="flex items-center gap-2">
                            <Download className="w-4 h-4" />
                            Download {taxYear} Summary (CSV)
                          </Button>
                          <Button onClick={exportFullLedger} variant="outline" className="flex items-center gap-2">
                            <Download className="w-4 h-4" />
                            Export Full Ledger
                          </Button>
                        </div>
                      </div>

                      <Alert className="bg-blue-50 border-blue-200">
                        <Info className="h-4 w-4 text-blue-600" />
                        <AlertDescription className="text-blue-900">
                          <div className="space-y-2">
                            <p className="font-semibold">💡 General Tax Guidance ({taxCountry})</p>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                              <li>This is self-employment income and may be subject to income tax and self-employment tax</li>
                              <li>Platform fees paid (£{taxYearFees.toFixed(2)}) may be deductible as business expenses (consult tax professional)</li>
                              <li>You may need to make quarterly estimated tax payments depending on your jurisdiction</li>
                              <li>Keep records of all business expenses related to mentorship activities</li>
                              <li>Consider consulting a tax professional for specific advice</li>
                            </ul>
                            <p className="text-sm mt-2">
                              <strong>For {taxCountry} tax filers:</strong> Tax year typically runs {taxYear}-01-01 to {taxYear}-12-31. 
                              Check with your local tax authority for specific requirements.
                            </p>
                          </div>
                        </AlertDescription>
                      </Alert>
                    </div>
                  ) : (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        No earnings data for tax year {taxYear}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* SECTION 4: TRANSACTION LEDGER */}
          {selectedSection === 'ledger' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Receipt className="w-5 h-5" />
                    Complete Transaction Ledger
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex flex-wrap gap-4">
                      <div className="flex-1 min-w-[200px]">
                        <label className="block text-sm mb-2 text-slate-700">Filter by Status</label>
                        <div className="flex flex-wrap gap-2">
                          {['pending', 'held', 'released', 'paid', 'disputed'].map(status => (
                            <Button
                              key={status}
                              size="sm"
                              variant={statusFilter.includes(status as Invoice['status']) ? 'default' : 'outline'}
                              onClick={() => {
                                if (statusFilter.includes(status as Invoice['status'])) {
                                  setStatusFilter(statusFilter.filter(s => s !== status));
                                } else {
                                  setStatusFilter([...statusFilter, status as Invoice['status']]);
                                }
                              }}
                            >
                              {status}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2 text-sm text-slate-600">Date</th>
                            <th className="text-left p-2 text-sm text-slate-600">Invoice</th>
                            <th className="text-left p-2 text-sm text-slate-600">Description</th>
                            <th className="text-right p-2 text-sm text-slate-600">Gross (£)</th>
                            <th className="text-right p-2 text-sm text-slate-600">Fee (£)</th>
                            <th className="text-right p-2 text-sm text-slate-600">Your Earnings (£)</th>
                            <th className="text-center p-2 text-sm text-slate-600">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredLedger.slice(0, 50).map((inv) => (
                            <tr key={inv.invoice_id} className="border-b hover:bg-slate-50">
                              <td className="p-2 text-sm">{inv.paid_date || inv.created_date}</td>
                              <td className="p-2 text-sm">{inv.invoice_number}</td>
                              <td className="p-2 text-sm">{inv.service_description}</td>
                              <td className="p-2 text-sm text-right">£{inv.amount.toFixed(2)}</td>
                              <td className="p-2 text-sm text-right">£{inv.platform_fee.toFixed(2)}</td>
                              <td className="p-2 text-sm text-right">£{inv.mentor_portion.toFixed(2)}</td>
                              <td className="p-2 text-center">
                                <Badge 
                                  variant={inv.status === 'released' ? 'default' : 'secondary'}
                                  className={
                                    inv.status === 'released' ? 'bg-emerald-100 text-emerald-800' :
                                    inv.status === 'held' ? 'bg-amber-100 text-amber-800' :
                                    'bg-slate-100 text-slate-800'
                                  }
                                >
                                  {inv.status}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="flex items-center justify-between">
                      <p className="text-sm text-slate-500">
                        Showing {Math.min(50, filteredLedger.length)} of {filteredLedger.length} transactions
                      </p>
                      <Button onClick={exportFullLedger} variant="outline" className="flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Export Full Ledger to CSV
                      </Button>
                    </div>

                    {filteredLedger.length === 0 && (
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          No transactions match the selected filters.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Footer */}
          <Separator />
          <div className="text-center text-sm text-slate-500 pb-6">
            <p>💰 Financial Dashboard | Earnings, Payouts & Tax Documentation | IntelliCV Mentor Portal</p>
          </div>
        </div>
      </div>
    </div>
  );
}