import type { JSX } from "solid-js";
import { splitProps } from "solid-js";
import { cx } from "../../utils/cx";

export function Badge(props: JSX.IntrinsicElements["span"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return (
    <span
      class={cx(
        "inline-flex items-center rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700",
        local.class,
      )}
      {...rest}
    />
  );
}
