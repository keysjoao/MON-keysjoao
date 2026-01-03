'use client';

import { Folder as FolderIcon, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface FolderCardProps {
    id: string;
    name: string;
    videoCount: number;
    status?: 'idle' | 'processing' | 'completed';
    onDelete: (id: string) => void;
}

export function FolderCard({ id, name, videoCount, onDelete, status = 'idle' }: FolderCardProps) {
    return (
        <Link href={`/dashboard/${id}`}>
            <Card className="group hover:border-primary/50 transition-colors cursor-pointer relative bg-card border-border">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <FolderIcon className="h-8 w-8 text-primary mb-2" />
                    <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity absolute top-2 right-2 hover:bg-destructive/20 hover:text-destructive"
                        onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            onDelete(id);
                        }}
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </CardHeader>
                <CardContent>
                    <CardTitle className="text-xl font-semibold text-foreground">{name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                        {videoCount} {videoCount === 1 ? 'vídeo' : 'vídeos'}
                    </p>
                    {status !== 'idle' && (
                        <p className="text-xs mt-2 text-primary capitalize">{status === 'processing' ? 'Processando...' : 'Concluído'}</p>
                    )}
                </CardContent>
            </Card>
        </Link>
    );
}
