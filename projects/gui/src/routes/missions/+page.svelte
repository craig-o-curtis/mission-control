<script lang="ts">
  import { onMount } from "svelte";
  import { missionsApi, type Mission, type MissionInput } from "#lib/api";

  let missions = $state<Mission[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(true);

  let editingId = $state<number | null>(null);
  let mission_name = $state("");
  let commander = $state("");
  let mission_type = $state("");
  let description = $state("");
  let phase = $state<string | null>(null);
  let priority = $state<number | null>(null);
  let launch_date = $state("");

  const PHASES = ["planning", "launch", "active", "complete", "archived"];

  function phaseClass(p: string | null): string {
    switch (p) {
      case "planning":
        return "bg-gray-600 text-white";
      case "launch":
        return "bg-lcars-yellow text-black";
      case "active":
        return "bg-lcars-teal text-black";
      case "complete":
        return "bg-green-600 text-white";
      case "archived":
        return "bg-gray-500 text-gray-200";
      default:
        return "bg-gray-700 text-gray-200";
    }
  }

  async function load() {
    loading = true;
    error = null;
    try {
      missions = await missionsApi.list();
    } catch (e) {
      error = (e as Error).message;
    } finally {
      loading = false;
    }
  }

  function startEdit(mission: Mission) {
    editingId = mission.id;
    mission_name = mission.mission_name;
    commander = mission.commander;
    mission_type = mission.mission_type;
    description = mission.description ?? "";
    phase = mission.phase;
    priority = mission.priority;
    launch_date = mission.launch_date ?? "";
  }

  function cancelEdit() {
    editingId = null;
    mission_name = "";
    commander = "";
    mission_type = "";
    description = "";
    phase = null;
    priority = null;
    launch_date = "";
  }

  async function submit(e: SubmitEvent) {
    e.preventDefault();
    error = null;
    const input: MissionInput = {
      mission_name,
      commander,
      mission_type,
      description: description || null,
      phase,
      priority,
      launch_date: launch_date || null,
    };
    try {
      if (editingId === null) {
        await missionsApi.create(input);
      } else {
        await missionsApi.update(editingId, input);
      }
      cancelEdit();
      await load();
    } catch (e) {
      error = (e as Error).message;
    }
  }

  async function remove(id: number) {
    error = null;
    try {
      await missionsApi.remove(id);
      missions = missions.filter((m) => m.id !== id);
    } catch (e) {
      error = (e as Error).message;
    }
  }

  async function reset() {
    error = null;
    try {
      await missionsApi.reset();
      await load();
    } catch (e) {
      error = (e as Error).message;
    }
  }

  onMount(load);
</script>

<section class="mx-auto max-w-5xl">
  <div class="mb-6 flex items-end gap-4">
    <div class="lcars-curve-left bg-lcars-orange px-6 py-3">
      <h1 class="text-xl font-bold tracking-widest text-black">MISSIONS</h1>
    </div>
    <div class="lcars-curve-right bg-lcars-blue px-4 py-2">
      <span class="text-sm tracking-wider text-black">MISSION DATABASE</span>
    </div>
    <button class="lcars-btn ml-auto bg-lcars-red text-black" onclick={reset}>
      Reset Data
    </button>
  </div>

  <div class="mb-6 h-1 w-full rounded-full bg-lcars-panel">
    <div class="h-1 w-1/3 rounded-full bg-lcars-teal"></div>
  </div>

  {#if error}
    <div
      class="lcars-curve-left mb-6 border-l-8 border-lcars-red bg-lcars-panel p-4"
    >
      <p class="text-lcars-red">{error}</p>
    </div>
  {/if}

  <div class="lcars-card mb-8 border-lcars-purple bg-lcars-panel">
    <form class="grid gap-3 sm:grid-cols-3" onsubmit={submit}>
      <input
        class="lcars-input"
        placeholder="Mission name"
        bind:value={mission_name}
        required
      />
      <input
        class="lcars-input"
        placeholder="Commander"
        bind:value={commander}
        required
      />
      <input
        class="lcars-input"
        placeholder="Mission type"
        bind:value={mission_type}
        required
      />
      <select class="lcars-select" bind:value={phase}>
        <option value={null}>Phase (any)</option>
        {#each PHASES as p}
          <option value={p}>{p}</option>
        {/each}
      </select>
      <input
        class="lcars-input"
        type="number"
        min="1"
        max="4"
        placeholder="Priority (1-4)"
        bind:value={priority}
      />
      <input
        class="lcars-input"
        placeholder="Launch date"
        bind:value={launch_date}
      />
      <input
        class="lcars-input sm:col-span-2"
        placeholder="Description"
        bind:value={description}
      />
      <div class="flex gap-3 sm:col-span-3">
        <button class="lcars-btn bg-lcars-orange text-black">
          {editingId === null ? "Add Mission" : "Save Changes"}
        </button>
        {#if editingId !== null}
          <button
            class="lcars-btn bg-lcars-blue text-white"
            onclick={cancelEdit}
          >
            Cancel
          </button>
        {/if}
      </div>
    </form>
  </div>

  {#if loading}
    <p class="text-lcars-teal">Loading…</p>
  {:else}
    <div
      class="lcars-curve-left overflow-hidden border-l-8 border-lcars-orange bg-lcars-panel"
    >
      {#each missions as mission (mission.id)}
        <div
          class="flex items-center justify-between border-b border-gray-800 px-6 py-4"
        >
          <div class="flex items-center gap-4">
            <div
              class="lcars-pill bg-lcars-blue px-3 py-1 text-xs font-bold text-white"
            >
              #{mission.id}
            </div>
            <span class="font-medium text-lcars-cream"
              >{mission.mission_name}</span
            >
            <span class="text-gray-500">
              — {mission.commander} ({mission.mission_type}) · P{mission.priority ??
                "—"}
            </span>
            <span
              class="lcars-pill px-2 py-0.5 text-xs {phaseClass(mission.phase)}"
            >
              {mission.phase ?? "—"}
            </span>
            {#if mission.seeded}
              <span
                class="lcars-pill bg-lcars-yellow px-2 py-0.5 text-xs text-black"
                >ORIGINAL</span
              >
            {/if}
          </div>
          <div class="flex gap-3 text-sm">
            <button
              class="text-lcars-teal hover:underline"
              onclick={() => startEdit(mission)}
            >
              Edit
            </button>
            <button
              class="text-lcars-red hover:underline"
              onclick={() => remove(mission.id)}
            >
              Delete
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</section>
