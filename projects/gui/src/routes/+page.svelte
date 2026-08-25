<script lang="ts">
  import { resolve } from "$app/paths";

  const cards = [
    {
      href: resolve(`missions`),
      title: "Mission Control",
      desc: "Browse, add, edit and reset the seeded mission collection.",
      color: "border-lcars-orange",
    },
    {
      href: resolve(`checklists`),
      title: "REPORT STATUS",
      desc: "Log in (JWT) and manage mission checklists, backed by Postgres.",
      color: "border-lcars-blue",
    },
  ];
</script>

<section class="mx-auto max-w-4xl p-8">
  <div class="mb-8 flex items-end gap-4">
    <div class="lcars-curve-left bg-lcars-teal px-6 py-3">
      <h1 class="text-2xl font-bold tracking-widest text-black">FLEET RANK</h1>
    </div>
    <div class="lcars-curve-right bg-lcars-purple px-4 py-2">
      <span class="text-sm tracking-wider text-black">Ensign</span>
    </div>
  </div>

  <div class="mt-4 mb-8 h-2 w-full rounded-full bg-lcars-panel">
    <div class="h-2 w-2/3 rounded-full bg-lcars-teal"></div>
  </div>

  <div class="grid gap-6 sm:grid-cols-2">
    {#each cards as card}
      <a
        href={card.href}
        class="lcars-card {card.color} block bg-lcars-panel transition-all hover:brightness-125"
      >
        <h2 class="text-xl font-bold text-lcars-cream">{card.title}</h2>
        <p class="mt-2 text-sm text-gray-400">{card.desc}</p>
        <div class="mt-4 flex items-center gap-2">
          <div class="h-2 w-8 rounded-full bg-lcars-orange"></div>
          <div class="h-2 w-12 rounded-full bg-lcars-blue"></div>
          <span class="ml-auto text-xs tracking-wider text-lcars-yellow"
            >ACCESS →</span
          >
        </div>
      </a>
    {/each}
  </div>

  <div class="mt-12 flex gap-2">
    <div class="h-3 w-24 rounded-full bg-lcars-orange"></div>
    <div class="h-3 w-16 rounded-full bg-lcars-purple"></div>
    <div class="h-3 w-20 rounded-full bg-lcars-blue"></div>
    <div class="h-3 w-10 rounded-full bg-lcars-teal"></div>
  </div>
</section>
