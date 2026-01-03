'use client';

import { Video } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { PlayCircle, Clock, AlertCircle, RefreshCw, FileVideo, Trash2, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface VideoCardProps {
    video: Video;
    onViewResults: () => void;
    onRetry?: () => void;
    onDelete?: () => void;
    onAnalyze?: () => void;
}

export function VideoCard({ video, onViewResults, onRetry, onDelete, onAnalyze }: VideoCardProps) {
    return (
        <Card className="overflow-hidden border-border bg-card">
            <CardContent className="p-4 flex items-center gap-4">
                {/* Thumbnail Placeholder */}
                <div className="h-20 w-32 bg-secondary/50 rounded-md flex items-center justify-center flex-shrink-0">
                    <FileVideo className="h-8 w-8 text-muted-foreground" />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-foreground truncate pr-4" title={video.filename}>
                            {video.filename}
                        </h4>
                        {/* Status Badge */}
                        {video.status === 'completed' && (
                            <Badge variant="success">Analisado</Badge>
                        )}
                        {video.status === 'processing' && (
                            <Badge variant="outline" className="border-info/40 text-info">Processando</Badge>
                        )}
                        {video.status === 'queued' && (
                            <Badge variant="outline" className="text-muted-foreground border-muted-foreground/30">Na Fila</Badge>
                        )}
                        {video.status === 'uploading' && (
                            <Badge variant="secondary">Upload...</Badge>
                        )}
                        {video.status === 'error' && (
                            <Badge variant="destructive">Erro</Badge>
                        )}
                    </div>

                    {/* Status Content */}
                    <div className="space-y-2">
                        {video.status === 'uploading' && (
                            <div className="flex items-center gap-3">
                                <Progress value={video.progress} className="h-2" />
                                <span className="text-xs text-muted-foreground w-10 text-right">{Math.round(video.progress)}%</span>
                            </div>
                        )}

                        {video.status === 'processing' && (
                            <div className="flex items-center gap-2 text-sm text-info">
                                <RefreshCw className="h-3 w-3 animate-spin" />
                                <span>Analisando vídeo com IA...</span>
                            </div>
                        )}

                        {video.status === 'completed' && (
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <Clock className="h-3 w-3" />
                                    <span>{video.duration ? formatDuration(video.duration) : '--:--'}</span>
                                </div>
                                <Button onClick={onViewResults} size="sm" variant="outline" className="ml-auto h-8 border-primary/30 hover:border-primary text-primary hover:bg-primary/10">
                                    <PlayCircle className="mr-2 h-4 w-4" />
                                    Ver Resultados
                                </Button>
                            </div>
                        )}

                        {video.status === 'error' && (
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1 text-xs text-destructive">
                                    <AlertCircle className="h-3 w-3" />
                                    <span>Falha no processamento</span>
                                </div>
                                <div className="ml-auto flex gap-2">
                                    {onRetry && (
                                        <Button onClick={onRetry} size="sm" variant="ghost" className="h-8 text-muted-foreground hover:text-foreground">
                                            <RefreshCw className="mr-1 h-3 w-3" />
                                            Tentar Novamente
                                        </Button>
                                    )}
                                    {onDelete && (
                                        <Button onClick={onDelete} size="sm" variant="ghost" className="h-8 text-destructive hover:text-destructive/80 hover:bg-destructive/10">
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                        )}
                        {video.status === 'queued' && (
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <Clock className="h-3 w-3" />
                                    <span>Pronto para análise</span>
                                </div>
                                <div className="flex gap-2">
                                    {onAnalyze && (
                                        <Button onClick={onAnalyze} size="sm" variant="default" className="h-8 bg-primary hover:bg-primary/90">
                                            <Sparkles className="mr-1 h-3 w-3" />
                                            Analisar com IA
                                        </Button>
                                    )}
                                    {onDelete && (
                                        <Button onClick={onDelete} size="sm" variant="ghost" className="h-8 text-destructive hover:text-destructive/80 hover:bg-destructive/10">
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Delete button for completed videos */}
                {video.status === 'completed' && onDelete && (
                    <Button
                        onClick={onDelete}
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        title="Deletar vídeo"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                )}
            </CardContent>
        </Card>
    );
}

function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
