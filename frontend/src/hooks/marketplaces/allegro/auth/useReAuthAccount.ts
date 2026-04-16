import { useState } from 'react';
import { api } from '../../../../lib/api';

interface ReAuthResponse {
  user_code: string;
  verification_uri: string;
  task_id: string;
  account_id: number;
  account_name: string;
}

export const useReAuthAccount = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startReAuth = async (accountId: number): Promise<ReAuthResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<ReAuthResponse>(
        `/allegro/accounts/${accountId}/re-authenticate/start`
      );
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to start re-authentication';
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    startReAuth,
    isLoading,
    error,
  };
};


