import React, { useState } from 'react';
import { financeService } from '../../../services/financeService';
import {
  ShieldAlert,
  AlertTriangle,
  Lock,
  FileCheck,
  CheckCircle2,
  Share2,
  DollarSign,
  ArrowRight,
  TrendingUp,
  Landmark,
  FileText,
  Search,
  ExternalLink,
} from 'lucide-react';

interface SuspiciousTransaction {
  id: string;
  txId: string;
  sender: string;
  senderAccount: string;
  recipient: string;
  recipientAccount: string;
  amount: string;
  rawAmount: number;
  channel: 'SWIFT' | 'RTGS' | 'UPI' | 'NEFT';
  riskScore: number;
  muleProbability: number;
  status: 'PENDING_SETTLEMENT' | 'HELD_IN_ESCROW' | 'SETTLED' | 'BLOCKED';
  flags: string[];
}

export const FraudAnalystWorkflow: React.FC = () => {
  const [transactions, setTransactions] = useState<SuspiciousTransaction[]>([
    {
      id: 'TX-F-01',
      txId: 'TXN-SWIFT-99182',
      sender: 'Municipal Water SCADA Treasury',
      senderAccount: '9988112233',
      recipient: 'DarkMule Wallet Syndicate',
      recipientAccount: '1122446688',
      amount: '₹ 4,500,000',
      rawAmount: 4500000,
      channel: 'SWIFT',
      riskScore: 94,
      muleProbability: 0.96,
      status: 'PENDING_SETTLEMENT',
      flags: ['Rapid Velocity Outflow', 'Tor Exit Node Node', 'Unregistered Offshore Payee'],
    },
    {
      id: 'TX-F-02',
      txId: 'TXN-RTGS-33109',
      sender: 'Apex Transit Gantry Sub-Treasury',
      senderAccount: '7766554433',
      recipient: 'Ghost Broker Shell LLC',
      recipientAccount: '5544332211',
      amount: '₹ 1,850,000',
      rawAmount: 1850000,
      channel: 'RTGS',
      riskScore: 82,
      muleProbability: 0.88,
      status: 'PENDING_SETTLEMENT',
      flags: ['Dormant Account Awakening', 'Structured Round Numbers'],
    },
    {
      id: 'TX-F-03',
      txId: 'TXN-UPI-77124',
      sender: 'Metro Rail Fare Gantry Pool',
      senderAccount: '2233445566',
      recipient: 'P2P Mule Aggregator 09',
      recipientAccount: '9900112233',
      amount: '₹ 98,000',
      rawAmount: 98000,
      channel: 'UPI',
      riskScore: 78,
      muleProbability: 0.79,
      status: 'PENDING_SETTLEMENT',
      flags: ['Burst Micro-Structuring', 'Device ID Churn'],
    },
  ]);

  const [selectedTxId, setSelectedTxId] = useState<string>('TX-F-01');
  const [sarFiled, setSarFiled] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedTx = transactions.find((t) => t.id === selectedTxId) || transactions[0];

  const handleHoldEscrow = async (tx: SuspiciousTransaction) => {
    try {
      await financeService.freezeAccount(tx.recipientAccount, `Mule Escrow Hold - ${tx.txId}`);
    } catch {
      // simulated fallback
    }
    setTransactions((prev) =>
      prev.map((t) => (t.id === tx.id ? { ...t, status: 'HELD_IN_ESCROW' } : t))
    );
    setFeedback(`PRE-SETTLEMENT ESCROW HOLD ENGAGED: Outflow of ${tx.amount} halted before clearing.`);
    setTimeout(() => setFeedback(null), 4500);
  };

  const handleFileSAR = () => {
    setSarFiled(true);
    setFeedback(`REGULATORY SAR FILED: FIU-IND Case #SAR-2026-${Math.floor(100000 + Math.random() * 900000)} generated.`);
    setTimeout(() => setFeedback(null), 5000);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <Landmark className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wide">
                FINANCIAL INTELLIGENCE & AML UNIT
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold animate-pulse">
                ● HIGH-RISK WIRES DETECTED
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">
              Pre-Settlement Mule Interception & SAR Dossier
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Real-Time Clearing Gatekeeper • Graph Topology ML & Velocity Analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleFileSAR}
            disabled={sarFiled}
            className={`px-4 py-2 rounded-xl font-mono text-xs font-bold flex items-center gap-2 transition shadow-lg ${
              sarFiled
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                : 'bg-purple-600 hover:bg-purple-500 text-white shadow-purple-500/20'
            }`}
          >
            <FileText className="w-4 h-4" />
            {sarFiled ? 'SAR Registered with FIU' : 'File Regulatory SAR (FIU-IND)'}
          </button>
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Main Grid: Wire Queue + Mule Graph & Action Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Wire Queue (4 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Pre-Settlement Queue</span>
            <span>{transactions.length} Wires Flagged</span>
          </div>

          <div className="space-y-3">
            {transactions.map((tx) => {
              const isSelected = tx.id === selectedTx.id;
              return (
                <div
                  key={tx.id}
                  onClick={() => setSelectedTxId(tx.id)}
                  className={`p-4 rounded-xl border font-mono cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-amber-500 shadow-md ring-1 ring-amber-500/50'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
                        <span>{tx.txId}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                          {tx.channel}
                        </span>
                      </div>
                      <div className="text-sm font-black text-amber-400 mt-1">{tx.amount}</div>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-mono font-black text-rose-400 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded">
                        RISK {tx.riskScore}/100
                      </span>
                      <div className="text-[9px] font-mono text-slate-400 mt-1">
                        Mule: {(tx.muleProbability * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-400 mt-2 truncate">
                    {tx.sender} → <strong className="text-slate-200">{tx.recipient}</strong>
                  </div>

                  <div className="flex items-center justify-between pt-2 mt-2 border-t border-slate-800/60 text-[10px]">
                    <span
                      className={`px-2 py-0.5 rounded font-bold ${
                        tx.status === 'HELD_IN_ESCROW'
                          ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {tx.status.replace('_', ' ')}
                    </span>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleHoldEscrow(tx);
                      }}
                      disabled={tx.status === 'HELD_IN_ESCROW'}
                      className={`px-2.5 py-1 rounded-lg font-mono text-[10px] font-bold transition ${
                        tx.status === 'HELD_IN_ESCROW'
                          ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                          : 'bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold'
                      }`}
                    >
                      {tx.status === 'HELD_IN_ESCROW' ? 'Held' : 'Hold Escrow'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3-Hop Money Mule Graph & Investigation (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Wire Detail Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
                  <Share2 className="w-4 h-4 text-amber-400" />
                  Mule Network Topology & 3-Hop Graph
                </h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">
                  Analyzing transaction {selectedTx.txId} ({selectedTx.amount})
                </p>
              </div>

              <button
                onClick={() => handleHoldEscrow(selectedTx)}
                disabled={selectedTx.status === 'HELD_IN_ESCROW'}
                className={`px-4 py-2 rounded-xl font-mono text-xs font-bold flex items-center gap-2 shadow-lg transition ${
                  selectedTx.status === 'HELD_IN_ESCROW'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 cursor-default'
                    : 'bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white shadow-rose-500/20'
                }`}
              >
                <Lock className="w-4 h-4" />
                {selectedTx.status === 'HELD_IN_ESCROW' ? 'Escrow Frozen (Held)' : '1-Tap Pre-Settlement Escrow Hold'}
              </button>
            </div>

            {/* Interactive 3-Hop Graph Visualization */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold tracking-wider">
                Graph Traversal: Layered Dispersion Pattern
              </div>

              <div className="flex flex-col md:flex-row items-center justify-between gap-3 font-mono text-xs">
                {/* Hop 0: Victim Source */}
                <div className="bg-slate-900 border border-emerald-500/40 rounded-xl p-3 text-center flex-1 w-full">
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 uppercase font-bold">
                    Hop 0: Compromised Origin
                  </span>
                  <div className="font-bold text-slate-100 mt-1 truncate">{selectedTx.sender}</div>
                  <div className="text-[10px] text-slate-400">Acc: {selectedTx.senderAccount}</div>
                </div>

                <div className="text-rose-400 flex items-center justify-center">
                  <ArrowRight className="w-5 h-5" />
                </div>

                {/* Hop 1: Primary Mule Layer */}
                <div className="bg-slate-900 border border-rose-500/50 rounded-xl p-3 text-center flex-1 w-full ring-1 ring-rose-500/30">
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 uppercase font-bold">
                    Hop 1: Mule Recipient
                  </span>
                  <div className="font-bold text-slate-100 mt-1 truncate">{selectedTx.recipient}</div>
                  <div className="text-[10px] text-rose-300">Acc: {selectedTx.recipientAccount}</div>
                </div>

                <div className="text-amber-400 flex items-center justify-center">
                  <ArrowRight className="w-5 h-5" />
                </div>

                {/* Hop 2: Offshore Crypto Bridge */}
                <div className="bg-slate-900 border border-purple-500/40 rounded-xl p-3 text-center flex-1 w-full">
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-400 uppercase font-bold">
                    Hop 2: Crypto Off-Ramp
                  </span>
                  <div className="font-bold text-slate-100 mt-1">XMR Mixer Swarm</div>
                  <div className="text-[10px] text-purple-300">Wallet: 0x9f...4a1</div>
                </div>
              </div>

              {/* Anomaly flags pill row */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-900">
                {selectedTx.flags.map((flag, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono px-2.5 py-1 rounded-lg bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1.5"
                  >
                    <AlertTriangle className="w-3 h-3 text-rose-400" />
                    {flag}
                  </span>
                ))}
              </div>
            </div>

            {/* Risk Factor Scorecard */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-[10px] font-mono text-slate-400">Velocity Surge</div>
                <div className="text-lg font-bold font-mono text-rose-400 mt-0.5">14 Wires / 60s</div>
                <div className="text-[9px] font-mono text-slate-500">Normal: 0.1 / hr</div>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-[10px] font-mono text-slate-400">Device Fingerprint</div>
                <div className="text-lg font-bold font-mono text-amber-400 mt-0.5">TOR Exit 92.1</div>
                <div className="text-[9px] font-mono text-slate-500">Unrecognized ASN</div>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-[10px] font-mono text-slate-400">Beneficiary Age</div>
                <div className="text-lg font-bold font-mono text-cyan-400 mt-0.5">2 Hours Old</div>
                <div className="text-[9px] font-mono text-slate-500">Zero KYC Track</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
