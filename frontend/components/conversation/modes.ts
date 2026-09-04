import type { LucideIcon } from "lucide-react";
import { ShoppingCart, Users, ReceiptText, Sparkles } from "lucide-react";
import type { Mode } from "@/lib/chatApi";

export type { Mode };

interface ModeConfig {
  title: string;
  hint: string;
  placeholder: string;
  icon: LucideIcon;
  /** Sale runs a structured parse + confirmation card. Others are conversational. */
  confirms: boolean;
}

export const MODES: Record<Mode, ModeConfig> = {
  sale: {
    title: "Naya Sale",
    hint: "Kya becha? Item, ginti aur total batayein.",
    placeholder: "jaise: do coke aur aik chips, chaar so",
    icon: ShoppingCart,
    confirms: true,
  },
  udhaar: {
    title: "Udhaar",
    hint: "Kis ka khata, kitna udhaar ya wapsi?",
    placeholder: "jaise: khata 12 pe 500 udhaar",
    icon: Users,
    confirms: false,
  },
  kharcha: {
    title: "Kharcha",
    hint: "Kis cheez ka kharcha aur kitna?",
    placeholder: "jaise: bijli ka bill teen hazaar",
    icon: ReceiptText,
    confirms: false,
  },
  ask: {
    title: "Poocho",
    hint: "Dukaan ke baare mein kuch bhi poochein.",
    placeholder: "jaise: aaj kitni sale hui?",
    icon: Sparkles,
    confirms: false,
  },
};

export function isMode(v: string): v is Mode {
  return v === "sale" || v === "udhaar" || v === "kharcha" || v === "ask";
}
