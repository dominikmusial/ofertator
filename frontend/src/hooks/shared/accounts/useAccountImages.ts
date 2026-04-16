import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../lib/api';

export interface AccountImage {
  id: number;
  filename: string;
  original_filename: string;
  url: string;
  content_type: string;
  size: number;
  is_logo: boolean;
  is_filler: boolean;
  filler_position: number | null;
  created_at: string;
}

export interface UploadImagesResponse {
  uploaded_images: AccountImage[];
  count: number;
}

// Hook to list account images
export const useAccountImages = (accountId: number) => {
  return useQuery<AccountImage[]>({
    queryKey: ['account-images', accountId],
    queryFn: async () => {
      const response = await api.get(`/allegro/images/account/${accountId}`);
      return response.data;
    },
    enabled: !!accountId,
  });
};

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB in bytes

// Hook to upload images
export const useUploadAccountImages = () => {
  const queryClient = useQueryClient();

  return useMutation<UploadImagesResponse, Error, { accountId: number; files: File[] | FileList; filenameOverrides?: { [key: string]: string } }>({
    mutationFn: async ({ accountId, files, filenameOverrides = {} }) => {
      const fileArray = Array.from(files);
      
      // Validate file sizes before upload
      const oversizedFiles: string[] = [];
      for (const file of fileArray) {
        if (file.size > MAX_FILE_SIZE) {
          oversizedFiles.push(`${file.name} (${(file.size / (1024 * 1024)).toFixed(1)}MB)`);
        }
      }
      
      if (oversizedFiles.length > 0) {
        throw new Error(`Następujące pliki są za duże (maksymalny rozmiar: ${Math.round(MAX_FILE_SIZE / (1024 * 1024))}MB):\n${oversizedFiles.join('\n')}`);
      }

      const formData = new FormData();
      
      // Add all files to FormData
      for (const file of fileArray) {
        formData.append('files', file);
      }
      
      // Add filename overrides if provided
      if (Object.keys(filenameOverrides).length > 0) {
        formData.append('filename_overrides', JSON.stringify(filenameOverrides));
      }

      const response = await api.post(`/allegro/images/account/${accountId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalidate and refetch account images
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
};

// Hook to set logo
export const useSetAccountLogo = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { accountId: number; imageId: number }>({
    mutationFn: async ({ accountId, imageId }) => {
      const formData = new FormData();
      formData.append('image_id', imageId.toString());

      const response = await api.post(`/allegro/images/account/${accountId}/set-logo`, formData);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
};

// Hook to set fillers
export const useSetAccountFillers = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { accountId: number; imageIds: number[] }>({
    mutationFn: async ({ accountId, imageIds }) => {
      const formData = new FormData();
      imageIds.forEach(id => formData.append('image_ids', id.toString()));

      const response = await api.post(`/allegro/images/account/${accountId}/set-fillers`, formData);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
};

// Hook to delete images
export const useDeleteAccountImages = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { accountId: number; imageIds: number[] }>({
    mutationFn: async ({ accountId, imageIds }) => {
      const formData = new FormData();
      imageIds.forEach(id => formData.append('image_ids', id.toString()));

      const response = await api.delete(`/allegro/images/account/${accountId}/images`, {
        data: formData,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
};

// Hook to unset logo
export const useUnsetAccountLogo = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { accountId: number }>({
    mutationFn: async ({ accountId }) => {
      const response = await api.post(`/allegro/images/account/${accountId}/unset-logo`);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
};

// Hook to unset fillers
export const useUnsetAccountFillers = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { accountId: number }>({
    mutationFn: async ({ accountId }) => {
      const response = await api.post(`/allegro/images/account/${accountId}/unset-fillers`);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['account-images', variables.accountId] });
    },
  });
}; 