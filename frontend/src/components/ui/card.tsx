import { splitProps, type ComponentProps } from "solid-js";
import { cn } from "@/lib/utils";

export function Card(props: ComponentProps<"div">) {
  const [local, rest] = splitProps(props, ["class", "children"]);
  return (
    <div class={cn("rounded-xl border bg-white text-slate-900 shadow", local.class)} {...rest}>
      {local.children}
    </div>
  );
}

export function CardHeader(props: ComponentProps<"div">) {
  const [local, rest] = splitProps(props, ["class", "children"]);
  return (
    <div class={cn("flex flex-col space-y-1.5 p-6", local.class)} {...rest}>
      {local.children}
    </div>
  );
}

export function CardTitle(props: ComponentProps<"h3">) {
  const [local, rest] = splitProps(props, ["class", "children"]);
  return (
    <h3 class={cn("text-2xl font-semibold leading-none tracking-tight", local.class)} {...rest}>
      {local.children}
    </h3>
  );
}

export function CardDescription(props: ComponentProps<"p">) {
  const [local, rest] = splitProps(props, ["class", "children"]);
  return (
    <p class={cn("text-sm text-slate-500", local.class)} {...rest}>
      {local.children}
    </p>
  );
}

export function CardContent(props: ComponentProps<"div">) {
  const [local, rest] = splitProps(props, ["class", "children"]);
  return (
    <div class={cn("p-6 pt-0", local.class)} {...rest}>
      {local.children}
    </div>
  );
}
