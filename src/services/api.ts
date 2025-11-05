const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiError {
  detail: string;
}

interface User {
  id: string;
  email: string;
  name?: string;
  credits: number;
  subscription_tier: string;
}

interface TransformationResponse {
  job_id: string;
  status: string;
  original_url: string;
  transformed_url?: string;
  processing_time?: number;
  created_at: string;
  completed_at?: string;
  metadata: Record<string, any>;
}

class ApiService {
  private baseURL = API_BASE_URL;

  // Helper to get auth token
  private getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Helper to build headers
  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  // Helper to handle response
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An error occurred'
      }));
      throw new Error(error.detail);
    }
    return response.json();
  }

  // ========== AUTH ENDPOINTS ==========

  async register(email: string, password: string, name?: string): Promise<User> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({ email, password, name }),
    });
    return this.handleResponse<User>(response);
  }

  async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({ email, password }),
    });
    const data = await this.handleResponse<{ access_token: string; refresh_token: string }>(response);

    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // ========== USER ENDPOINTS ==========

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseURL}/api/v1/user/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<User>(response);
  }

  async getUserCredits(): Promise<{ credits: number; subscription_tier: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/user/credits`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(response);
  }

  // ========== TRANSFORMATION ENDPOINTS ==========

  async createTransformation(
    image: File,
    vibe: string,
    colors: string,
    description?: string,
    referenceImages?: File[]
  ): Promise<TransformationResponse> {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('vibe', vibe);
    formData.append('colors', colors);
    if (description) {
      formData.append('description', description);
    }
    if (referenceImages) {
      referenceImages.forEach((ref) => {
        formData.append('reference_images', ref);
      });
    }

    const token = this.getAuthToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}/api/v1/transform/transform`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return this.handleResponse<TransformationResponse>(response);
  }

  async getTransformationStatus(jobId: string): Promise<TransformationResponse> {
    const token = this.getAuthToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}/api/v1/transform/${jobId}`, {
      headers,
    });
    return this.handleResponse<TransformationResponse>(response);
  }

  async getTransformationHistory(limit = 10, offset = 0): Promise<{
    transformations: TransformationResponse[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await fetch(
      `${this.baseURL}/api/v1/transform/history?limit=${limit}&offset=${offset}`,
      {
        headers: this.getHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  // ========== HEALTH CHECK ==========

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/health`);
    return this.handleResponse(response);
  }
}

export const apiService = new ApiService();
export default apiService;
