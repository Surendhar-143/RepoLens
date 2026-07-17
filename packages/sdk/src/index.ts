import axios, { AxiosInstance } from 'axios';

export interface HealthResponse {
  status: string;
}

export interface VersionResponse {
  version: string;
  name: string;
}

export class RepoLensClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async getVersion(): Promise<VersionResponse> {
    const response = await this.client.get<VersionResponse>('/version');
    return response.data;
  }
}
