import { create } from 'zustand';
import { Folder, Video, Analysis } from '@/types';
import { apiClient } from '@/lib/api';

interface Store {
    folders: Folder[];
    isLoading: boolean;
    error: string | null;

    // Fetch data
    fetchFolders: () => Promise<void>;
    fetchFolderVideos: (folderId: string) => Promise<void>;

    // Folders (Projects in backend)
    addFolder: (name: string) => Promise<string>;
    deleteFolder: (id: string) => Promise<void>;

    // Videos
    addVideo: (folderId: string, video: Video) => void;
    uploadVideo: (folderId: string, file: File, onProgress: (p: number) => void) => Promise<Video>;
    quickAnalyze: (folderId: string, file: File, onProgress: (p: number) => void) => Promise<any>;
    updateVideoProgress: (videoId: string, progress: number) => void;
    updateVideoStatus: (videoId: string, status: Video['status']) => void;
    setVideoAnalysis: (videoId: string, analysis: Analysis) => void;
    deleteVideo: (videoId: string) => Promise<void>;
    startAnalysis: (videoId: string) => Promise<void>;
    refreshVideoStatus: (videoId: string) => Promise<void>;

    // WebSocket updates
    updateVideoFromWebSocket: (videoId: string, data: { progress?: number; status?: Video['status'] }) => void;
    markVideoCompleted: (videoId: string, analysis: any, metadata?: { duration?: number; resolution?: string }) => void;
    markVideoFailed: (videoId: string, error: string) => void;
}

