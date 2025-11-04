import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, Sparkles, Download, RefreshCw, Home } from 'lucide-react';
import ImageUpload from './components/ImageUpload';
import StylePreferences from './components/StylePreferences';
import ReferenceImages from './components/ReferenceImages';
import BeforeAfterSlider from './components/BeforeAfterSlider';

function App() {
  const [originalImage, setOriginalImage] = useState<string>('');
  const [transformedImage, setTransformedImage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [vibe, setVibe] = useState('modern');
  const [colors, setColors] = useState('neutral');
  const [description, setDescription] = useState('');
  const [referenceImages, setReferenceImages] = useState<string[]>([]);

  const handleTransform = async () => {
    if (!originalImage) return;

    setIsProcessing(true);

    // Simulate AI processing (replace with actual API call)
    await new Promise(resolve => setTimeout(resolve, 3000));

    // For demo purposes, use the original image as transformed
    // In production, this would be the AI-generated result
    setTransformedImage(originalImage);
    setIsProcessing(false);
  };

  const handleReset = () => {
    setOriginalImage('');
    setTransformedImage('');
    setVibe('modern');
    setColors('neutral');
    setDescription('');
    setReferenceImages([]);
  };

  const handleDownload = () => {
    if (!transformedImage) return;

    const link = document.createElement('a');
    link.href = transformedImage;
    link.download = 'transformed-interior.png';
    link.click();
  };

  const handleReferenceImageAdd = (_file: File, preview: string) => {
    setReferenceImages(prev => [...prev, preview]);
  };

  const handleReferenceImageRemove = (index: number) => {
    setReferenceImages(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            >
              <Home className="w-12 h-12 text-white" />
            </motion.div>
            <h1 className="text-5xl font-bold text-white">
              Interior AI
            </h1>
          </div>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Transform your space with AI-powered interior design
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Input Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <div className="bg-white rounded-2xl shadow-2xl p-6 space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <Wand2 className="w-6 h-6 text-primary-600" />
                Design Your Space
              </h2>

              {/* Upload Original Image */}
              <ImageUpload
                onImageSelect={(_file, preview) => {
                  setOriginalImage(preview);
                  setTransformedImage('');
                }}
                currentImage={originalImage}
                label="Upload Your Room Photo"
                description="Upload a photo of the room you want to transform"
              />

              {/* Style Preferences */}
              <StylePreferences
                vibe={vibe}
                setVibe={setVibe}
                colors={colors}
                setColors={setColors}
                description={description}
                setDescription={setDescription}
              />

              {/* Reference Images */}
              <ReferenceImages
                referenceImages={referenceImages}
                onReferenceImageAdd={handleReferenceImageAdd}
                onReferenceImageRemove={handleReferenceImageRemove}
              />

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleTransform}
                  disabled={!originalImage || isProcessing}
                  className={`
                    flex-1 py-4 px-6 rounded-xl font-semibold text-white
                    transition-all duration-300 flex items-center justify-center gap-2
                    ${!originalImage || isProcessing
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-gradient-to-r from-primary-500 to-accent-500 hover:shadow-xl hover:shadow-primary-500/30'
                    }
                  `}
                >
                  {isProcessing ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      >
                        <RefreshCw className="w-5 h-5" />
                      </motion.div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Transform Space
                    </>
                  )}
                </motion.button>

                {(originalImage || transformedImage) && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleReset}
                    className="py-4 px-6 rounded-xl font-semibold bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all"
                  >
                    <RefreshCw className="w-5 h-5" />
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>

          {/* Right Panel - Preview Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="space-y-6"
          >
            <div className="bg-white rounded-2xl shadow-2xl p-6 h-full">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-primary-600" />
                Preview
              </h2>

              <AnimatePresence mode="wait">
                {transformedImage && originalImage ? (
                  <div key="slider" className="space-y-4">
                    <div className="aspect-video bg-gray-100 rounded-2xl overflow-hidden">
                      <BeforeAfterSlider
                        beforeImage={originalImage}
                        afterImage={transformedImage}
                      />
                    </div>

                    <motion.button
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleDownload}
                      className="w-full py-3 px-6 rounded-xl font-semibold bg-green-500 text-white hover:bg-green-600 transition-all flex items-center justify-center gap-2 shadow-lg"
                    >
                      <Download className="w-5 h-5" />
                      Download Result
                    </motion.button>
                  </div>
                ) : originalImage && isProcessing ? (
                  <motion.div
                    key="processing"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="aspect-video bg-gradient-to-br from-primary-100 to-accent-100 rounded-2xl flex flex-col items-center justify-center gap-4"
                  >
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        rotate: [0, 180, 360],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                    >
                      <Sparkles className="w-16 h-16 text-primary-600" />
                    </motion.div>
                    <p className="text-lg font-semibold text-gray-700">
                      Transforming your space...
                    </p>
                    <div className="w-64 h-2 bg-white rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-primary-500 to-accent-500"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{ duration: 3, ease: 'easeInOut' }}
                      />
                    </div>
                  </motion.div>
                ) : originalImage ? (
                  <motion.div
                    key="original"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="aspect-video bg-gray-100 rounded-2xl overflow-hidden"
                  >
                    <img
                      src={originalImage}
                      alt="Original"
                      className="w-full h-full object-cover"
                    />
                  </motion.div>
                ) : (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="aspect-video bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl flex flex-col items-center justify-center gap-4 border-2 border-dashed border-gray-300"
                  >
                    <motion.div
                      animate={{ y: [0, -10, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                    >
                      <Home className="w-20 h-20 text-gray-300" />
                    </motion.div>
                    <p className="text-gray-400 font-medium">
                      Upload an image to get started
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Info Cards */}
              <div className="grid grid-cols-2 gap-4 mt-6">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  className="bg-gradient-to-br from-primary-50 to-primary-100 p-4 rounded-xl"
                >
                  <div className="text-2xl font-bold text-primary-700">
                    {vibe.charAt(0).toUpperCase() + vibe.slice(1)}
                  </div>
                  <div className="text-xs text-primary-600 font-medium">Selected Vibe</div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.05 }}
                  className="bg-gradient-to-br from-accent-50 to-accent-100 p-4 rounded-xl"
                >
                  <div className="text-2xl font-bold text-accent-700">
                    {colors.charAt(0).toUpperCase() + colors.slice(1)}
                  </div>
                  <div className="text-xs text-accent-600 font-medium">Color Palette</div>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-12 text-white/80"
        >
          <p className="text-sm">
            Powered by AI • Transform your interior design dreams into reality
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export default App;
