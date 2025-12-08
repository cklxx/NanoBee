import { ComponentProps, splitProps } from "solid-js";
import { cx } from "../../utils/cx";

export function Button(props: ComponentProps<"button"> & { variant?: "default" | "outline" }) {
  const [local, rest] = splitProps(props, ["class", "variant"]);
  const variantClass = local.variant === "outline"
    ? "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50"
    : "bg-slate-900 text-white hover:bg-slate-800";
  return (
    <button
      class={cx(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60",
        variantClass,
        local.class,
      )}
      {...rest}
    />
  );
}
