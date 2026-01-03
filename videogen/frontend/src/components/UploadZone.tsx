'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Video } from '@/types';

interface UploadZoneProps {
    folderId: string;
    onUpload: (files: File[]) => void;
}

export function UploadZone({ folderId, onUpload }: UploadZoneProps) {
    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            onUpload(acceptedFiles);
        }
    }, [onUpload]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/mp4': ['.mp4'],
            'video/quicktime': ['.mov'],
            'video/x-msvideo': ['.avi'],
        },
        multiple: true
    });

    return (
        <div
            {...getRootProps()}
            className={cn(
                "border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-colors bg-card/40 shadow-[var(--shadow-soft)]",
                isDragActive ? "border-primary/70 bg-primary/10" : "border-border/60 hover:border-primary/50 hover:bg-card/60"
            )}
        >
            <input {...getInputProps()} />
            <div className="bg-primary/15 p-4 rounded-full mb-4 border border-primary/30">
                <UploadCloud className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Arraste vídeos aqui</h3>
            <p className="text-muted-foreground text-sm text-center">
                ou clique para selecionar arquivos<br />
                <span className="text-xs opacity-70">MP4, MOV, AVI</span>
            </p>
        </div>
    );
}
