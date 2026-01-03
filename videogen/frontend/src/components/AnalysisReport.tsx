'use client';

import { Video } from '@/types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    CheckCircle2,
    XCircle,
    AlertTriangle,
    Scissors,
    Subtitles,
    Clock,
    ArrowLeft,
    FileText,
    Video as VideoIcon,
    Timer,
    Languages
} from 'lucide-react';

interface AnalysisReportProps {
    video: Video;
    onClose: () => void;
}

interface DecupageProblema {
    timestamp: string;
    tipo: string;
    descricao: string;
    severidade: 'critico' | 'menor';
    sugestao?: string;
}

interface LegendaProblema {
    timestamp: string;
    tipo: string;
    texto_original?: string;
    texto_corrigido?: string;
    descricao: string;
    severidade: 'critico' | 'menor';
}

interface ResumoAnalise {
    duracao_video?: string;
    quantidade_cortes?: number;
    tem_legendas?: boolean;
    idioma_detectado?: string;
    tipo_conteudo?: string;
}

export function AnalysisReport({ video, onClose }: AnalysisReportProps) {
    const analysis = video.analysis;

    // Parse the rawResponse if available, otherwise use legacy format
    const rawResponse = analysis?.rawResponse as any;

    const aprovado = rawResponse?.aprovado ?? (
        (analysis?.cuts?.length === 0 || !analysis?.cuts) &&
        (analysis?.subtitleErrors?.length === 0 || !analysis?.subtitleErrors)
    );

    const resumo = rawResponse?.resumo ?? (aprovado
        ? 'Vídeo aprovado! Nenhum problema encontrado.'
        : 'Vídeo necessita revisão antes de postar.');

    function formatDuration(seconds: any): string {
        if (!seconds) return 'N/A';
        const secNum = typeof seconds === 'string' ? parseFloat(seconds) : seconds;
        if (isNaN(secNum)) return 'N/A';
        const m = Math.floor(secNum / 60);
        const s = Math.floor(secNum % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    const resumoAnalise: ResumoAnalise = rawResponse?.resumo_analise ?? {
        duracao_video: video.duration ? formatDuration(video.duration) : undefined,
        quantidade_cortes: rawResponse?.decupagem?.total_cortes ?? analysis?.cuts?.length ?? 0,
        tem_legendas: rawResponse?.legendas?.tem_legendas,
        tipo_conteudo: undefined
    };

    const decupagem = analysis?.decupagem ?? rawResponse?.decupagem ?? {
        aprovado: !analysis?.cuts?.length,
        total_cortes: analysis?.cuts?.length ?? 0,
        problemas: analysis?.cuts?.map((c: any) => ({
            timestamp: c.timestamp,
            tipo: c.type || 'corte_abrupto',
            descricao: c.description,
            severidade: c.confidence > 0.8 ? 'critico' : 'menor',
            sugestao: 'Revise o corte neste ponto'
        })) ?? []
    };

    const legendas = analysis?.legendas ?? rawResponse?.legendas ?? {
        aprovado: !analysis?.subtitleErrors?.length,
        tem_legendas: Boolean(analysis?.subtitleErrors?.length),
        problemas: analysis?.subtitleErrors?.map((e: any) => ({
            timestamp: e.timestamp,
            tipo: e.errorType || 'erro_portugues',
            texto_original: e.original,
            texto_corrigido: e.corrected,
            descricao: e.errorDescription || `Erro de ${e.errorType}`,
            severidade: e.severity === 'high' ? 'critico' : 'menor'
        })) ?? []
    };

    const audio = analysis?.audio ?? rawResponse?.audio;
    const b_roll = analysis?.b_roll ?? rawResponse?.b_roll;

    const problemasCriticos = (decupagem.problemas?.filter((p: any) => p.severidade === 'critico').length ?? 0) +
        (legendas.problemas?.filter((p: any) => p.severidade === 'critico').length ?? 0) +
        (audio?.problemas?.filter((p: any) => p.severidade === 'critico').length ?? 0) +
        (b_roll?.problemas?.filter((p: any) => p.severidade === 'critico').length ?? 0);

    const problemasMenores = (decupagem.problemas?.filter((p: any) => p.severidade === 'menor').length ?? 0) +
        (legendas.problemas?.filter((p: any) => p.severidade === 'menor').length ?? 0) +
        (audio?.problemas?.filter((p: any) => p.severidade === 'menor').length ?? 0) +
        (b_roll?.problemas?.filter((p: any) => p.severidade === 'menor').length ?? 0);

    return (
        <Card className="w-full max-w-2xl mx-auto bg-card border-border overflow-hidden">
            {/* Header with Verdict */}
            <CardHeader className={`p-6 ${aprovado ? 'bg-success/10' : 'bg-destructive/10'}`}>
                <div className="flex items-center justify-between">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onClose}
                        className="text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="h-4 w-4 mr-1" />
                        Voltar
                    </Button>
                    <Badge variant="outline" className="text-xs">
                        <FileText className="h-3 w-3 mr-1" />
                        Relatório de QA
                    </Badge>
                </div>

                <div className="flex items-center gap-4 mt-4">
                    {aprovado ? (
                        <CheckCircle2 className="h-16 w-16 text-success" />
                    ) : (
                        <XCircle className="h-16 w-16 text-destructive" />
                    )}
                    <div>
                        <h2 className={`text-3xl font-bold ${aprovado ? 'text-success' : 'text-destructive'}`}>
                            {aprovado ? 'APTO' : 'INAPTO'}
                        </h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            {video.filename}
                        </p>
                    </div>
                </div>

                <p className="text-foreground mt-4 text-sm">
                    {resumo}
                </p>

                {/* Stats */}
                <div className="flex gap-4 mt-4">
                    {problemasCriticos > 0 && (
                        <Badge variant="destructive" className="gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            {problemasCriticos} crítico{problemasCriticos > 1 ? 's' : ''}
                        </Badge>
                    )}
                    {problemasMenores > 0 && (
                        <Badge variant="secondary" className="gap-1">
                            {problemasMenores} menor{problemasMenores > 1 ? 'es' : ''}
                        </Badge>
                    )}
                    {problemasCriticos === 0 && problemasMenores === 0 && (
                        <Badge variant="outline" className="gap-1 text-success border-success/30">
                            <CheckCircle2 className="h-3 w-3" />
                            Sem problemas
                        </Badge>
                    )}
                </div>
            </CardHeader>

            <CardContent className="p-6 space-y-6">
                {/* Mini Analysis Summary */}
                <div className="flex flex-wrap gap-2 pb-4 border-b border-border">
                    {resumoAnalise.duracao_video && (
                        <Badge variant="outline" className="gap-1 text-xs">
                            <Timer className="h-3 w-3" />
                            {resumoAnalise.duracao_video}
                        </Badge>
                    )}
                    <Badge variant="outline" className="gap-1 text-xs">
                        <Scissors className="h-3 w-3" />
                        {resumoAnalise.quantidade_cortes ?? decupagem.total_cortes ?? 0} cortes
                    </Badge>
                    <Badge variant="outline" className={`gap-1 text-xs ${legendas.tem_legendas ? 'text-success border-success/30' : 'text-muted-foreground'}`}>
                        <Subtitles className="h-3 w-3" />
                        {legendas.tem_legendas ? 'Com legendas' : 'Sem legendas'}
                    </Badge>
                    {resumoAnalise.idioma_detectado && (
                        <Badge variant="outline" className="gap-1 text-xs">
                            <Languages className="h-3 w-3" />
                            {resumoAnalise.idioma_detectado}
                        </Badge>
                    )}
                    {resumoAnalise.tipo_conteudo && (
                        <Badge variant="outline" className="gap-1 text-xs">
                            <VideoIcon className="h-3 w-3" />
                            {resumoAnalise.tipo_conteudo}
                        </Badge>
                    )}
                </div>
                {/* Decupagem Section */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <Scissors className="h-5 w-5 text-primary" />
                        <h3 className="font-semibold">Decupagem (Cortes)</h3>
                        {decupagem.aprovado ? (
                            <CheckCircle2 className="h-4 w-4 text-success ml-auto" />
                        ) : (
                            <AlertTriangle className="h-4 w-4 text-warning ml-auto" />
                        )}
                    </div>

                    {decupagem.problemas?.length > 0 ? (
                        <div className="space-y-2">
                            {decupagem.problemas.map((problema: DecupageProblema, i: number) => (
                                <div
                                    key={i}
                                    className={`p-3 rounded-lg border ${problema.severidade === 'critico'
                                        ? 'border-destructive/30 bg-destructive/5'
                                        : 'border-warning/30 bg-warning/5'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 mb-1">
                                        <Clock className="h-3 w-3 text-muted-foreground" />
                                        <span className="text-xs font-mono text-muted-foreground">
                                            {problema.timestamp}
                                        </span>
                                        <Badge
                                            variant={problema.severidade === 'critico' ? 'destructive' : 'secondary'}
                                            className="text-xs"
                                        >
                                            {problema.tipo.replace('_', ' ')}
                                        </Badge>
                                    </div>
                                    <p className="text-sm">{problema.descricao}</p>
                                    {problema.sugestao && (
                                        <p className="text-xs text-muted-foreground mt-1">
                                            💡 {problema.sugestao}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-success flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4" />
                            Cortes OK - Nenhum problema de timing detectado
                        </p>
                    )}
                </div>

                {/* Legendas Section */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <Subtitles className="h-5 w-5 text-primary" />
                        <h3 className="font-semibold">Legendas & Safe Zone</h3>
                        {legendas.aprovado ? (
                            <CheckCircle2 className="h-4 w-4 text-success ml-auto" />
                        ) : (
                            <AlertTriangle className="h-4 w-4 text-warning ml-auto" />
                        )}
                    </div>
                    {/* ... existing legendas display logic ... */}
                    {!legendas.tem_legendas && legendas.problemas?.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                            Nenhuma legenda detectada. Verifique se estão embutidas.
                        </p>
                    ) : legendas.problemas?.length > 0 ? (
                        <div className="space-y-2">
                            {legendas.problemas.map((problema: LegendaProblema, i: number) => (
                                <div key={i} className={`p-3 rounded-lg border ${problema.severidade === 'critico' ? 'border-destructive/30 bg-destructive/5' : 'border-warning/30 bg-warning/5'}`}>
                                    <div className="flex items-center gap-2 mb-1">
                                        <Clock className="h-3 w-3 text-muted-foreground" />
                                        <span className="text-xs font-mono text-muted-foreground">{problema.timestamp}</span>
                                        <Badge variant={problema.severidade === 'critico' ? 'destructive' : 'secondary'} className="text-xs">
                                            {problema.tipo?.replace('_', ' ')}
                                        </Badge>
                                    </div>
                                    <p className="text-sm">{problema.descricao}</p>
                                    {problema.texto_original && problema.texto_corrigido && (
                                        <div className="mt-2 text-xs">
                                            <span className="text-destructive/80 line-through">{problema.texto_original}</span>
                                            <span className="mx-2">→</span>
                                            <span className="text-success/90">{problema.texto_corrigido}</span>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-success flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4" />
                            Legendas OK - Português, Sincronia e Safe Zone
                        </p>
                    )}
                </div>

                {/* Audio Section */}
                {audio && (
                    <div className="space-y-3 pt-4 border-t border-border">
                        <div className="flex items-center gap-2">
                            <VideoIcon className="h-5 w-5 text-primary" />
                            <h3 className="font-semibold">Áudio & Mixagem</h3>
                            {audio.aprovado ? (
                                <CheckCircle2 className="h-4 w-4 text-success ml-auto" />
                            ) : (
                                <AlertTriangle className="h-4 w-4 text-warning ml-auto" />
                            )}
                        </div>
                        {audio.problemas?.length > 0 ? (
                            <div className="space-y-2">
                                {audio.problemas.map((p: any, i: number) => {
                                    // Handle both old format (timestamp, descricao, severidade) and new format (tipo, localizacao, detalhes)
                                    const timestamp = p.timestamp || p.localizacao;
                                    const tipo = p.tipo || 'audio';
                                    const descricao = p.descricao || p.detalhes || (typeof p === 'string' ? p : JSON.stringify(p));
                                    const severidade = p.severidade || 'critico';

                                    return (
                                        <div key={i} className={`p-3 rounded-lg border ${severidade === 'critico' ? 'border-destructive/30 bg-destructive/5' : 'border-warning/30 bg-warning/5'}`}>
                                            <div className="flex items-center gap-2 mb-1">
                                                {timestamp && (
                                                    <>
                                                        <Clock className="h-3 w-3 text-muted-foreground" />
                                                        <span className="text-xs font-mono text-muted-foreground">{timestamp}</span>
                                                    </>
                                                )}
                                                <Badge variant={severidade === 'critico' ? 'destructive' : 'secondary'} className="text-xs">
                                                    {tipo.replace('_', ' ')}
                                                </Badge>
                                            </div>
                                            <p className="text-sm">{descricao}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-sm text-success flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4" />
                                Áudio OK - Voz clara e música equilibrada
                            </p>
                        )}
                    </div>
                )}

                {/* B-Roll Section */}
                {b_roll && (
                    <div className="space-y-3 pt-4 border-t border-border">
                        <div className="flex items-center gap-2">
                            <VideoIcon className="h-5 w-5 text-primary" />
                            <h3 className="font-semibold">B-Rolls & Contexto</h3>
                            {b_roll.aprovado ? (
                                <CheckCircle2 className="h-4 w-4 text-success ml-auto" />
                            ) : (
                                <AlertTriangle className="h-4 w-4 text-warning ml-auto" />
                            )}
                        </div>
                        {b_roll.problemas?.length > 0 ? (
                            <div className="space-y-2">
                                {b_roll.problemas.map((p: any, i: number) => (
                                    <div key={i} className={`p-3 rounded-lg border ${p.severidade === 'critico' ? 'border-destructive/30 bg-destructive/5' : 'border-warning/30 bg-warning/5'}`}>
                                        <div className="flex items-center gap-2 mb-1">
                                            {p.timestamp && (
                                                <>
                                                    <Clock className="h-3 w-3 text-muted-foreground" />
                                                    <span className="text-xs font-mono text-muted-foreground">{p.timestamp}</span>
                                                </>
                                            )}
                                            <Badge variant={p.severidade === 'critico' ? 'destructive' : 'secondary'} className="text-xs">
                                                {p.tipo ? p.tipo.replace('_', ' ') : 'Problema Visual'}
                                            </Badge>
                                        </div>
                                        <p className="text-sm text-warning">{p.descricao || p}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-success flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4" />
                                Contexto Visual OK
                            </p>
                        )}
                    </div>
                )}

                {/* Footer */}
                <div className="pt-4 border-t border-border">
                    <p className="text-xs text-muted-foreground text-center">
                        Analisado com Gemini AI • Tempo de processamento: {analysis?.processingTime ? `${analysis.processingTime.toFixed(1)}s` : 'N/A'}
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}
