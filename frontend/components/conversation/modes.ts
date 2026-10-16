import type { LucideIcon } from "lucide-react";
import { ShoppingCart, Users, ReceiptText, Sparkles, Package } from "lucide-react";
import type { Mode } from "@/lib/chatApi";

export type { Mode };

interface ModeConfig {
  title: string;
  hint: string;
  placeholder: string;
  icon: LucideIcon;
}

export const MODES: Record<Mode, ModeConfig> = {
  sale: {
    title: "Naya Sale",
    hint: "Kya becha? Item, ginti aur total batayein.",
    placeholder: "jaise: do coke aur aik chips, chaar so",
    icon: ShoppingCart,
  },
  udhaar: {
    title: "Udhaar",
    hint: "Kis ka khata, kitna udhaar ya wapsi?",
    placeholder: "jaise: khata 12 pe 500 udhaar",
    icon: Users,
  },
  kharcha: {
    title: "Kharcha",
    hint: "Kis cheez ka kharcha aur kitna?",
    placeholder: "jaise: bijli ka bill teen hazaar",
    icon: ReceiptText,
  },
  ask: {
    title: "Poocho",
    hint: "Dukaan ke baare mein kuch bhi poochein.",
    placeholder: "jaise: aaj kitni sale hui?",
    icon: Sparkles,
  },
  maal: {
    title: "Maal",
    hint: "Stock update karein ya naya maal add karein.",
    placeholder: "jaise: coke ka stock 50 karo",
    icon: Package,
  },
};

export function isMode(v: string): v is Mode {
  return ["sale", "udhaar", "kharcha", "ask", "maal"].includes(v);
}
