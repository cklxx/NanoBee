import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cx(...classes: any[]) {
  return twMerge(clsx(classes));
}
