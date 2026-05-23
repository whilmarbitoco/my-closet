'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Shirt, Sparkles, Download, ChevronLeft, Plus, X } from 'lucide-react'
import axios from 'axios'

const API = 'http://localhost:8000'

type Step = 'upload-user' | 'upload-clothes' | 'select' | 'result'
type Category = 'top' | 'bottom' | 'dress' | 'jacket'

interface ClothingItem {
  id: string
  category: Category
  original: string
  no_background?: string
}

export default function Home() {
  const [step, setStep] = useState<Step>('upload-user')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [userPhoto, setUserPhoto] = useState<string | null>(null)
  const [wardrobe, setWardrobe] = useState<ClothingItem[]>([])
  const [selectedCategory, setSelectedCategory] = useState<Category>('top')
  const [selectedClothing, setSelectedClothing] = useState<string | null>(null)
  const [resultUrl, setResultUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Create session on mount
  const createSession = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/api/session/create`)
      setSessionId(res.data.session_id)
    } catch {
      setError('Failed to create session')
    }
  }, [])

  // Upload user photo
  const handleUserPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !sessionId) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await axios.post(`${API}/api/user/upload?session_id=${sessionId}`, formData)
      setUserPhoto(URL.createObjectURL(file))
      setStep('upload-clothes')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  // Upload clothing
  const handleClothingUpload = async (e: React.ChangeEvent<HTMLInputElement>, category: Category) => {
    const file = e.target.files?.[0]
    if (!file || !sessionId) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(
        `${API}/api/wardrobe/upload?session_id=${sessionId}&category=${category}`,
        formData
      )
      // Refresh wardrobe
      const res = await axios.get(`${API}/api/wardrobe/${sessionId}`)
      setWardrobe(res.data.wardrobe)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  // Generate try-on
  const handleTryOn = async () => {
    if (!sessionId || !selectedClothing) return

    setLoading(true)
    setError(null)

    try {
      const res = await axios.post(`${API}/api/try-on`, {
        session_id: sessionId,
        clothing_id: selectedClothing,
        category: selectedCategory,
      })
      setResultUrl(`${API}${res.data.image_url}`)
      setStep('result')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Try-on failed')
    } finally {
      setLoading(false)
    }
  }

  const filteredWardrobe = wardrobe.filter(item => item.category === selectedCategory)

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-lg mx-auto flex items-center justify-between">
          {step !== 'upload-user' && (
            <button
              onClick={() => {
                if (step === 'upload-clothes') setStep('upload-user')
                else if (step === 'select') setStep('upload-clothes')
                else if (step === 'result') setStep('select')
              }}
              className="p-2 rounded-full hover:bg-black/5 transition"
            >
              <ChevronLeft size={20} />
            </button>
          )}
          <h1 className="text-lg font-semibold tracking-tight">My Closet</h1>
          <div className="w-8" />
        </div>
      </header>

      {/* Content */}
      <div className="pt-20 pb-12 px-6">
        <div className="max-w-lg mx-auto">
          <AnimatePresence mode="wait">
            {/* Step 1: Upload User Photo */}
            {step === 'upload-user' && (
              <motion.div
                key="upload-user"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-8"
              >
                <div className="text-center space-y-3">
                  <h2 className="text-2xl font-bold">Upload Your Photo</h2>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Take or upload a full-body photo for the best results
                  </p>
                </div>

                <label className="upload-zone block">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleUserPhotoUpload}
                    className="hidden"
                    disabled={loading}
                  />
                  <div className="space-y-4">
                    <div className="w-16 h-16 mx-auto rounded-full flex items-center justify-center" style={{ background: 'rgba(201,168,124,0.1)' }}>
                      <Upload size={28} style={{ color: 'var(--accent)' }} />
                    </div>
                    <div>
                      <p className="font-medium">Tap to upload</p>
                      <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                        JPG or PNG • Max 10MB
                      </p>
                    </div>
                  </div>
                </label>

                {loading && (
                  <div className="text-center py-4">
                    <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
                    <p className="text-sm mt-3" style={{ color: 'var(--text-secondary)' }}>Processing...</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 2: Upload Clothes */}
            {step === 'upload-clothes' && (
              <motion.div
                key="upload-clothes"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold">Build Your Wardrobe</h2>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Upload clothing items to try on
                  </p>
                </div>

                {userPhoto && (
                  <div className="w-24 h-24 mx-auto rounded-full overflow-hidden border-2" style={{ borderColor: 'var(--accent)' }}>
                    <img src={userPhoto} alt="You" className="w-full h-full object-cover" />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {(['top', 'bottom', 'dress', 'jacket'] as Category[]).map(cat => (
                    <label key={cat} className="upload-zone !p-4 cursor-pointer">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleClothingUpload(e, cat)}
                        className="hidden"
                        disabled={loading}
                      />
                      <div className="space-y-2">
                        <Shirt size={24} className="mx-auto" style={{ color: 'var(--accent)' }} />
                        <p className="text-sm font-medium capitalize">{cat}</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                          {wardrobe.filter(i => i.category === cat).length} items
                        </p>
                      </div>
                    </label>
                  ))}
                </div>

                {wardrobe.length > 0 && (
                  <button
                    onClick={() => setStep('select')}
                    className="btn-primary w-full"
                  >
                    Continue to Try-On
                  </button>
                )}
              </motion.div>
            )}

            {/* Step 3: Select & Try On */}
            {step === 'select' && (
              <motion.div
                key="select"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold">Try It On</h2>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Select a clothing item to preview
                  </p>
                </div>

                {/* Category Tabs */}
                <div className="flex gap-2 justify-center">
                  {(['top', 'bottom', 'dress', 'jacket'] as Category[]).map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition capitalize ${
                        selectedCategory === cat
                          ? 'text-white'
                          : 'bg-white border'
                      }`}
                      style={{
                        background: selectedCategory === cat ? 'var(--accent)' : undefined,
                        borderColor: 'var(--border)',
                      }}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Clothing Grid */}
                {filteredWardrobe.length > 0 ? (
                  <div className="grid grid-cols-3 gap-3">
                    {filteredWardrobe.map(item => (
                      <button
                        key={item.id}
                        onClick={() => setSelectedClothing(item.id)}
                        className={`aspect-square rounded-xl overflow-hidden border-2 transition ${
                          selectedClothing === item.id ? 'border-[var(--accent)]' : 'border-transparent'
                        }`}
                        style={{ background: 'var(--bg-secondary)' }}
                      >
                        <div className="w-full h-full flex items-center justify-center">
                          <Shirt size={32} style={{ color: 'var(--text-secondary)' }} />
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8" style={{ color: 'var(--text-secondary)' }}>
                    <p>No {selectedCategory}s uploaded yet</p>
                    <button
                      onClick={() => setStep('upload-clothes')}
                      className="text-sm mt-2 underline"
                      style={{ color: 'var(--accent)' }}
                    >
                      Go back & upload
                    </button>
                  </div>
                )}

                {selectedClothing && (
                  <button
                    onClick={handleTryOn}
                    disabled={loading}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    <Sparkles size={18} />
                    {loading ? 'Generating...' : 'Generate Try-On'}
                  </button>
                )}

                {loading && (
                  <div className="text-center py-4">
                    <div className="w-8 h-8 border-2 rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
                    <p className="text-sm mt-3" style={{ color: 'var(--text-secondary)' }}>
                      Rendering your outfit...
                    </p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 4: Result */}
            {step === 'result' && resultUrl && (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold">Your Look</h2>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Here's how it looks on you
                  </p>
                </div>

                <div className="rounded-2xl overflow-hidden" style={{ boxShadow: 'var(--shadow)' }}>
                  <img
                    src={resultUrl}
                    alt="Try-on result"
                    className="w-full"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setResultUrl(null)
                      setStep('select')
                    }}
                    className="flex-1 py-3 rounded-xl font-medium border"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    Try Another
                  </button>
                  <a
                    href={resultUrl}
                    download
                    className="flex-1 py-3 rounded-xl font-medium text-center flex items-center justify-center gap-2"
                    style={{ background: 'var(--accent)', color: 'white' }}
                  >
                    <Download size={18} />
                    Save
                  </a>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="fixed bottom-6 left-6 right-6 max-w-lg mx-auto p-4 rounded-xl text-white text-sm"
              style={{ background: '#e74c3c' }}
            >
              {error}
              <button onClick={() => setError(null)} className="float-right">
                <X size={16} />
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </main>
  )
}
