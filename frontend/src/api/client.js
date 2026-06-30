const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = {
  getUniversities: async () => {
    const response = await fetch(`${API_BASE_URL}/universities`);
    if (!response.ok) throw new Error('Failed to fetch universities');
    return response.json();
  }
};
