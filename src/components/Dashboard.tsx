import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, Clock, Sparkles, CreditCard, LogOut } from 'lucide-react';
import { apiService } from '../services/api';

interface Transformation {
  id: string;
  original_image_url: string;
  transformed_image_url: string;
  vibe: string;
  colors: string;
  status: string;
  created_at: string;
}

interface User {
  email: string;
  name: string;
  credits: number;
  subscription_tier: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [userData, historyData] = await Promise.all([
        apiService.getCurrentUser(),
        apiService.getTransformationHistory()
      ]);

      setUser(userData);
      setTransformations(historyData.transformations);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-purple-100 to-pink-100 flex items-center justify-center">
        <div className="text-center">
          <Sparkles className="w-16 h-16 text-purple-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-purple-100 to-pink-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-purple-600" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Interior AI
              </h1>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">Welcome back,</p>
                <p className="font-semibold">{user?.name || user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Available Credits</p>
                <p className="text-3xl font-bold text-purple-600">{user?.credits || 0}</p>
              </div>
              <CreditCard className="w-12 h-12 text-purple-200" />
            </div>
            <button className="mt-4 w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm">
              Buy More Credits
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Subscription</p>
                <p className="text-3xl font-bold text-gray-900">{user?.subscription_tier || 'Free'}</p>
              </div>
              <Sparkles className="w-12 h-12 text-pink-200" />
            </div>
            <button className="mt-4 w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all text-sm">
              Upgrade Plan
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Transformations</p>
                <p className="text-3xl font-bold text-gray-900">{transformations.length}</p>
              </div>
              <Clock className="w-12 h-12 text-purple-200" />
            </div>
            <button
              onClick={() => window.location.href = '/'}
              className="mt-4 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
            >
              Create New
            </button>
          </motion.div>
        </div>

        {/* Transformation History */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-6">Your Transformations</h2>

          {transformations.length === 0 ? (
            <div className="text-center py-12">
              <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No transformations yet</p>
              <button
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
              >
                Create Your First Transformation
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {transformations.map((transformation, index) => (
                <motion.div
                  key={transformation.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gray-50 rounded-lg overflow-hidden hover:shadow-xl transition-all"
                >
                  <div className="relative aspect-video">
                    <img
                      src={transformation.transformed_image_url || transformation.original_image_url}
                      alt={`${transformation.vibe} transformation`}
                      className="w-full h-full object-cover"
                    />
                    {transformation.status === 'PROCESSING' && (
                      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                        <div className="text-white text-center">
                          <Sparkles className="w-8 h-8 animate-spin mx-auto mb-2" />
                          <p className="text-sm">Processing...</p>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold text-gray-900 capitalize">{transformation.vibe}</p>
                        <p className="text-sm text-gray-500 capitalize">{transformation.colors} colors</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        transformation.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                        transformation.status === 'PROCESSING' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {transformation.status}
                      </span>
                    </div>

                    <p className="text-xs text-gray-400 mb-3">
                      {new Date(transformation.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </p>

                    {transformation.status === 'COMPLETED' && transformation.transformed_image_url && (
                      <button
                        onClick={() => handleDownload(
                          transformation.transformed_image_url,
                          `interior-ai-${transformation.id}.jpg`
                        )}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
