const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface ApiResponse<T> {
    status: 'success' | 'error';
    data?: T;
    code?: string;
    message?: string;
}

class ApiClient {
    private token: string | null = null;

    constructor() {
        // Load token from localStorage on init
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('token');
        }
    }

    setToken(token: string | null) {
        this.token = token;
        if (typeof window !== 'undefined') {
            if (token) {
                localStorage.setItem('token', token);
            } else {
                localStorage.removeItem('token');
            }
        }
    }

    getToken() {
        return this.token;
    }

    private async fetch<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const headers: HeadersInit = {
            ...options.headers,
        };

        // Add Content-Type for JSON requests only when there's a body
        if (options.body && !(options.body instanceof FormData)) {
            (headers as Record<string, string>)['Content-Type'] = 'application/json';
        }

        // Add auth header if token exists
        if (this.token) {
            (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Request failed' }));
            throw new Error(error.message || `HTTP ${response.status}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    }

    // Auth
    async register(email: string, password: string, name: string) {
        const res = await this.fetch<ApiResponse<{
            user: { id: string; email: string; name: string };
            token: string;
            refreshToken: string;
        }>>('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, name }),
        });
        if (res.data?.token) {
            this.setToken(res.data.token);
        }
        return res.data!;
    }

    async login(email: string, password: string) {
        const res = await this.fetch<ApiResponse<{
            user: { id: string; email: string; name: string };
            token: string;
            refreshToken: string;
        }>>('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        if (res.data?.token) {
            this.setToken(res.data.token);
        }
        return res.data!;
    }

    async getMe() {
        const res = await this.fetch<ApiResponse<{
            id: string;
            email: string;
            name: string;
            projectCount: number;
        }>>('/api/auth/me');
        return res.data!;
    }

    logout() {
        this.setToken(null);
        if (typeof window !== 'undefined') {
            localStorage.removeItem('refreshToken');
        }
    }

    // Projects (called Folders in frontend)
    async getProjects() {
        const res = await this.fetch<ApiResponse<{
            projects: Array<{
                id: string;
                name: string;
                description?: string;
                createdAt: string;
                videoCount: number;
            }>;
            pagination: { page: number; limit: number; total: number };
        }>>('/api/projects');
        return res.data!.projects;
    }

    async createProject(name: string, description?: string) {
        const res = await this.fetch<ApiResponse<{
            id: string;
            name: string;
            description?: string;
            createdAt: string;
            videoCount: number;
        }>>('/api/projects', {
            method: 'POST',
            body: JSON.stringify({ name, description }),
        });
        return res.data!;
    }

    async getProject(id: string) {
        const res = await this.fetch<ApiResponse<{
            id: string;
            name: string;
            description?: string;
            createdAt: string;
            videoCount: number;
            videos: Array<{
                id: string;
                filename: string;
                originalName: string;
                status: string;
                progress: number;
                thumbnailKey?: string;
                uploadedAt: string;
            }>;
        }>>(`/api/projects/${id}`);
        return res.data!;
    }

    async deleteProject(id: string) {
        await this.fetch(`/api/projects/${id}`, { method: 'DELETE' });
    }

    // Videos
    async getVideos(projectId: string) {
        const res = await this.fetch<ApiResponse<{
            videos: Array<{
                id: string;
                filename: string;
                originalName: string;
                status: string;
                progress: number;
                thumbnailUrl?: string;
                duration?: number;
                analysis?: { id: string };
            }>;
            pagination: { page: number; limit: number; total: number };
        }>>(`/api/projects/${projectId}/videos`);
        return res.data!.videos;
    }

    async uploadVideo(
        projectId: string,
        file: File,
        onProgress?: (progress: number) => void
    ): Promise<{ id: string; status: string }> {
        const formData = new FormData();
        formData.append('file', file);

        // Use XMLHttpRequest for progress tracking
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    const progress = Math.round((e.loaded / e.total) * 100);
                    onProgress(progress);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response.data);
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            };

            xhr.onerror = () => {
                console.error('Upload XHR Error:', xhr.status, xhr.statusText);
                reject(new Error('Network error during upload'));
            };

            xhr.ontimeout = () => {
                console.error('Upload XHR Timeout');
                reject(new Error('Upload timed out'));
            };

            xhr.open('POST', `${API_BASE_URL}/api/projects/${projectId}/videos/upload`);

            // Disable timeout (0 means no timeout) calling it after open is safe
            xhr.timeout = 0;

            if (this.token) {
                xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            }
            xhr.send(formData);
        });
    }

    /**
     * Get a presigned URL for direct S3 upload
     */
    async getUploadUrl(
        projectId: string,
        filename: string,
        contentType: string,
        fileSize: number
    ): Promise<{ uploadUrl: string; videoId: string; storageKey: string; expiresIn: number }> {
        const res = await this.fetch<ApiResponse<{
            uploadUrl: string;
            videoId: string;
            storageKey: string;
            expiresIn: number;
        }>>(`/api/projects/${projectId}/videos/upload-url`, {
            method: 'POST',
            body: JSON.stringify({ filename, contentType, fileSize }),
        });
        return res.data!;
    }

    /**
     * Confirm that a direct S3 upload has completed
     */
    async confirmUpload(projectId: string, videoId: string): Promise<{ id: string; status: string }> {
        const res = await this.fetch<ApiResponse<{
            id: string;
            status: string;
        }>>(`/api/projects/${projectId}/videos/${videoId}/confirm`, {
            method: 'POST',
        });
        return res.data!;
    }

    /**
     * Upload video directly to S3 using presigned URL (faster, bypasses server)
     */
    async uploadVideoDirect(
        projectId: string,
        file: File,
        onProgress?: (progress: number) => void
    ): Promise<{ id: string; status: string }> {
        // 1. Get presigned URL from backend
        const { uploadUrl, videoId } = await this.getUploadUrl(
            projectId,
            file.name,
            file.type || 'video/mp4',
            file.size
        );

        // 2. Upload directly to S3
        await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    const progress = Math.round((e.loaded / e.total) * 100);
                    onProgress(progress);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    reject(new Error(`S3 upload failed: ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('S3 upload failed'));

            xhr.open('PUT', uploadUrl);
            xhr.setRequestHeader('Content-Type', file.type || 'video/mp4');
            xhr.send(file);
        });

        // 3. Confirm upload completed
        const result = await this.confirmUpload(projectId, videoId);
        return result;
    }

    async getVideo(id: string) {
        const res = await this.fetch<ApiResponse<{
            id: string;
            filename: string;
            originalName: string;
            status: string;
            progress: number;
            duration?: number;
            thumbnailUrl?: string;
            analysis?: {
                id: string;
                cutsDetected: Array<{
                    timestamp: string;
                    type: string;
                    confidence: number;
                    description?: string;
                }>;
                subtitleErrors: Array<{
                    timestamp: string;
                    text_original: string;
                    text_corrected: string;
                    error_type: string;
                }>;
            };
        }>>(`/api/videos/${id}`);
        return res.data!;
    }

    async getVideoStatus(id: string) {
        const res = await this.fetch<ApiResponse<{
            id: string;
            status: string;
            progress: number;
            errorMessage?: string;
        }>>(`/api/videos/${id}/status`);
        return res.data!;
    }

    async startAnalysis(videoId: string, analysisType: 'full' | 'cuts-only' | 'subtitles-only' = 'full') {
        const res = await this.fetch<ApiResponse<{
            message: string;
            videoId: string;
            status: string;
        }>>(`/api/videos/${videoId}/analyze`, {
            method: 'POST',
            body: JSON.stringify({ analysisType }),
        });
        return res.data!;
    }

    async deleteVideo(id: string) {
        await this.fetch(`/api/videos/${id}`, { method: 'DELETE' });
    }

    // Analysis
    async getAnalysis(videoId: string) {
        const res = await this.fetch<ApiResponse<any>>(`/api/analysis/${videoId}`);
        return res.data!;
    }

    async exportAnalysis(videoId: string, format: 'csv' | 'json' = 'json'): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/analysis/${videoId}/export?format=${format}`,
            {
                headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
            }
        );
        return response.blob();
    }

    async retryAnalysis(videoId: string) {
        const res = await this.fetch<ApiResponse<{
            message: string;
            videoId: string;
            status: string;
        }>>(`/api/analysis/${videoId}/retry`, {
            method: 'POST',
        });
        return res.data!;
    }

    /**
     * Quick analyze - upload directly to Gemini, get result immediately
     * Much faster than upload → queue → analyze flow
     */
    async quickAnalyze(
        projectId: string,
        file: File,
        onProgress?: (progress: number) => void
    ): Promise<{
        videoId: string;
        approved: boolean;
        summary: string;
        criticalIssues: number;
        minorIssues: number;
        processingTime: number;
        analysis: any;
    }> {
        const formData = new FormData();
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    // Only first 30% is upload, rest is Gemini processing
                    const progress = Math.round((e.loaded / e.total) * 30);
                    onProgress(progress);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    const response = JSON.parse(xhr.responseText);
                    onProgress?.(100);
                    resolve(response.data);
                } else {
                    reject(new Error(`Quick analyze failed: ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('Quick analyze failed'));

            xhr.open('POST', `${API_BASE_URL}/api/projects/${projectId}/videos/quick-analyze`);
            if (this.token) {
                xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            }
            xhr.send(formData);
        });
    }
}

export const apiClient = new ApiClient();
