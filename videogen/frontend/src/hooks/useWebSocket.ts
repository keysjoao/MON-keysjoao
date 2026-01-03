'use client';

import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useStore } from '@/store/useStore';

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export function useWebSocket(projectId?: string) {
    const socketRef = useRef<Socket | null>(null);
    const updateVideoInStore = useStore((state) => state.updateVideoFromWebSocket);
    const markVideoCompleted = useStore((state) => state.markVideoCompleted);
    const markVideoFailed = useStore((state) => state.markVideoFailed);

    useEffect(() => {
        // Connect to WebSocket
        socketRef.current = io(SOCKET_URL, {
            transports: ['websocket', 'polling'],
        });

        const socket = socketRef.current;

        socket.on('connect', () => {
            console.log('🔌 WebSocket connected');

            // Subscribe to project updates if projectId provided
            if (projectId) {
                socket.emit('subscribe:project', { projectId });
            }
        });

        socket.on('video:progress', (data: { videoId: string; progress: number; status: string }) => {
            console.log('📊 Video progress:', data);
            updateVideoInStore(data.videoId, {
                progress: data.progress,
                status: mapStatus(data.status),
            });
        });

        socket.on('video:completed', (data: { videoId: string; analysis: any; metadata?: { duration?: number; resolution?: string } }) => {
            console.log('✅ Video completed:', data);
            markVideoCompleted(data.videoId, data.analysis, data.metadata);
        });

        socket.on('video:failed', (data: { videoId: string; error: string }) => {
            console.log('❌ Video failed:', data);
            markVideoFailed(data.videoId, data.error);
        });

        socket.on('disconnect', () => {
            console.log('🔌 WebSocket disconnected');
        });

        return () => {
            if (projectId) {
                socket.emit('unsubscribe:project', { projectId });
            }
            socket.disconnect();
        };
    }, [projectId, updateVideoInStore, markVideoCompleted, markVideoFailed]);

    // Subscribe to specific video updates
    const subscribeToVideo = (videoId: string) => {
        if (socketRef.current?.connected) {
            socketRef.current.emit('subscribe:video', { videoId });
        }
    };

    const unsubscribeFromVideo = (videoId: string) => {
        if (socketRef.current?.connected) {
            socketRef.current.emit('unsubscribe:video', { videoId });
        }
    };

    return { subscribeToVideo, unsubscribeFromVideo };
}

function mapStatus(status: string): 'uploading' | 'queued' | 'processing' | 'completed' | 'error' {
    const statusMap: Record<string, 'uploading' | 'queued' | 'processing' | 'completed' | 'error'> = {
        'UPLOADING': 'uploading',
        'UPLOADED': 'queued',
        'PROCESSING': 'processing',
        'COMPLETED': 'completed',
        'FAILED': 'error',
    };
    return statusMap[status] || 'processing';
}
