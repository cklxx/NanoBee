import type { JSX } from "solid-js";
import { splitProps } from "solid-js";
import { cx } from "../../utils/cx";

export function Label(props: JSX.IntrinsicElements["label"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <label class={cx("text-sm font-medium text-slate-700", local.class)} {...rest} />;
}
