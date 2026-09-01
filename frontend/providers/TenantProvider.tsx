'use client'

import React, { createContext, useContext } from 'react'

export interface UserContext {
  id: string
  role: 'admin' | 'shopkeeper'
  full_name: string | null
}

export interface ShopContext {
  id: string
  name: string
}

interface TenantContextType {
  currentUser: UserContext | null
  currentShop: ShopContext | null
}

const TenantContext = createContext<TenantContextType>({
  currentUser: null,
  currentShop: null,
})

export const TenantProvider = ({
  children,
  value,
}: {
  children: React.ReactNode
  value: TenantContextType
}) => (
  <TenantContext.Provider value={value}>{children}</TenantContext.Provider>
)

export const useTenant = () => useContext(TenantContext)