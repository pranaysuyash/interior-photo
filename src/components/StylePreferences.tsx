import React from 'react';
import { motion } from 'framer-motion';
import { Palette, Sparkles, Type } from 'lucide-react';

interface StylePreferencesProps {
  vibe: string;
  setVibe: (vibe: string) => void;
  colors: string;
  setColors: (colors: string) => void;
  description: string;
  setDescription: (description: string) => void;
}

const vibeOptions = [
  { value: 'modern', label: 'Modern', emoji: '✨' },
  { value: 'minimalist', label: 'Minimalist', emoji: '⚪' },
  { value: 'cozy', label: 'Cozy', emoji: '🛋️' },
  { value: 'industrial', label: 'Industrial', emoji: '🏭' },
  { value: 'bohemian', label: 'Bohemian', emoji: '🌿' },
  { value: 'scandinavian', label: 'Scandinavian', emoji: '🌲' },
  { value: 'luxurious', label: 'Luxurious', emoji: '💎' },
  { value: 'rustic', label: 'Rustic', emoji: '🪵' },
];

const colorOptions = [
  { value: 'neutral', label: 'Neutral Tones', color: 'bg-gradient-to-r from-gray-200 to-gray-300' },
  { value: 'warm', label: 'Warm Colors', color: 'bg-gradient-to-r from-orange-300 to-red-300' },
  { value: 'cool', label: 'Cool Colors', color: 'bg-gradient-to-r from-blue-300 to-cyan-300' },
  { value: 'earthy', label: 'Earthy Tones', color: 'bg-gradient-to-r from-amber-600 to-green-700' },
  { value: 'pastel', label: 'Pastel', color: 'bg-gradient-to-r from-pink-200 to-purple-200' },
  { value: 'bold', label: 'Bold & Vibrant', color: 'bg-gradient-to-r from-purple-500 to-pink-500' },
];

const StylePreferences: React.FC<StylePreferencesProps> = ({
  vibe,
  setVibe,
  colors,
  setColors,
  description,
  setDescription,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="space-y-6"
    >
      {/* Vibe Selection */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary-600" />
          <label className="block text-sm font-semibold text-gray-700">
            Choose Your Vibe
          </label>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {vibeOptions.map((option) => (
            <motion.button
              key={option.value}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setVibe(option.value)}
              className={`
                px-4 py-3 rounded-xl font-medium text-sm transition-all
                ${vibe === option.value
                  ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg shadow-primary-500/30'
                  : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm'
                }
              `}
            >
              <span className="mr-2">{option.emoji}</span>
              {option.label}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Color Palette Selection */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Palette className="w-5 h-5 text-primary-600" />
          <label className="block text-sm font-semibold text-gray-700">
            Color Palette
          </label>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {colorOptions.map((option) => (
            <motion.button
              key={option.value}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setColors(option.value)}
              className={`
                relative px-4 py-3 rounded-xl font-medium text-sm transition-all overflow-hidden
                ${colors === option.value
                  ? 'ring-2 ring-primary-500 ring-offset-2 shadow-lg'
                  : 'ring-1 ring-gray-200 hover:ring-gray-300'
                }
              `}
            >
              <div className={`absolute inset-0 ${option.color} opacity-20`}></div>
              <span className="relative z-10 text-gray-700">{option.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Additional Description */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Type className="w-5 h-5 text-primary-600" />
          <label className="block text-sm font-semibold text-gray-700">
            Additional Details (Optional)
          </label>
        </div>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="E.g., Add more plants, include a reading nook, make it feel spacious..."
          className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all resize-none"
          rows={4}
        />
      </div>
    </motion.div>
  );
};

export default StylePreferences;
