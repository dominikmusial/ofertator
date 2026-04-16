import { useState, useEffect } from 'react';
import api from '../../../lib/api';

export const useAuthenticatedImage = (imageUrl: string | null) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!imageUrl) {
      setBlobUrl(null);
      return;
    }

    const fetchImage = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await api.get(imageUrl, {
          responseType: 'blob'
        });
        
        const blob = new Blob([response.data], { 
          type: response.headers['content-type'] || 'image/jpeg' 
        });
        const url = URL.createObjectURL(blob);
        setBlobUrl(url);
      } catch (err: any) {
        setError(err.message || 'Failed to load image');
        setBlobUrl(null);
      } finally {
        setLoading(false);
      }
    };

    fetchImage();

    // Cleanup function to revoke blob URL
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [imageUrl]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  return { blobUrl, loading, error };
}; 