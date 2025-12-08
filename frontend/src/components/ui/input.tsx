import type { JSX } from "solid-js";
import { splitProps } from "solid-js";
import { cx } from "../../utils/cx";

export function Input(props: JSX.IntrinsicElements["input"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return (
    <input
      class={cx(
        "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none",
        local.class,
      )}
      {...rest}
    />
  );
}
