'use client';

import { Analysis } from '@/types';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { Button } from '@/components/ui/button';
import { Download, Scissors, Type } from 'lucide-react';

interface AnalysisResultsProps {
    videoId: string;
    videoName: string;
    analysis: Analysis | undefined;
    isOpen: boolean;
    onClose: () => void;
}

export function AnalysisResults({ videoId, videoName, analysis, isOpen, onClose }: AnalysisResultsProps) {
    if (!analysis) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent side="right" className="w-full sm:w-[540px] border-l-border/70 bg-card p-0 flex flex-col">
                <SheetHeader className="p-6 border-b border-border/70 bg-card/90">
                    <SheetTitle className="text-xl">{videoName}</SheetTitle>
                    <SheetDescription>Resultados da análise de IA</SheetDescription>
                </SheetHeader>

                <div className="flex-1 overflow-y-auto">
                    {/* Mock Video Player */}
                    <div className="aspect-video bg-surface w-full flex items-center justify-center border-b border-border/70">
                        <p className="text-muted-foreground">Player de Vídeo (Mock)</p>
                    </div>

                    <div className="p-6">
                        <Tabs defaultValue="cuts" className="w-full">
                            <TabsList className="w-full grid grid-cols-2 mb-6">
                                <TabsTrigger value="cuts">
                                    <Scissors className="mr-2 h-4 w-4" />
                                    Decupagem ({analysis.cuts.length})
                                </TabsTrigger>
                                <TabsTrigger value="subtitles">
                                    <Type className="mr-2 h-4 w-4" />
                                    Legendas ({analysis.subtitleErrors.length})
                                </TabsTrigger>
                            </TabsList>

                            <TabsContent value="cuts" className="space-y-4">
                                {analysis.cuts.map((cut, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/40 hover:bg-muted/60 border border-border/50 cursor-pointer transition text-sm">
                                        <div className="flex items-center gap-3">
                                            <span className="font-mono text-primary font-bold">{cut.timestamp}</span>
                                            <span className="text-foreground">{cut.type}</span>
                                        </div>
                                        <span className="text-xs text-muted-foreground">Wait: {Math.round(cut.confidence * 100)}%</span>
                                    </div>
                                ))}
                            </TabsContent>

                            <TabsContent value="subtitles" className="space-y-4">
                                {analysis.subtitleErrors.map((error, idx) => (
                                    <div key={idx} className="p-4 rounded-lg bg-muted/40 border border-border/50 text-sm space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="font-mono text-primary font-bold">{error.timestamp}</span>
                                            <span className="text-xs text-destructive font-medium">{error.errorType}</span>
                                        </div>
                                        <div className="grid grid-cols-[auto_1fr] gap-2">
                                            <span className="text-destructive line-through decoration-destructive/50 opacity-70">{error.original}</span>
                                            <span className="text-success font-medium">{error.corrected}</span>
                                        </div>
                                    </div>
                                ))}
                            </TabsContent>
                        </Tabs>
                    </div>
                </div>

                <div className="p-6 border-t border-border/70 bg-card/90 mt-auto grid grid-cols-2 gap-4">
                    <Button variant="outline" className="w-full border-border/70 hover:bg-muted/60">
                        <Download className="mr-2 h-4 w-4" /> Exportar CSV
                    </Button>
                    <Button variant="outline" className="w-full border-border/70 hover:bg-muted/60">
                        <Download className="mr-2 h-4 w-4" /> Exportar JSON
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    );
}
