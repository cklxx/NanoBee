import { JSX, splitProps } from "solid-js";
import { cx } from "../../utils/cx";

export function Card(props: JSX.IntrinsicElements["div"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <div class={cx("card", local.class)} {...rest} />;
}

export function CardHeader(props: JSX.IntrinsicElements["div"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <div class={cx("mb-3", local.class)} {...rest} />;
}

export function CardTitle(props: JSX.IntrinsicElements["h3"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <h3 class={cx("text-lg font-semibold", local.class)} {...rest} />;
}

export function CardDescription(props: JSX.IntrinsicElements["p"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <p class={cx("text-sm text-slate-600", local.class)} {...rest} />;
}

export function CardContent(props: JSX.IntrinsicElements["div"]) {
  const [local, rest] = splitProps(props, ["class"]);
  return <div class={cx("space-y-2", local.class)} {...rest} />;
}
