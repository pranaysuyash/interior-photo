import React from 'react';
import { motion } from 'framer-motion';
import { Images, Info } from 'lucide-react';
import ImageUpload from './ImageUpload';

interface ReferenceImagesProps {
  referenceImages: string[];
  onReferenceImageAdd: (file: File, preview: string) => void;
  onReferenceImageRemove: (index: number) => void;
}

const ReferenceImages: React.FC<ReferenceImagesProps> = ({
  referenceImages,
  onReferenceImageAdd,
  onReferenceImageRemove,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="space-y-4"
    >
      <div className="flex items-start gap-3">
        <Images className="w-5 h-5 text-primary-600 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-700">
            Reference Images
          </h3>
          <div className="flex items-start gap-2 mt-1">
            <Info className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-500">
              Upload inspiration images of furniture, colors, or objects you'd like to incorporate
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {referenceImages.map((image, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="relative group"
          >
            <img
              src={image}
              alt={`Reference ${index + 1}`}
              className="w-full h-32 object-cover rounded-lg shadow-md"
            />
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => onReferenceImageRemove(index)}
              className="absolute -top-2 -right-2 bg-red-500 text-white w-6 h-6 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
            >
              ×
            </motion.button>
          </motion.div>
        ))}

        {referenceImages.length < 6 && (
          <div className="h-32">
            <ImageUpload
              onImageSelect={(file, preview) => {
                if (preview) onReferenceImageAdd(file, preview);
              }}
              label=""
              description=""
              currentImage=""
            />
          </div>
        )}
      </div>

      {referenceImages.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-4">
          No reference images added yet
        </p>
      )}
    </motion.div>
  );
};

export default ReferenceImages;