export const useStore = create<Store>((set, get) => ({
    folders: [],
    isLoading: false,
    error: null,

    fetchFolders: async () => {
        set({ isLoading: true, error: null });
        try {
            const projects = await apiClient.getProjects();
            const folders: Folder[] = projects.map(p => ({
                id: p.id,
                name: p.name,
                createdAt: p.createdAt,
                videos: [],
            }));
            set({ folders, isLoading: false });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
        }
    },

    fetchFolderVideos: async (folderId: string) => {
        try {
            const videos = await apiClient.getVideos(folderId);
            set(state => ({
                folders: state.folders.map(f =>
                    f.id === folderId
                        ? {
                            ...f,
                            videos: videos.map(v => ({
                                id: v.id,
                                folderId,
                                filename: v.originalName || v.filename,
                                status: mapBackendStatus(v.status),
                                progress: v.progress,
                                duration: v.duration,
                                thumbnailUrl: v.thumbnailUrl,
                                analysis: undefined,
                            })),
                        }
                        : f
                ),
            }));
        } catch (error) {
            console.error('Failed to fetch videos:', error);
        }
    },

    addFolder: async (name: string) => {
        try {
            const project = await apiClient.createProject(name);
            const folder: Folder = {
                id: project.id,
                name: project.name,
                createdAt: project.createdAt,
                videos: [],
            };
            set(state => ({ folders: [...state.folders, folder] }));
            return project.id;
        } catch (error) {
            throw error;
        }
    },

    deleteFolder: async (id: string) => {
        try {
            await apiClient.deleteProject(id);
            set(state => ({
                folders: state.folders.filter(f => f.id !== id),
            }));
        } catch (error) {
            throw error;
        }
    },

    addVideo: (folderId, video) => set((state) => ({
        folders: state.folders.map(f =>
            f.id === folderId
                ? { ...f, videos: [...f.videos, video] }
                : f
        ),
    })),

    uploadVideo: async (folderId: string, file: File, onProgress: (p: number) => void) => {
        // Create optimistic video entry
        const tempId = `temp-${Date.now()}`;
        const tempVideo: Video = {
            id: tempId,
            folderId,
            filename: file.name,
            status: 'uploading',
            progress: 0,
        };

        // Add to store
        get().addVideo(folderId, tempVideo);

        try {
            // Try direct S3 upload first (scalable), fallback to legacy if fails
            let result: { id: string; status: string };
            try {
                result = await apiClient.uploadVideoDirect(folderId, file, (progress) => {
                    get().updateVideoProgress(tempId, progress);
                    onProgress(progress);
                });
                console.log('✅ Direct S3 upload succeeded');
            } catch (directError) {
                console.warn('⚠️ Direct S3 upload failed, using fallback:', directError);
                result = await apiClient.uploadVideo(folderId, file, (progress) => {
                    get().updateVideoProgress(tempId, progress);
                    onProgress(progress);
                });
            }

            // Replace temp with real video
            set(state => ({
                folders: state.folders.map(f => ({
                    ...f,
                    videos: f.videos.map(v =>
                        v.id === tempId
                            ? {
                                ...v,
                                id: result.id,
                                status: mapBackendStatus(result.status),
                                progress: 100,
                            }
                            : v
                    ),
                })),
            }));

            return { ...tempVideo, id: result.id, status: mapBackendStatus(result.status), progress: 100 };
        } catch (error) {
            // Update status to error
            get().updateVideoStatus(tempId, 'error');
            throw error;
        }
    },

    /**
     * Quick analyze - upload directly to Gemini, get result immediately
     * Much faster than traditional upload + queue flow
     */
    quickAnalyze: async (folderId: string, file: File, onProgress: (p: number) => void) => {
        // Create optimistic video entry
        const tempId = `temp-${Date.now()}`;
        const tempVideo: Video = {
            id: tempId,
            folderId,
            filename: file.name,
            status: 'processing',
            progress: 0,
        };

        // Add to store
        get().addVideo(folderId, tempVideo);

        try {
            // Quick analyze - direct to Gemini
            const result = await apiClient.quickAnalyze(folderId, file, (progress) => {
                get().updateVideoProgress(tempId, progress);
                onProgress(progress);
            });

            // Update video with result
            set(state => ({
                folders: state.folders.map(f => ({
                    ...f,
                    videos: f.videos.map(v =>
                        v.id === tempId
                            ? {
                                ...v,
                                id: result.videoId,
                                status: 'completed' as const,
                                progress: 100,
                                analysis: {
                                    cuts: result.analysis.decupagem?.problemas || [],
                                    subtitleErrors: result.analysis.legendas?.problemas || [],
                                    rawResponse: result.analysis,
                                    processingTime: result.processingTime,
                                },
                            }
                            : v
                    ),
                })),
            }));

            return result;
        } catch (error) {
            // Update status to error
            get().updateVideoStatus(tempId, 'error');
            throw error;
        }
    },

    updateVideoProgress: (videoId, progress) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId ? { ...v, progress } : v
            )
        })),
    })),

    updateVideoStatus: (videoId, status) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId ? { ...v, status } : v
            )
        })),
    })),

    setVideoAnalysis: (videoId, analysis) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId ? { ...v, analysis, status: 'completed' as const } : v
            )
        })),
    })),

    deleteVideo: async (videoId: string) => {
        try {
            await apiClient.deleteVideo(videoId);
            set(state => ({
                folders: state.folders.map(f => ({
                    ...f,
                    videos: f.videos.filter(v => v.id !== videoId)
                })),
            }));
        } catch (error) {
            throw error;
        }
    },

    startAnalysis: async (videoId: string) => {
        try {
            await apiClient.startAnalysis(videoId);
            get().updateVideoStatus(videoId, 'processing');
        } catch (error) {
            throw error;
        }
    },

    refreshVideoStatus: async (videoId: string) => {
        try {
            const status = await apiClient.getVideoStatus(videoId);
            get().updateVideoStatus(videoId, mapBackendStatus(status.status));
            get().updateVideoProgress(videoId, status.progress);

            // If completed, fetch analysis
            if (status.status === 'COMPLETED') {
                try {
                    const analysis = await apiClient.getAnalysis(videoId);
                    const mappedAnalysis: Analysis = {
                        cuts: Array.isArray(analysis.cutsDetected)
                            ? analysis.cutsDetected.map((c: any) => ({ timestamp: c.timestamp, type: c.type, confidence: c.confidence }))
                            : (analysis.decupagem?.problemas?.map((p: any) => ({ timestamp: p.timestamp, type: p.tipo, description: p.descricao, confidence: p.severidade === 'critico' ? 1.0 : 0.5 })) || []),
                        subtitleErrors: Array.isArray(analysis.subtitleErrors)
                            ? analysis.subtitleErrors.map((e: any) => ({ timestamp: e.timestamp, original: e.text_original, corrected: e.text_corrected, errorType: e.error_type }))
                            : (analysis.legendas?.problemas?.map((p: any) => ({ timestamp: p.timestamp, original: p.texto_original, corrected: p.texto_corrigido, errorType: p.tipo, errorDescription: p.descricao })) || []),
                        decupagem: analysis.decupagem,
                        legendas: analysis.legendas,
                        audio: analysis.audio,
                        b_roll: analysis.b_roll,
                        rawResponse: analysis.rawResponse || analysis,
                        processingTime: analysis.processingTime,
                    };
                    get().setVideoAnalysis(videoId, mappedAnalysis);
                } catch {
                    // Analysis might not be ready yet
                }
            }
        } catch (error) {
            console.error('Failed to refresh video status:', error);
        }
    },

    // WebSocket updates
    updateVideoFromWebSocket: (videoId, data) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId
                    ? {
                        ...v,
                        progress: data.progress ?? v.progress,
                        status: data.status ?? v.status,
                    }
                    : v
            )
        })),
    })),

    markVideoCompleted: (videoId, analysis, metadata) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId
                    ? {
                        ...v,
                        status: 'completed' as const,
                        progress: 100,
                        analysis: {
                            cuts: Array.isArray(analysis.cutsDetected)
                                ? analysis.cutsDetected.map((c: any) => ({ timestamp: c.timestamp, type: c.type, confidence: c.confidence }))
                                : (analysis.decupagem?.problemas?.map((p: any) => ({ timestamp: p.timestamp, type: p.tipo, description: p.descricao, confidence: p.severidade === 'critico' ? 1.0 : 0.5 })) || []),
                            subtitleErrors: Array.isArray(analysis.subtitleErrors)
                                ? analysis.subtitleErrors.map((e: any) => ({ timestamp: e.timestamp, original: e.text_original, corrected: e.text_corrected, errorType: e.error_type }))
                                : (analysis.legendas?.problemas?.map((p: any) => ({ timestamp: p.timestamp, original: p.texto_original, corrected: p.texto_corrigido, errorType: p.tipo, errorDescription: p.descricao })) || []),
                            decupagem: analysis.decupagem,
                            legendas: analysis.legendas,
                            audio: analysis.audio,
                            b_roll: analysis.b_roll,
                            rawResponse: analysis.rawResponse || analysis,
                            processingTime: analysis.processingTime,
                        },
                        // Update metadata if provided
                        ...(metadata?.duration ? { duration: metadata.duration } : {}),
                        ...(metadata?.resolution ? { resolution: metadata.resolution } : {}),
                    }
                    : v
            )
        })),
    })),

    markVideoFailed: (videoId, error) => set((state) => ({
        folders: state.folders.map(f => ({
            ...f,
            videos: f.videos.map(v =>
                v.id === videoId
                    ? { ...v, status: 'error' as const, errorMessage: error }
                    : v
            )
        })),
    })),
}));

// Map backend status to frontend status
function mapBackendStatus(status: string): Video['status'] {
    const statusMap: Record<string, Video['status']> = {
        'UPLOADING': 'uploading',
        'UPLOADED': 'queued',
        'PROCESSING': 'processing',
        'COMPLETED': 'completed',
        'FAILED': 'error',
    };
    return statusMap[status] || 'queued';
}
