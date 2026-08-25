<script lang="ts">
	import { onMount } from 'svelte';
	import { checklistsApi, type ChecklistItem, type ChecklistItemInput } from '#lib/api.js';

	let token = $state<string | null>(null);
	let checklistItems = $state<ChecklistItem[]>([]);
	let error = $state<string | null>(null);
	let loading = $state(false);

	let username = $state('');
	let password = $state('');

	let editingId = $state<number | null>(null);
	let checklist_item = $state('');
	let description = $state('');
	let criticality = $state<number | null>(null);
	let executed = $state(false);
	let mission_id = $state<number | null>(null);
	let notes = $state('');

	const TOKEN_KEY = 'checklists_api_token';

	const CRITICALITIES = [
		{ value: 1, label: 'Critical' },
		{ value: 2, label: 'High' },
		{ value: 3, label: 'Medium' },
		{ value: 4, label: 'Low' }
	];

	function criticalityLabel(c: number | null): string {
		return CRITICALITIES.find((x) => x.value === c)?.label ?? '—';
	}

	async function load() {
		if (!token) return;
		loading = true;
		error = null;
		try {
			checklistItems = await checklistsApi.list(token);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	async function login(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		try {
			token = await checklistsApi.login(username, password);
			localStorage.setItem(TOKEN_KEY, token);
			username = '';
			password = '';
			await load();
		} catch (e) {
			error = (e as Error).message;
		}
	}

	function logout() {
		token = null;
		checklistItems = [];
		localStorage.removeItem(TOKEN_KEY);
	}

	function startEdit(item: ChecklistItem) {
		editingId = item.id;
		checklist_item = item.checklist_item;
		description = item.description ?? '';
		criticality = item.criticality;
		executed = item.executed;
		mission_id = item.mission_id;
		notes = item.notes ?? '';
	}

	function cancelEdit() {
		editingId = null;
		checklist_item = '';
		description = '';
		criticality = null;
		executed = false;
		mission_id = null;
		notes = '';
	}

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		if (!token) return;
		error = null;
		const input: ChecklistItemInput = {
			checklist_item,
			description: description || null,
			criticality,
			executed,
			mission_id,
			notes: notes || null
		};
		try {
			if (editingId === null) {
				await checklistsApi.create(token, input);
			} else {
				await checklistsApi.update(token, editingId, input);
			}
			cancelEdit();
			await load();
		} catch (e) {
			error = (e as Error).message;
		}
	}

	async function remove(id: number) {
		if (!token) return;
		error = null;
		try {
			await checklistsApi.remove(token, id);
			checklistItems = checklistItems.filter((item) => item.id !== id);
		} catch (e) {
			error = (e as Error).message;
		}
	}

	async function reset() {
		if (!token) return;
		error = null;
		try {
			await checklistsApi.reset(token);
			await load();
		} catch (e) {
			error = (e as Error).message;
		}
	}

	onMount(() => {
		const saved = localStorage.getItem(TOKEN_KEY);
		if (saved) {
			token = saved;
			load();
		}
	});
</script>

<section class="mx-auto max-w-3xl p-8">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">Checklist Ops</h1>
		{#if token}
			<div class="flex items-center gap-3">
				<button class="text-sm text-gray-600 hover:underline" onclick={reset}>Reset demo data</button>
				<button class="text-sm text-red-600 hover:underline" onclick={logout}>Log out</button>
			</div>
		{/if}
	</div>

	{#if error}
		<p class="mt-4 rounded bg-red-100 p-3 text-red-700">{error}</p>
	{/if}

	{#if !token}
		<form class="mt-6 grid gap-3 rounded border p-4 sm:grid-cols-2" onsubmit={login}>
			<input class="border p-2" placeholder="Username" bind:value={username} required />
			<input
				class="border p-2"
				type="password"
				placeholder="Password"
				bind:value={password}
				required
			/>
			<div class="sm:col-span-2">
				<button class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500">Log in</button>
			</div>
		</form>
		<p class="mt-3 text-sm text-gray-500">
			Demo admin credentials are configured on the backend via the
			<code>ADMIN_USER</code> / <code>ADMIN_PASSWORD</code> environment variables (set on Render).
		</p>
	{:else}
		<form class="mt-6 grid gap-3 rounded border p-4 sm:grid-cols-2" onsubmit={submit}>
			<input
				class="border p-2"
				placeholder="Checklist item"
				bind:value={checklist_item}
				required
			/>
			<select class="border p-2" bind:value={criticality}>
				<option value={null}>Criticality (any)</option>
				{#each CRITICALITIES as c}
					<option value={c.value}>{c.value} - {c.label}</option>
				{/each}
			</select>
			<input
				class="border p-2 sm:col-span-2"
				placeholder="Description"
				bind:value={description}
			/>
			<input
				class="border p-2"
				type="number"
				placeholder="Mission ID"
				bind:value={mission_id}
			/>
			<input class="border p-2" placeholder="Notes" bind:value={notes} />
			<label class="flex items-center gap-2 text-sm sm:grid-cols-2">
				<input type="checkbox" bind:checked={executed} /> Executed
			</label>
			<div class="sm:col-span-2">
				<button class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500">
					{editingId === null ? 'Add item' : 'Save changes'}
				</button>
				{#if editingId !== null}
					<button class="ml-2 px-4 py-2 text-gray-600 hover:underline" onclick={cancelEdit}>
						Cancel
					</button>
				{/if}
			</div>
		</form>

		{#if loading}
			<p class="mt-6 text-gray-500">Loading…</p>
		{:else}
			<ul class="mt-6 divide-y">
				{#each checklistItems as item (item.id)}
					<li class="flex items-center justify-between py-3">
						<div>
							<span class={item.executed ? 'text-gray-400 line-through' : 'font-medium'}>
								{item.checklist_item}
							</span>
							<span class="text-gray-500">
								— {criticalityLabel(item.criticality)} · M{item.mission_id ?? '—'}
							</span>
							{#if item.notes}
								<span class="text-gray-400"> ({item.notes})</span>
							{/if}
							{#if item.seeded}
								<span class="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700"
									>ORIGINAL</span
								>
							{/if}
						</div>
						<div class="flex gap-3 text-sm">
							<button class="text-blue-600 hover:underline" onclick={() => startEdit(item)}>
								Edit
							</button>
							<button class="text-red-600 hover:underline" onclick={() => remove(item.id)}>
								Delete
							</button>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</section>
