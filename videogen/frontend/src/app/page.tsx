'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { motion, AnimatePresence } from 'framer-motion';
import Particles from '@/components/ParticlesBackground';
import BlurText from '@/components/BlurText';
import PreviewPlayer from '@/components/PreviewPlayer';
import { Loader2, Download, RefreshCcw, BookOpen, Flame, Newspaper, Smile, Mic, Video, Clock, Zap, Play, type LucideIcon } from 'lucide-react';

// API Configuration
const API_URL = 'http://localhost:3001/api';

interface FormData {
  tema: string;
  estilo: string;
  duracao: string;
  edicao: string;
  voz: string;
  idioma: string;
  formato: string;
}

export default function VideoGenPage() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('Gerando roteiro...');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    tema: '',
    estilo: 'educational',
    duracao: 'medium',
    edicao: 'tiktok',
    voz: 'alloy',
    idioma: 'pt',
    formato: 'vertical'
  });

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  const updateForm = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async () => {
    setStep(5); // Loading screen
    setLoading(true);
    setError(null);

    // Simulate progress messages
    const messages = ['Gerando roteiro...', 'Criando narração...', 'Compondo vídeo...'];
    let msgIdx = 0;
    const interval = setInterval(() => {
      msgIdx = (msgIdx + 1) % messages.length;
      setLoadingText(messages[msgIdx]);
    }, 4000);

    try {
      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          voz_instrucao: 'brazilian_energetic' // Default instruction
        })
      });

      const data = await response.json();
      clearInterval(interval);

      if (data.success) {
        setResult(data);
        setStep(6); // Result screen
      } else {
        throw new Error(data.error || 'Erro desconhecido');
      }
    } catch (err: any) {
      clearInterval(interval);
      setError(err.message);
      setStep(7); // Error screen
    } finally {
      setLoading(false);
    }
  };


  const handlePreview = async () => {
    setStep(5);
    setLoading(true);
    setLoadingText('Preparando preview instantâneo...');

    try {
      const response = await fetch(`${API_URL}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          voz_instrucao: 'brazilian_energetic'
        })
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
        setStep(6);
      } else {
        throw new Error(data.error || 'Erro no preview');
      }
    } catch (err: any) {
      setError(err.message);
      setStep(7);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(1);
    setFormData({ ...formData, tema: '' });
    setResult(null);
    setError(null);
  };

  const playPreview = (voice: string) => {
    const audio = new Audio(`http://localhost:3001/voices/${voice}.mp3`);
    audio.play().catch(e => console.error("Error playing preview:", e));
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground relative overflow-hidden selection:bg-primary/25">
      <div className="absolute inset-0 z-0 pointer-events-none">
        <Particles
          particleColors={['#5fa8ff', '#22d3ee']}
          particleCount={80}
          particleSpread={10}
          speed={0.1}
          particleBaseSize={100}
          moveParticlesOnHover={false}
          alphaParticles={false}
          disableRotation={false}
        />
      </div>

      {/* Background gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/15 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-0 right-1/2 translate-x-1/3 w-[700px] h-[420px] bg-accent/15 rounded-full blur-[140px] -z-10" />

      <motion.div
        className="w-full max-w-2xl px-6 relative z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <AnimatePresence mode="wait">

          {/* STEP 1: INTRO */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center"
            >
              <div className="mb-6 inline-block">
                <span className="bg-card/70 text-muted-foreground px-3 py-1 rounded-full text-sm font-medium border border-border/60 backdrop-blur-sm shadow-[var(--shadow-soft)]">v2.0 Beta</span>
              </div>

              <div className="flex flex-col items-center justify-center gap-2 mb-8">
                <h1 className="text-6xl md:text-7xl font-black tracking-tighter mb-4 bg-clip-text text-transparent bg-gradient-to-b from-foreground via-foreground/80 to-muted-foreground drop-shadow-sm">
                  VideoGen
                </h1>
                <BlurText
                  text="Crie vídeos virais em segundos com IA. Roteiro e edição automáticos."
                  className="text-xl text-muted-foreground max-w-lg mx-auto leading-relaxed text-center justify-center"
                  delay={30}
                  animateBy="words"
                  direction="bottom"
                />
              </div>

              <Button size="lg" onClick={nextStep} className="text-lg px-8 py-6 h-auto rounded-2xl shadow-[var(--shadow-glow)] hover:shadow-[var(--shadow-elevated)] transition-all hover:scale-105">
                Começar Agora
              </Button>
            </motion.div>
          )}

          {/* STEP 2: THEME */}
          {step === 2 && (
            <StepLayout title="Qual é o tema?" subtitle="Sobre o que será seu vídeo?">
              <textarea
                autoFocus
                className="w-full h-40 bg-card/50 border border-border/60 rounded-2xl p-4 text-lg focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/70 resize-none shadow-[var(--shadow-soft)]"
                placeholder="Ex: O futuro da inteligência artificial no trabalho..."
                value={formData.tema}
                onChange={(e) => updateForm('tema', e.target.value)}
              />
              <div className="flex gap-4 mt-8">
                <Button variant="ghost" onClick={prevStep} className="flex-1">Voltar</Button>
                <Button onClick={() => formData.tema ? nextStep() : null} disabled={!formData.tema} className="flex-1" size="lg">Próximo</Button>
              </div>
            </StepLayout>
          )}

          {/* STEP 3: STYLE */}
          {step === 3 && (
            <StepLayout title="Estilo do Vídeo" subtitle="Escolha o tom do roteiro">
              <div className="grid grid-cols-3 gap-4">
                <OptionCard icon={BookOpen} label="Educacional" desc="Didático e simples" value="educational" selected={formData.estilo} onClick={() => updateForm('estilo', 'educational')} />
                <OptionCard icon={Flame} label="Polêmico" desc="Gera debate" value="polemic" selected={formData.estilo} onClick={() => updateForm('estilo', 'polemic')} />
                <OptionCard icon={Newspaper} label="Notícia" desc="Fatos rápidos" value="news" selected={formData.estilo} onClick={() => updateForm('estilo', 'news')} />
                <OptionCard icon={Smile} label="Humor" desc="Engraçado" value="humor" selected={formData.estilo} onClick={() => updateForm('estilo', 'humor')} />
                <OptionCard icon={Mic} label="Primata" desc="Bananas e Galhos" value="primata" selected={formData.estilo} onClick={() => updateForm('estilo', 'primata')} />
                <OptionCard icon={Video} label="AutoLabs" desc="Animações de Macaco" value="autolabs" selected={formData.estilo} onClick={() => updateForm('estilo', 'autolabs')} />
              </div>
              <div className="flex gap-4 mt-8">
                <Button variant="ghost" onClick={prevStep} className="flex-1">Voltar</Button>
                <Button onClick={nextStep} className="flex-1" size="lg">Próximo</Button>
              </div>
            </StepLayout>
          )}

          {/* STEP 4: CONFIG */}
          {step === 4 && (
            <StepLayout title="Configurações" subtitle="Personalize os detalhes">
              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium mb-2 block text-muted-foreground">Duração</label>
                  <div className="grid grid-cols-4 gap-2">
                    <SelectButton label="15-30s" value="short" current={formData.duracao} onClick={(v: string) => updateForm('duracao', v)} />
                    <SelectButton label="30-60s" value="medium" current={formData.duracao} onClick={(v: string) => updateForm('duracao', v)} />
                    <SelectButton label="60-90s" value="long" current={formData.duracao} onClick={(v: string) => updateForm('duracao', v)} />
                    <SelectButton label="5 min" value="extra_long" current={formData.duracao} onClick={(v: string) => updateForm('duracao', v)} />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block text-muted-foreground">Formato</label>
                  <div className="grid grid-cols-2 gap-2">
                    <SelectButton label="📱 Vertical (TikTok/Reels)" value="vertical" current={formData.formato} onClick={(v: string) => updateForm('formato', v)} />
                    <SelectButton label="🖥️ Horizontal (YouTube)" value="horizontal" current={formData.formato} onClick={(v: string) => updateForm('formato', v)} />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block text-muted-foreground">Voz</label>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <select
                        className="w-full bg-card/50 border border-border/60 rounded-xl p-3 outline-none focus:ring-2 focus:ring-primary/40 text-foreground"
                        value={formData.voz}
                        onChange={(e) => updateForm('voz', e.target.value)}
                      >
                        <option value="alloy">Alloy (Neutro/Versátil)</option>
                        <option value="echo">Echo (Masculino/Suave)</option>
                        <option value="fable">Fable (Britânico/Expressivo)</option>
                        <option value="onyx">Onyx (Masculino/Profundo)</option>
                        <option value="nova">Nova (Feminino/Energético)</option>

                        <option value="shimmer">Shimmer (Feminino/Claro)</option>

                        {/* Premium Voices */}
                        <option value="elevenlabs">ElevenLabs (Ultra Realista)</option>

                        {/* GPT-4o-mini Voices */}
                        <option value="ash">Ash (Masculino/Assertivo)</option>
                        <option value="coral">Coral (Feminino/Claro)</option>
                        <option value="sage">Sage (Neutro/Calmo)</option>
                        <option value="verse">Verse (Narrativa/Natural)</option>
                        <option value="ballad">Ballad (Emocional)</option>
                        <option value="marin">Marin (Natural/Recomendado)</option>
                        <option value="cedar">Cedar (Natural/Recomendado)</option>
                      </select>
                    </div>
                    <Button
                      variant="outline"
                      size="icon"
                      className="shrink-0"
                      onClick={() => playPreview(formData.voz)}
                      title="Ouvir prévia"
                    >
                      <Play size={20} />
                    </Button>
                  </div>
                </div>
                <div className="flex gap-4 mt-8">
                  <Button variant="ghost" onClick={prevStep} className="flex-1">Voltar</Button>
                  <Button onClick={handlePreview} className="flex-1 bg-warning/15 text-warning hover:bg-warning/25 border border-warning/40" size="lg">
                    <Zap className="mr-2 h-4 w-4" /> Preview
                  </Button>
                  <Button onClick={handleGenerate} className="flex-1 shadow-[var(--shadow-glow)]" size="lg">Generar MP4</Button>
                </div>
              </div>
            </StepLayout>
          )}

          {/* STEP 5: LOADING */}
          {step === 5 && (
            <motion.div
              key="step5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <div className="relative w-24 h-24 mx-auto mb-8">
                <div className="absolute inset-0 border-4 border-border/60 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-t-primary rounded-full animate-spin"></div>
              </div>
              <h2 className="text-2xl font-bold mb-2">{loadingText}</h2>
              <p className="text-muted-foreground">Isso pode levar alguns segundos...</p>
            </motion.div>
          )}

          {/* STEP 6: RESULT */}
          {step === 6 && result && (
            <motion.div
              key="step6"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative z-10 w-full max-w-4xl flex flex-col items-center"
            >
              <h2 className="text-3xl font-bold mb-8 flex items-center gap-2">
                {result.video_path ? 'Video Gerado' : 'Preview Instantâneo'}
                <span className="text-xs bg-success/20 text-success px-2 py-1 rounded-full border border-success/30">Concluído</span>
              </h2>

              {result.video_path ? (
                // FULL VIDEO PLAYER
                <div className="bg-card/80 p-2 rounded-2xl border border-border/70 shadow-[var(--shadow-elevated)]">
                  <video
                    src={result.video_path.startsWith('http') ? result.video_path : `http://localhost:3001${result.video_path}`}
                    controls
                    autoPlay
                    className="rounded-xl max-h-[70vh] w-auto shadow-inner"
                  />
                  <div className="flex gap-4 mt-4 px-2 pb-2">
                    <Button onClick={reset} variant="outline" className="flex-1 border-border/60 hover:bg-muted/60 text-foreground">
                      <RefreshCcw className="mr-2 h-4 w-4" /> Novo
                    </Button>
                    <a href={result.video_path.startsWith('http') ? result.video_path : `http://localhost:3001${result.video_path}`} download className="flex-1">
                      <Button className="w-full">
                        <Download className="mr-2 h-4 w-4" /> Baixar
                      </Button>
                    </a>
                  </div>
                </div>
              ) : (
                // PREVIEW PLAYER
                <PreviewPlayer
                  data={result}
                  onGenerateFull={handleGenerate}
                  onReset={reset}
                />
              )}
            </motion.div>
          )}

          {/* STEP 7: ERROR */}
          {step === 7 && (
            <motion.div
              key="step7"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <div className="w-20 h-20 bg-destructive/15 rounded-full flex items-center justify-center mx-auto mb-6 text-destructive border border-destructive/30">
                <span className="text-4xl">❌</span>
              </div>
              <h2 className="text-2xl font-bold mb-4">Ops! Algo deu errado</h2>
              <p className="text-muted-foreground mb-8 max-w-md mx-auto">{error}</p>
              <Button onClick={reset} variant="outline" className="border-border/60">Tentar Novamente</Button>
            </motion.div>
          )}

        </AnimatePresence>
      </motion.div>

      <footer className="absolute bottom-6 text-sm text-muted-foreground">
        &copy; 2024 VideoGen AI
      </footer>
    </div >
  );
}

