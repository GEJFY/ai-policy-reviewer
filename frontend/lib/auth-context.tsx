'use client'

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  user_id: string
  username: string
  display_name: string
  roles: string[]
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, display_name: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  const clearAuth = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }, [])

  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) return null

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!res.ok) return null

      const data = await res.json()
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      return data.access_token
    } catch {
      return null
    }
  }, [])

  const fetchUser = useCallback(async (token: string): Promise<User | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.status === 401) {
        const newToken = await refreshAccessToken()
        if (!newToken) return null
        const retry = await fetch(`${API_BASE}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${newToken}` },
        })
        if (!retry.ok) return null
        return retry.json()
      }
      if (!res.ok) return null
      return res.json()
    } catch {
      return null
    }
  }, [refreshAccessToken])

  useEffect(() => {
    async function init() {
      const token = localStorage.getItem('access_token')
      if (token) {
        const userData = await fetchUser(token)
        if (userData) {
          setUser(userData)
        } else {
          clearAuth()
        }
      }
      setIsLoading(false)
    }
    init()
  }, [fetchUser, clearAuth])

  const login = async (username: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'ログインに失敗しました')
    }

    const data = await res.json()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)

    const userData = await fetchUser(data.access_token)
    if (userData) {
      setUser(userData)
    }
  }

  const register = async (username: string, password: string, display_name: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, display_name }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '登録に失敗しました')
    }
  }

  const logout = () => {
    const token = localStorage.getItem('access_token')
    if (token) {
      fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {})
    }
    clearAuth()
    router.push('/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
