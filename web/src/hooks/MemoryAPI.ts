import { useState } from 'react';
import { MemoryService } from '../services/memoryService';

// Export the Memory interface from the hook file
export interface Memory {
  id: string;
  user_name: string;
  base_model: string;
  knowledge_base: string;
  human_input: string;
  ai_response: string;
  timestamp?: string;
}

export const useMemoryApi = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const fetchMemories = async (): Promise<Memory[]> => {
        setIsLoading(true);
        setError(null);
        
        try {
            const data = await MemoryService.fetchMemories();
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(errorMessage);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    return { fetchMemories, isLoading, error };
}