import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Download, RefreshCw } from 'lucide-react';

interface PreviewPlayerProps {
    data: {
        script: any;
        audio_url: string;
        assets: string[];
        durations: number[];
    };
    onGenerateFull: () => void;
    onReset: () => void;
}

export default function PreviewPlayer({ data, onGenerateFull, onReset }: PreviewPlayerProps) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);

    // Constants
    const API_URL = 'http://localhost:3001';

    // Audio is 1 file. We need to switch images based on estimated durations.
    // durations is list of seconds per scene.
    // We need cumulative thresholds.
    const thresholds = data.durations.reduce((acc, curr, i) => {
        const prev = acc.length > 0 ? acc[acc.length - 1] : 0;
        acc.push(prev + curr);
        return acc;
    }, [] as number[]);

    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const handleTimeUpdate = () => {
            const t = audio.currentTime;
            const duration = audio.duration || 1;
            setProgress((t / duration) * 100);

            // Find which scene we are in
            // thresholds[i] is the END time of scene i
            let foundIndex = 0;
            for (let i = 0; i < thresholds.length; i++) {
                if (t < thresholds[i]) {
                    foundIndex = i;
                    break;
                }
                foundIndex = i; // if exceeded all (last scene)
            }

            if (foundIndex !== currentIndex) {
                setCurrentIndex(foundIndex);
            }
        };

        const handlePlay = () => setIsPlaying(true);
        const handlePause = () => setIsPlaying(false);

        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('play', handlePlay);
        audio.addEventListener('pause', handlePause);

        // Auto play
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.log("Autoplay prevented:", error);
                setIsPlaying(false);
            });
        }

        return () => {
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('play', handlePlay);
            audio.removeEventListener('pause', handlePause);
        };
    }, [currentIndex, thresholds]);

    const currentAsset = data.assets[currentIndex]
        ? `${API_URL}${data.assets[currentIndex]}`
        : null;

    const currentText = data.script.cenas[currentIndex]?.texto || "";

    const handleAudioError = () => {
        console.error("Audio Load Error. URL:", data.audio_url);
    };

    return (
        <div className="w-full max-w-md mx-auto bg-card/90 rounded-3xl overflow-hidden shadow-[var(--shadow-elevated)] border border-border/70 relative group">
            {/* HEADER */}
            <div className="absolute top-0 left-0 right-0 p-4 z-20 bg-gradient-to-b from-background/80 to-transparent flex justify-between items-start">
                <div className="bg-warning text-warning-foreground text-xs font-bold px-2 py-1 rounded flex items-center gap-1 shadow-[var(--shadow-soft)] border border-warning/40">
                    <span>⚡ PREVIEW</span>
                </div>
            </div>

            {/* SCREEN */}
            <div className="aspect-[9/16] bg-surface relative flex items-center justify-center overflow-hidden">
                {/* GRID BACKGROUND */}
                <div className="absolute inset-0 opacity-20 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

                {currentAsset ? (
                    <motion.img
                        key={currentAsset}
                        src={currentAsset}
                        initial={{ opacity: 0, scale: 1.1 }}
                        animate={{ opacity: 1, scale: 1.0 }}
                        transition={{ duration: 0.5 }}
                        className="w-full h-full object-contain z-10 p-4"
                        alt="Scene Asset"
                    />
                ) : (
                    <div className="text-muted-foreground z-10 flex flex-col items-center animate-pulse">
                        <span className="text-4xl mb-2">🖼️</span>
                        <span className="text-xs">Carregando Asset...</span>
                    </div>
                )}

                {/* SUBTITLES */}
                <div className="absolute bottom-24 left-4 right-4 text-center z-20 pointer-events-none">
                    <motion.p
                        key={currentText}
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="text-warning font-bold text-xl drop-shadow-md bg-background/70 p-3 rounded-xl inline-block backdrop-blur-sm border border-border/40"
                    >
                        {currentText}
                    </motion.p>
                </div>
            </div>

            {/* CONTROLS */}
            <div className="bg-card/80 p-4 space-y-4 border-t border-border/70 relative z-30">
                {/* Progress Bar */}
                <div className="w-full bg-muted/60 h-1.5 rounded-full overflow-hidden border border-border/60 cursor-pointer" onClick={(e) => {
                    // Seek functionality (simple)
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const width = rect.width;
                    const percentage = x / width;
                    if (audioRef.current && audioRef.current.duration) {
                        audioRef.current.currentTime = percentage * audioRef.current.duration;
                    }
                }}>
                    <div
                        className="bg-warning h-full transition-all duration-100 ease-linear shadow-[0_0_12px_var(--warning)]"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground justify-between px-1">
                    <span>{Math.floor(audioRef.current?.currentTime || 0)}s</span>
                    <span>{Math.floor(audioRef.current?.duration || 0)}s</span>
                </div>

                <audio
                    ref={audioRef}
                    src={`${API_URL}${data.audio_url}`}
                    className="hidden"
                    controls
                    onError={handleAudioError}
                />

                {/* Custom Controls */}
                <div className="grid grid-cols-2 gap-3">
                    <Button onClick={() => {
                        if (isPlaying) audioRef.current?.pause();
                        else audioRef.current?.play();
                    }} className={`col-span-2 font-bold transition-all ${isPlaying ? 'bg-muted text-foreground hover:bg-muted/80' : 'bg-warning text-warning-foreground hover:bg-warning/90 shadow-[0_0_15px_var(--warning)]'}`}>
                        {isPlaying ? "Pause ⏸️" : "Play ▶️"}
                    </Button>

                    <Button onClick={onReset} variant="outline" className="text-foreground bg-card/50 hover:bg-muted/60 border-border/60">
                        <RefreshCw className="mr-2 h-4 w-4" /> Voltar
                    </Button>
                    <Button onClick={onGenerateFull} className="bg-success hover:bg-success/90 text-success-foreground font-bold border border-success/30 shadow-[var(--shadow-soft)]">
                        <Download className="mr-2 h-4 w-4" /> Exportar
                    </Button>
                </div>
            </div>
        </div>
    );
}
