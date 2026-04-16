import { Image } from '../../hooks/shared/images'

interface ImageGalleryProps {
  images: Image[]
  onImageSelect: (imageUrl: string) => void
}

export default function ImageGallery({ images, onImageSelect }: ImageGalleryProps) {
  if (images.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🖼️</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Brak obrazów</h3>
        <p className="text-gray-500">Przesłane obrazy pojawią się tutaj</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {images.map((image) => (
        <div
          key={image.id}
          className="group relative aspect-square overflow-hidden rounded-lg bg-gray-100 cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all"
          onClick={() => onImageSelect(image.url)}
        >
          <img
            src={image.url}
            alt={image.filename || 'Obraz'}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            loading="lazy"
          />
          
          {/* Overlay na hover */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <div className="bg-white bg-opacity-90 rounded-full p-2">
                <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </div>
            </div>
          </div>
          
          {/* Info o pliku */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/70 to-transparent p-2 translate-y-full group-hover:translate-y-0 transition-transform duration-200">
            <p className="text-white text-xs font-medium truncate">
              {image.filename || 'Nieznana nazwa'}
            </p>
            <p className="text-white/70 text-xs">
              {formatFileSize(image.size)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
} 