const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

export interface TriangleAnalysisRequest {
    csv: File;
    origin_col?: string;
    dev_col?: string;
    value_col?: string;
    cumulative?: boolean;
}

export interface TriangleAnalysisResponse {
    mack_ultimate: number | null;
    mack_mse: number | null;
    cape_cod_ultimate: number | null;
    ldfs: Array<{
        origin: string;
        development: string;
        ldf: number | null;
    }>;
}

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    async analyzeTriangle(request: TriangleAnalysisRequest): Promise<TriangleAnalysisResponse> {
        const formData = new FormData();
        formData.append("csv", request.csv);
        formData.append("origin_col", request.origin_col || "origin");
        formData.append("dev_col", request.dev_col || "dev");
        formData.append("value_col", request.value_col || "value");
        formData.append("cumulative", request.cumulative !== false ? "true" : "false");

        const response = await fetch(`${this.baseUrl}/reserving/analyze`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    async healthCheck(): Promise<{ status: string }> {
        const response = await fetch(`${this.baseUrl}/health`);
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        return response.json();
    }
}

// Export a default instance
export const apiClient = new ApiClient();