// Components
function StepLayout({ title, subtitle, children }: { title: string, subtitle: string, children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="w-full"
    >
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2">{title}</h2>
        <p className="text-muted-foreground">{subtitle}</p>
      </div>
      {children}
    </motion.div>
  );
}

function OptionCard({ icon: Icon, label, desc, value, selected, onClick }: any) {
  const isSelected = selected === value;
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-xl border cursor-pointer transition-all ${isSelected
        ? 'bg-primary/15 border-primary/60 shadow-[var(--shadow-glow)] ring-1 ring-primary/60'
        : 'bg-card/50 border-border/60 hover:border-border/80 hover:bg-card/70'
        }`}
    >
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted/60 text-muted-foreground'}`}>
        <Icon size={20} />
      </div>
      <div className="font-bold text-sm">{label}</div>
      <div className="text-xs text-muted-foreground">{desc}</div>
    </div>
  );
}

function SelectButton({ label, value, current, onClick }: any) {
  const isSelected = current === value;
  return (
    <button
      onClick={() => onClick(value)}
      className={`p-3 rounded-xl text-sm font-medium transition-all border ${isSelected
        ? 'bg-primary text-primary-foreground border-primary/60 shadow-[var(--shadow-glow)]'
        : 'bg-card/40 border-border/60 text-muted-foreground hover:border-border/80 hover:bg-card/60'
        }`}
    >
      {label}
    </button>
  );
}
