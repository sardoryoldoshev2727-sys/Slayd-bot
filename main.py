"/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import Markdown from 'react-markdown';
import { 
  Key, 
  Plus, 
  Trash2, 
  Copy, 
  CheckCircle2, 
  ShieldAlert, 
  Activity, 
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Search,
  Settings,
  MoreVertical,
  Zap,
  Info,
  Layers,
  LayoutDashboard,
  Box,
  CreditCard,
  ChevronRight,
  TrendingUp,
  AlertCircle,
  MessageSquare,
  Wand2,
  Code2,
  Terminal,
  Cpu,
  Globe
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { GoogleGenAI } from '@google/genai';
import { APIKey, SecurityLevel } from './types';

// Constants
const GEMINI_MODEL = 'gemini-3-flash-preview';

export default function App() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [activeTab, setActiveTab] = useState<'keys' | 'architect'>('keys');

  // Bot Architect State
  const [botGoal, setBotGoal] = useState('');
  const [botResponse, setBotResponse] = useState<string | null>(null);
  const [isGeneratingBot, setIsGeneratingBot] = useState(false);

  // Initial data population
  useEffect(() => {
    if (keys.length === 0) {
      setKeys([
        {
          id: '1',
          name: 'Ishlab chiqarish (Production) Mobile',
          key: 'ks_live_a9b8c7d6e5f4g3h2i1j0k9l8m7n6o5p4',
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
          lastUsed: new Date().toISOString(),
          status: 'active',
          usageLimit: 5000,
          currentUsage: 1240
        }
      ]);
    }
  }, []);

  const [isAddingMode, setIsAddingMode] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiInsight, setAiInsight] = useState<string | null>(null);

  // Initialize Gemini
  const ai = useMemo(() => {
    try {
      const apiKey = process.env.GEMINI_API_KEY;
      if (!apiKey || apiKey === "MY_GEMINI_API_KEY") return null;
      return new GoogleGenAI({ apiKey });
    } catch (e) {
      console.error('Gemini init failed', e);
      return null;
    }
  }, []);

  const generateBotGuide = async () => {
    if (!ai) {
      alert("Iltimos, Secrets panelida GEMINI_API_KEY ni sozlang.");
      return;
    }
    if (!botGoal) return;

    setIsGeneratingBot(true);
    try {
      const prompt = `Siz professional Telegram bot dasturchisisiz. Foydalanuvchi quyidagi botni yaratmoqchi: "${botGoal}". 
      Unga quyidagilarni o'zbek tilida batafsil yozib bering:
      1. Botning 0-dan boshlab yaratish rejasi (Taqdimot, Krassvord, Test bo'limlari bilan).
      2. Har bir buyruq uchun yoqimli emojilar va reply xabarlar namunasi.
      3. Node.js (Telegraf.js) kodi namunasi (Start menyu va bo'limlar).
      4. PPTX yaratish (pptxgenjs) va Click/Payme to'lovlarini screenshot orqali tekshirish bo'yicha maslahatlar.
      Markdown formatida yozing.`;

      const response = await ai.models.generateContent({
        model: GEMINI_MODEL,
        contents: prompt
      });
      setBotResponse(response.text || "Javob olib bo'lmadi.");
    } catch (error) {
      console.error('Bot generation failed', error);
      setBotResponse("Xatolik yuz berdi. Iltimos qaytadan urunib ko'ring.");
    } finally {
      setIsGeneratingBot(false);
    }
  };

  // Filter keys
  const filteredKeys = useMemo(() => {
    return keys.filter(k => 
      k.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      k.key.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [keys, searchQuery]);

  // Generate a random key
  const generateKey = (name: string) => {
    const randomPart = Array.from({ length: 32 }, () => 
      Math.random().toString(36)[2]
    ).join('');
    
    const newKey: APIKey = {
      id: Math.random().toString(36).substring(7),
      name: name || 'Untitled Key',
      key: `ks_${randomPart}`,
      createdAt: new Date().toISOString(),
      lastUsed: null,
      status: 'active',
      usageLimit: 1000,
      currentUsage: 0
    };
    
    setKeys(prev => [newKey, ...prev]);
    setIsAddingMode(false);
    setNewKeyName('');
  };

  const deleteKey = (id: string) => {
    setKeys(prev => prev.filter(k => k.id !== id));
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const analyzeSecurity = async () => {
    if (!ai) {
      setAiInsight("Gemini API kaliti topilmadi (Secrets paneliga qarang).");
      return;
    }
    
    setIsAnalyzing(true);
    try {
      const response = await ai.models.generateContent({
        model: GEMINI_MODEL,
        contents: "Siz kiberxavfsizlik ekspertisiz. API kalitlarini xavfsiz saqlash bo'yicha 3 ta qisqa va foydali maslahat bering (o'zbek tilida). Maksimum 80 so'z."
      });
      setAiInsight(response.text || "Auditi natijasi chiqmadi.");
    } catch (error) {
      console.error('Security analysis failed', error);
      setAiInsight("AI bilan bog'lanishda xatolik.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 flex flex-col border-r border-slate-800 shrink-0">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center text-white shrink-0">
            <Zap className="w-5 h-5 fill-white" />
          </div>
          <span className="font-bold text-slate-100 tracking-tight text-lg">KEYSCALE API</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavItem icon={<LayoutDashboard size={18} />} label="Boshqaruv paneli" />
          <div onClick={() => setActiveTab('keys')}>
            <NavItem icon={<Key size={18} />} label="API Kalitlar" active={activeTab === 'keys'} />
          </div>
          <div onClick={() => setActiveTab('architect')}>
            <NavItem icon={<Wand2 size={18} />} label="Bot Arxitektori" active={activeTab === 'architect'} />
          </div>
          <NavItem icon={<Activity size={18} />} label="Foydalanish tarixi" />
          <NavItem icon={<CreditCard size={18} />} label="To'lovlar" />
          <NavItem icon={<Box size={18} />} label="Integratsiyalar" />
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer group">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-bold leading-none shrink-0 group-hover:bg-indigo-200 transition-colors">
              SY
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium text-white truncate">Sardor Developer</p>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Professional Plan</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0 z-10">
          <h1 className="text-lg font-semibold text-slate-800 uppercase tracking-tight">
            {activeTab === 'keys' ? 'API Kalitlarni Boshqarish' : 'Bot Arxitektori (Beta)'}
          </h1>
          
          <div className="flex items-center gap-4">
            {activeTab === 'keys' && (
              <div className="relative group hidden md:block">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Kalitlarni qidirish..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-1.5 bg-slate-100 border border-transparent rounded text-sm focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all w-64 outline-none"
                />
              </div>
            )}
            {activeTab === 'keys' ? (
              <button 
                onClick={() => setIsAddingMode(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold hover:bg-indigo-700 transition-all shadow-sm active:scale-95"
              >
                + Yangi kalit yaratish
              </button>
            ) : (
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                <span className="px-2 py-1 bg-slate-100 rounded">AI POWERED</span>
              </div>
            )}
          </div>
        </header>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {activeTab === 'keys' ? (
            <>
              {/* Dashboard Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard 
                  label="Faol kalitlar" 
                  value={keys.length} 
                  icon={<Key className="text-indigo-600" size={16} />} 
                  trend="Bu oyda +2 ta"
                />
                <StatCard 
                  label="Umumiy foydalanish (24s)" 
                  value={keys.reduce((acc, k) => acc + k.currentUsage, 0).toLocaleString()} 
                  icon={<TrendingUp className="text-indigo-600" size={16} />} 
                  subValue="Kvota: 85%"
                />
                <StatCard 
                  label="Xatolik darajasi" 
                  value="0.04%" 
                  icon={<AlertCircle className="text-emerald-600" size={16} />} 
                  positive
                />
              </div>

              {/* AI Security Insight Section (Density Update) */}
              <section className="bg-slate-900 rounded-lg p-6 text-white relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
                  <ShieldCheck size={120} className="text-indigo-400 rotate-12" />
                </div>
                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 bg-indigo-400/10 px-2 py-0.5 rounded border border-indigo-400/20">Gemini Xavfsizlik Auditi</span>
                  </div>
                  <h3 className="text-xl font-bold mb-2">Avtomatlashtirilgan Xavfsizlik Tahlili</h3>
                  {aiInsight ? (
                    <p className="text-slate-300 leading-relaxed text-sm mb-4 max-w-3xl">
                      {aiInsight}
                    </p>
                  ) : (
                    <p className="text-slate-400 text-sm mb-4 italic">
                      Gemini AI yordamida real vaqt rejimida API infratuzilmangizni xavfsizlik tahlilidan o'tkazing.
                    </p>
                  )}
                  
                  <button 
                    onClick={analyzeSecurity}
                    disabled={isAnalyzing}
                    className="inline-flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded text-xs font-bold transition-all disabled:opacity-50"
                  >
                    {isAnalyzing ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Zap className="w-3.5 h-3.5 fill-white" />
                    )}
                    {isAnalyzing ? 'TAHLIL QILINMOQDA...' : 'AUDITNI BOSHLASH'}
                  </button>
                </div>
              </section>

              {/* Keys Table Container */}
              <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Faol API kalitlari</h4>
                  <button className="text-slate-400 hover:text-slate-600 transition-colors">
                    <Settings size={14} />
                  </button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-6 py-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Tavsif (Nomi)</th>
                        <th className="px-6 py-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Maxfiy kalit</th>
                        <th className="px-6 py-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Yaratilgan sana</th>
                        <th className="px-6 py-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Holati</th>
                        <th className="px-6 py-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider text-right">Amallar</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <AnimatePresence mode="popLayout">
                        {filteredKeys.length > 0 ? (
                          filteredKeys.map((k) => (
                            <motion.tr 
                              layout
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              key={k.id}
                              className="hover:bg-slate-50/80 transition-colors group"
                            >
                              <td className="px-6 py-4">
                                <div className="flex flex-col">
                                  <span className="text-sm font-bold text-slate-900">{k.name}</span>
                                  <span className="text-[10px] font-medium text-slate-400 uppercase tracking-tight mt-0.5">Foydalanish: {k.currentUsage} ta</span>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-2">
                                  <code className="text-[11px] font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded border border-slate-200 block truncate max-w-[150px]">
                                    {k.key.substring(0, 10)}â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢
                                  </code>
                                  <button 
                                    onClick={() => copyToClipboard(k.key, k.id)}
                                    className="p-1 text-slate-400 hover:text-indigo-600 transition-colors"
                                  >
                                    {copiedId === k.id ? <CheckCircle2 size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                  </button>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-xs text-slate-500 font-medium">
                                {new Date(k.createdAt).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })}
                              </td>
                              <td className="px-6 py-4">
                                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded text-[10px] font-bold uppercase tracking-wider">
                                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                                  Faol
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <button 
                                  onClick={() => deleteKey(k.id)}
                                  className="text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </td>
                            </motion.tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={5} className="px-6 py-20 text-center">
                               <div className="flex flex-col items-center gap-4 text-slate-400">
                                  <Key size={40} className="text-slate-200" />
                                  <div className="space-y-1">
                                    <p className="text-sm font-bold text-slate-500">Hech qanday ma'lumot topilmadi</p>
                                    <p className="text-xs">{(searchQuery ? "Filtrga mos keladigan kalitlar mavjud emas." : "Yangi API kalit yaratish orqali boshlang.")}</p>
                                  </div>
                               </div>
                            </td>
                          </tr>
                        )}
                      </AnimatePresence>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-100 rounded-lg p-4 flex gap-4">
                <Info className="text-amber-600 shrink-0 mt-0.5" size={18} />
                <div className="flex-1">
                  <h5 className="text-sm font-bold text-amber-900 mb-1">Dasturchilar uchun eslatma</h5>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    Bu yerda ko'rsatilgan kalitlar namuna uchun. Haqiqiy ishchi muhitda tizimingizni himoya qilish uchun <strong>IP-larni oq ro'yxatga kiritish</strong> 
                    va <strong>Ruxsatlar nazorati (RBAC)</strong>-ni amalga oshirishingizni tavsiya qilamiz. Gemini API kalitini xavfsiz boshqarish uchun Secrets panelidan foydalaning.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 text-indigo-600 rounded-2xl mb-4">
                  <Cpu size={32} />
                </div>
                <h2 className="text-3xl font-bold text-slate-900">Bot Arxitektori</h2>
                <p className="text-slate-500">Botingiz g'oyasini yozing, biz esa uni 0-dan yaratishga yordam beramiz.</p>
              </div>

              {/* Step by Step Guide for Beginners */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <GuideStep number="1" title="BotFather" desc="Token oling" />
                <GuideStep number="2" title="G'oya" desc="Shartlarni yozing" />
                <GuideStep number="3" title="Kod" desc="AI yordamida oling" />
                <GuideStep number="4" title="Railway" desc="Serverga yuklang" />
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="p-8 space-y-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Bot g'oyasi va barcha shartlarini kiriting:</label>
                    <textarea 
                      placeholder="Masalan: Taqdimot yaratadigan bot. Narxlar: 1 ta slayd 2000 so'm. To'lov screenshot orqali..." 
                      rows={6}
                      value={botGoal}
                      onChange={(e) => setBotGoal(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none text-slate-800"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FeatureBox 
                      icon={<Terminal size={20} className="text-indigo-600" />} 
                      title="Tayyor Kod" 
                      desc="Node.js yoki Python uchun boshlang'ich kod snippetlari." 
                    />
                    <FeatureBox 
                      icon={<Globe size={20} className="text-indigo-600" />} 
                      title="Railway Guide" 
                      desc="Botingizni serverga joylash bo'yicha bosqichma-bosqich qo'llanma." 
                    />
                  </div>

                  <button 
                    onClick={generateBotGuide}
                    disabled={isGeneratingBot || !botGoal}
                    className="w-full bg-slate-900 text-white flex items-center justify-center gap-3 py-4 rounded-xl font-bold hover:bg-slate-800 transition-all shadow-xl active:scale-95 disabled:opacity-50"
                  >
                    {isGeneratingBot ? (
                      <>
                        <RefreshCw size={20} className="animate-spin" />
                        ARXITEKTURA LOYIHALANMOQDA...
                      </>
                    ) : (
                      <>
                        <Wand2 size={20} />
                        BOTNI LOYIHALASHNI BOSHLASH
                      </>
                    )}
                  </button>
                </div>
              </div>

              {botResponse && (
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 prose prose-slate max-w-none">
                  <div className="flex items-center gap-2 mb-6 text-indigo-600 font-bold border-b border-slate-100 pb-4">
                    <Code2 size={24} />
                    SIZNING BOTINGIZ UCHUN YO'RIQNOMA
                  </div>
                  <div className="markdown-body">
                    <Markdown>{botResponse}</Markdown>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* High Density Modal Overlay */}
      <AnimatePresence>
        {isAddingMode && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 overflow-hidden">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
              onClick={() => setIsAddingMode(false)}
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white w-[480px] rounded-xl shadow-2xl border border-slate-200 overflow-hidden relative z-50"
            >
              <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                <h3 className="text-lg font-bold text-slate-900">Yangi API kalit yaratish</h3>
                <p className="text-sm text-slate-500 mt-1">Ilovangiz yoki xizmatingiz uchun kirish ruxsatini sozlang.</p>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2">Kalit nomi</label>
                  <input 
                    type="text" 
                    placeholder="masalan: Production Mobile App" 
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    autoFocus
                    className="w-full border border-slate-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium transition-all"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2">Ruxsatlar (Bosqichlar)</label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <input type="checkbox" checked readOnly className="w-4 h-4 text-indigo-600 rounded cursor-pointer" />
                      <span className="text-sm text-slate-700 group-hover:text-slate-900 transition-colors">Faqat o'qish (Standart)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <input type="checkbox" className="w-4 h-4 text-indigo-600 rounded cursor-pointer" />
                      <span className="text-sm text-slate-700 group-hover:text-slate-900 transition-colors">Yozish ruxsati</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <input type="checkbox" className="w-4 h-4 text-indigo-600 rounded cursor-pointer" />
                      <span className="text-sm text-slate-700 group-hover:text-slate-900 transition-colors">Ma'muriy ruxsatlar</span>
                    </label>
                  </div>
                </div>
                <div className="bg-amber-50 p-4 rounded-lg border border-amber-100 flex gap-3">
                  <ShieldAlert className="text-amber-600 shrink-0" />
                  <p className="text-[11px] text-amber-800 leading-normal font-medium">
                    Diqqat: Kalit yaratilgandan so'ng, uning to'liq maxfiy qismi faqat bir marta ko'rsatiladi. Uni xavfsiz joyda saqlashingizga ishonch hosil qiling.
                  </p>
                </div>
              </div>
              <div className="bg-slate-50 px-6 py-4 flex justify-end gap-3 border-t border-slate-100">
                <button 
                  onClick={() => setIsAddingMode(false)}
                  className="px-4 py-2 text-sm font-bold text-slate-600 hover:text-slate-800 transition-colors"
                >
                  Bekor qilish
                </button>
                <button 
                  onClick={() => generateKey(newKeyName)}
                  className="px-6 py-2 bg-indigo-600 text-white text-sm font-black rounded shadow-md hover:bg-indigo-700 transition-all active:scale-95"
                >
                  KALITNI YARATISH
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Sub-components for better organization & themes
function NavItem({ icon, label, active = false }: { icon: React.ReactNode, label: string, active?: boolean }) {
  return (
    <div 
      className={`flex items-center px-4 py-2.5 text-sm font-medium transition-all group rounded-md cursor-pointer ${
        active 
          ? 'bg-slate-800 text-white shadow-inner' 
          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
      }`}
    >
      <span className={`mr-3 transition-colors ${active ? 'text-indigo-400' : 'group-hover:text-white'}`}>
        {icon}
      </span>
      {label}
      {active && <ChevronRight size={14} className="ml-auto text-slate-500" />}
    </div>
  );
}

function StatCard({ label, value, icon, trend, subValue, positive = false }: { 
  label: string, 
  value: string | number, 
  icon: React.ReactNode, 
  trend?: string,
  subValue?: string,
  positive?: boolean
}) {
  return (
    <div className="bg-white p-5 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-300 transition-all flex flex-col group">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
        <div className="p-1.5 bg-slate-50 rounded border border-slate-100 group-hover:bg-indigo-50 group-hover:border-indigo-100 transition-colors">
          {icon}
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <p className={`text-2xl font-mono tracking-tight font-bold ${positive ? 'text-emerald-600' : 'text-slate-900'}`}>
          {value}
        </p>
        {trend && (
          <span className="text-[10px] font-bold text-slate-400 tracking-tight">
            ({trend})
          </span>
        )}
      </div>
      {subValue && (
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mt-1">{subValue}</p>
      )}
    </div>
  );
}

function FeatureBox({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex gap-4">
      <div className="shrink-0">{icon}</div>
      <div>
        <h5 className="text-sm font-bold text-slate-900">{title}</h5>
        <p className="text-xs text-slate-500 leading-normal">{desc}</p>
      </div>
    </div>
  );
}

function GuideStep({ number, title, desc }: { number: string, title: string, desc: string }) {
  return (
    <div className="bg-indigo-600 p-4 rounded-xl text-white flex flex-col items-center text-center gap-1 shadow-lg shadow-indigo-200">
      <span className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs font-black">{number}</span>
      <h5 className="text-sm font-bold">{title}</h5>
      <p className="text-[10px] opacity-80 font-medium leading-tight">{desc}</p>
    </div>
  );
}"
