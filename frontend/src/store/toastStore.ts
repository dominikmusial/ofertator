import { create } from 'zustand'
import { ReactNode } from 'react'

interface Toast {
  id: string
  message: string | ReactNode
  type: 'success' | 'error' | 'info'
}

interface State {
  toasts: Toast[]
  addToast: (msg: string | ReactNode, type: 'success' | 'error' | 'info', duration?: number) => string
  removeToast: (id: string) => void
  updateToast: (id: string, message: string | ReactNode, type?: 'success' | 'error' | 'info') => void
}

export const useToastStore = create<State>((set) => ({
  toasts: [],
  addToast: (message, type, duration = 4000) => {
    const id = Math.random().toString(36)
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }))
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) }))
    }, duration)
    return id  // Return the ID so it can be used for updates
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) })),
  updateToast: (id, message, type) => {
    set((s) => ({
      toasts: s.toasts.map(t => 
        t.id === id 
          ? { ...t, message, ...(type ? { type } : {}) }
          : t
      )
    }))
  },
})) 