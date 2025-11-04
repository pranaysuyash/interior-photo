# Interior AI - Transform Your Space

A beautiful and functional frontend application for AI-powered interior design transformation. Upload your room photos and get AI-generated redesigns based on your preferred style, colors, and vibe.

## ✨ Features

- **Beautiful UI/UX**: Modern, gradient-based design with smooth animations
- **Drag & Drop Upload**: Easy image upload with drag-and-drop functionality
- **Style Customization**: Choose from 8 different vibes (Modern, Minimalist, Cozy, Industrial, etc.)
- **Color Palettes**: Select from 6 curated color schemes
- **Reference Images**: Upload inspiration images for objects, colors, or furniture
- **Before/After Slider**: Interactive comparison slider to see transformations
- **Responsive Design**: Works beautifully on all screen sizes
- **Smooth Animations**: Powered by Framer Motion for delightful interactions

## 🎨 Design Highlights

- **Color Scheme**: Beautiful purple gradient background with modern UI elements
- **Animations**: Smooth transitions, hover effects, and loading states
- **Typography**: Clean, modern Inter font family
- **Components**: Reusable, well-structured React components

## 🚀 Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

### Development

Run the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

Create a production build:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## 🛠️ Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Framer Motion** - Animation library
- **Lucide React** - Beautiful icon set

## 📁 Project Structure

```
src/
├── components/
│   ├── BeforeAfterSlider.tsx    # Interactive before/after comparison
│   ├── ImageUpload.tsx          # Drag & drop image upload
│   ├── StylePreferences.tsx     # Vibe and color selection
│   └── ReferenceImages.tsx      # Reference image gallery
├── App.tsx                      # Main application component
├── main.tsx                     # Application entry point
└── index.css                    # Global styles and Tailwind imports
```

## 🎯 Usage

1. **Upload Your Room Photo**: Click or drag & drop an image of your room
2. **Choose Your Vibe**: Select from Modern, Minimalist, Cozy, Industrial, Bohemian, Scandinavian, Luxurious, or Rustic
3. **Select Color Palette**: Pick from Neutral, Warm, Cool, Earthy, Pastel, or Bold & Vibrant
4. **Add Details** (Optional): Describe specific requirements like "Add more plants" or "Include a reading nook"
5. **Upload References** (Optional): Add inspiration images for furniture, colors, or objects
6. **Transform**: Click the "Transform Space" button to generate your AI-redesigned room
7. **Compare**: Use the interactive slider to compare before and after
8. **Download**: Save your transformed image

## 🔮 Future Enhancements

- Backend API integration for actual AI image transformation
- Multiple transformation options per upload
- Save and share designs
- User accounts and design history
- 3D room visualization
- AR preview mode

## 📝 License

MIT

## 🙏 Acknowledgments

- Design inspiration from modern interior design platforms
- Icons by Lucide
- Fonts by Google Fonts
