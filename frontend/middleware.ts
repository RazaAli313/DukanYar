import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const SHOP_PREFIXES = ['/app', '/record', '/khata', '/maal', '/hisaab']

function isShopPath(path: string) {
  return SHOP_PREFIXES.some((p) => path === p || path.startsWith(p + '/'))
}

export async function middleware(request: NextRequest) {
  const response = NextResponse.next({ request: { headers: request.headers } })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          )
        },
      },
    },
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()
  const path = request.nextUrl.pathname
  const protectedPath = isShopPath(path) || path.startsWith('/admin')

  if (!user && protectedPath) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (user) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('role_name')
      .eq('id', user.id)
      .single()

    if (path.startsWith('/admin') && profile?.role_name !== 'admin') {
      return NextResponse.redirect(new URL('/app', request.url))
    }
    if (isShopPath(path) && profile?.role_name === 'admin') {
      return NextResponse.redirect(new URL('/admin', request.url))
    }
  }

  return response
}

export const config = {
  matcher: [
    '/app/:path*',
    '/record/:path*',
    '/khata/:path*',
    '/maal/:path*',
    '/hisaab/:path*',
    '/admin/:path*',
  ],
}
