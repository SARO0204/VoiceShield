import React, { useState } from 'react';
import { ShieldQuestion, CheckCircle2, XCircle, Send, KeyRound, Lock, UserCheck } from 'lucide-react';
import { api } from '../services/api';

export const VerificationPage: React.FC = () => {
  const [callerName, setCallerName] = useState('');
  const [secretQuestion, setSecretQuestion] = useState('What is our family secret vacation keyword?');
  const [expectedAnswer, setExpectedAnswer] = useState('');
  const [activeChallenge, setActiveChallenge] = useState<any | null>(null);
  const [answerInput, setAnswerInput] = useState('');
  const [challengeResult, setChallengeResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCreateChallenge = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setChallengeResult(null);

    try {
      const challenge = await api.createVerification(undefined, callerName || 'Suspicious Caller', secretQuestion);
      challenge.expected_answer = expectedAnswer || 'blue';
      setActiveChallenge(challenge);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeChallenge) return;
    setLoading(true);

    try {
      const res = await api.submitVerificationAnswer(activeChallenge.verification_id, answerInput);
      setChallengeResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <ShieldQuestion className="w-4 h-4" />
            Out-of-Band Identity Verification
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Caller Identity Challenge & Verification Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            When high synthetic voice probability is detected, execute challenge-response verification before authorizing any financial or sensitive actions.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: Dispatch Challenge */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-cyan-400" />
            Dispatch Verification Challenge
          </h3>

          <form onSubmit={handleCreateChallenge} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Caller / Target Contact Name:
              </label>
              <input
                type="text"
                value={callerName}
                onChange={(e) => setCallerName(e.target.value)}
                placeholder="e.g. John Doe (Claiming to be grandson)"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Pre-Agreed Secret Question:
              </label>
              <select
                value={secretQuestion}
                onChange={(e) => setSecretQuestion(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option>What was the name of our first family pet?</option>
                <option>In what city did we meet last summer?</option>
                <option>What is our family secret vacation keyword?</option>
                <option>What is the nickname we only use at home?</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Expected Correct Answer:
              </label>
              <input
                type="text"
                value={expectedAnswer}
                onChange={(e) => setExpectedAnswer(e.target.value)}
                placeholder="Enter expected answer (e.g. Charlie, Tokyo)"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/30 flex items-center justify-center gap-2 transition-all"
            >
              <Send className="w-4 h-4" />
              <span>Create Active Challenge</span>
            </button>
          </form>
        </div>

        {/* Right: Active Challenge & Challenge Response */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            Active Challenge Status
          </h3>

          {!activeChallenge ? (
            <div className="p-12 text-center text-xs font-mono text-slate-500 rounded-xl bg-slate-950/40 border border-slate-800/80">
              No active challenge ticket. Dispatch a challenge from the left form.
            </div>
          ) : (
            <div className="p-5 rounded-xl bg-slate-950/70 border border-cyan-500/30 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <span className="text-xs font-bold text-white block">{activeChallenge.caller_name}</span>
                  <span className="text-[10px] font-mono text-slate-400">{activeChallenge.verification_id}</span>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono ${challengeResult?.status === 'PASSED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : challengeResult?.status === 'FAILED' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'}`}>
                  {challengeResult?.status || activeChallenge.status}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/80 text-xs">
                <span className="text-slate-400 block mb-1">Challenge Question:</span>
                <span className="font-semibold text-cyan-300">"{activeChallenge.question}"</span>
              </div>

              {/* Answering Form */}
              {!challengeResult ? (
                <form onSubmit={handleAnswerSubmit} className="space-y-3 pt-2">
                  <label className="text-xs font-semibold text-slate-300 block">
                    Submit Caller's Verbal Response:
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={answerInput}
                      onChange={(e) => setAnswerInput(e.target.value)}
                      placeholder="Type what caller answered..."
                      className="flex-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      type="submit"
                      disabled={loading || !answerInput}
                      className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
                    >
                      Verify
                    </button>
                  </div>
                </form>
              ) : (
                <div className={`p-4 rounded-xl border space-y-1.5 ${challengeResult.status === 'PASSED' ? 'bg-emerald-500/15 border-emerald-500/35 text-emerald-300' : 'bg-rose-500/15 border-rose-500/35 text-rose-300'}`}>
                  <div className="flex items-center gap-2 font-bold text-xs">
                    {challengeResult.status === 'PASSED' ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span>{challengeResult.status === 'PASSED' ? 'IDENTITY VERIFIED' : 'CHALLENGE FAILED — SUSPICIOUS CALLER'}</span>
                  </div>
                  <p className="text-xs">{challengeResult.result_message}</p>
                </div>
              )}
            </div>
          )}

          {/* Prevention Directives */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              Standard Safety Directives:
            </h4>
            <ul className="text-[11px] text-slate-400 space-y-1 list-disc list-inside">
              <li>Do NOT treat voice pitch or caller ID as standalone identity proof.</li>
              <li>Do NOT authorize wire transfers or bank transfers over phone calls.</li>
              <li>Always call back the individual using a saved, verified telephone number.</li>
            </ul>
          </div>

        </div>

      </div>

    </div>
  );
};
