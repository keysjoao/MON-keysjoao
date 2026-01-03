export interface Folder {
    id: string;
    name: string;
    createdAt: string;
    videos: Video[];
}

export interface Video {
    id: string;
    folderId: string;
    filename: string;
    status: 'uploading' | 'queued' | 'processing' | 'completed' | 'error';
    progress: number;
    duration?: number;
    thumbnailUrl?: string;
    analysis?: Analysis;
}

export interface Analysis {
    cuts: Array<{
        timestamp: string;
        type: string;
        confidence: number;
    }>;
    subtitleErrors: Array<{
        timestamp: string;
        original: string;
        corrected: string;
        errorType: string;
    }>;
    // New fields
    decupagem?: {
        aprovado: boolean;
        total_cortes: number;
        problemas: Array<{
            timestamp: string;
            tipo: string;
            descricao: string;
            severidade: 'critico' | 'menor';
            sugestao?: string;
        }>;
    };
    legendas?: {
        aprovado: boolean;
        tem_legendas: boolean;
        estilo_legenda?: string;
        problemas: Array<{
            timestamp: string;
            tipo: string;
            texto_original?: string;
            texto_corrigido?: string;
            descricao: string;
            severidade: 'critico' | 'menor';
        }>;
    };
    audio?: {
        aprovado: boolean;
        problemas: Array<{
            timestamp: string;
            tipo: string;
            descricao: string;
            severidade: 'critico' | 'menor';
        }>;
    };
    b_roll?: {
        aprovado: boolean;
        problemas: Array<{
            timestamp: string;
            tipo: string;
            descricao: string;
            severidade: 'critico' | 'menor';
        }>;
    };
    rawResponse?: Record<string, unknown>;
    processingTime?: number;
}
