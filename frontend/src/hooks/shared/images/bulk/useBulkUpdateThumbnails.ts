import { useMutation } from '@tanstack/react-query'
import api from '../../../../lib/api'

interface BulkUpdateThumbnailsParams {
  accountId: number
  offerIds: string[]
  imageFiles: File[]
  extractIdsFromNames: boolean
}

interface TaskResponse {
  task_id: string
  offer_id: string
}

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB in bytes
const MAX_TOTAL_SIZE = 100 * 1024 * 1024 // 100MB total for bulk uploads

export const useBulkUpdateThumbnails = () => {
  return useMutation({
    mutationFn: async ({ accountId, offerIds, imageFiles, extractIdsFromNames }: BulkUpdateThumbnailsParams): Promise<TaskResponse[]> => {
      // Validate individual file sizes
      const oversizedFiles: string[] = [];
      let totalSize = 0;
      
      imageFiles.forEach(file => {
        totalSize += file.size;
        if (file.size > MAX_FILE_SIZE) {
          oversizedFiles.push(`${file.name} (${(file.size / (1024 * 1024)).toFixed(1)}MB)`);
        }
      });
      
      if (oversizedFiles.length > 0) {
        throw new Error(`Następujące pliki są za duże (maksymalny rozmiar pojedynczego pliku: ${Math.round(MAX_FILE_SIZE / (1024 * 1024))}MB):\n${oversizedFiles.join('\n')}`);
      }

      // Validate total upload size
      if (totalSize > MAX_TOTAL_SIZE) {
        const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
        const maxSizeMB = Math.round(MAX_TOTAL_SIZE / (1024 * 1024));
        throw new Error(`Całkowity rozmiar przesyłanych plików jest za duży (${totalSizeMB}MB). Maksymalny rozmiar dla jednej operacji to ${maxSizeMB}MB.\n\nProponowane rozwiązania:\n• Podziel pliki na mniejsze grupy\n• Zmniejsz rozmiar obrazów przed przesłaniem\n• Usuń niepotrzebne pliki z wyboru`);
      }

      const formData = new FormData()
      
      // Add offer IDs as JSON string in body
      formData.append('offer_ids', JSON.stringify(offerIds))
      
      // Add image files
      imageFiles.forEach(file => {
        formData.append('image_files', file)
      })
      
      // Add extract flag
      formData.append('extract_ids_from_names', extractIdsFromNames.toString())

      try {
        const response = await api.post(`/allegro/offers/bulk-update-thumbnails?account_id=${accountId}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        
        return response.data
      } catch (error: any) {
        // Handle specific HTTP error codes with user-friendly messages
        if (error.response?.status === 413) {
          const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
          throw new Error(`Przesyłane pliki są za duże dla serwera (${totalSizeMB}MB).\n\nProponowane rozwiązania:\n• Podziel pliki na mniejsze grupy (np. 10-15 plików na raz)\n• Zmniejsz rozmiar obrazów przed przesłaniem\n• Usuń niektóre pliki z obecnego wyboru\n\nMaksymalny rozmiar dla jednej operacji wynosi około 50MB.`);
        }
        
        // Re-throw other errors as-is
        throw error;
      }
    }
  })
} 