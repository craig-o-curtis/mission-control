<script lang="ts">
  import { onMount } from "svelte";
  import { Temporal } from "@js-temporal/polyfill";
  import "../app.css";

  let { children } = $props();

  let stardate = $state("");

  function calcStardate(): string {
    const now = Temporal.Now.plainDateISO();
    const year = now.year;
    const dayOfYear = now.dayOfYear;
    const sd = (year - 2323) * 1000 + (dayOfYear / 365) * 1000;
    return sd.toFixed(1);
  }

  onMount(() => {
    stardate = calcStardate();
    const timer = setInterval(() => (stardate = calcStardate()), 1000);
    return () => clearInterval(timer);
  });
</script>

<div class="min-h-screen bg-black">
  <header
    class="flex items-center gap-3 border-b-4 border-lcars-orange bg-lcars-bg px-6 py-4"
  >
    <a
      href="./"
      class="lcars-curve-left bg-lcars-orange px-8 py-3 transition hover:brightness-110"
    >
      <span class="text-xl font-bold tracking-widest text-black"
        >MISSION CONTROL</span
      >
    </a>
    <div class="lcars-curve-right bg-lcars-blue px-6 py-2">
      <span class="text-sm tracking-wider text-black">STARSHIP CONSOLE</span>
    </div>
    <div class="ml-auto flex items-center gap-3">
      <div class="lcars-pill bg-lcars-panel px-4 py-1.5">
        <span class="text-sm font-bold tracking-wider text-lcars-yellow"
          >STARDATE {stardate}</span
        >
      </div>
      <div class="flex gap-2">
        <div class="h-4 w-16 rounded-full bg-lcars-purple"></div>
        <div class="h-4 w-10 rounded-full bg-lcars-yellow"></div>
        <div class="h-4 w-12 rounded-full bg-lcars-teal"></div>
      </div>
    </div>
  </header>
  <main class="p-6">
    {@render children()}
  </main>
</div>
