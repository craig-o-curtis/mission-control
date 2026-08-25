<script lang="ts">
	import { onMount } from 'svelte';
	import { checklistsApi, type ChecklistItem, type ChecklistItemInput } from '#lib/api';

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

<section class="mx-auto max-w-5xl">
	<div class="mb-6 flex items-end gap-4">
		<div class="lcars-curve-left bg-lcars-blue px-6 py-3">
			<h1 class="text-xl font-bold tracking-widest text-white">CHECKLIST OPS</h1>
		</div>
		<div class="lcars-curve-right bg-lcars-teal px-4 py-2">
			<span class="text-sm tracking-wider text-black">OPERATIONS</span>
		</div>
		{#if token}
			<div class="ml-auto flex gap-3">
				<button class="lcars-btn bg-lcars-red text-white" onclick={reset}>Reset Data</button>
				<button class="lcars-btn bg-lcars-purple text-white" onclick={logout}>Log Out</button>
			</div>
		{/if}
	</div>

	<div class="mb-6 h-1 w-full rounded-full bg-lcars-panel">
		<div class="h-1 w-2/3 rounded-full bg-lcars-blue"></div>
	</div>

	{#if error}
		<div class="lcars-curve-left mb-6 border-l-8 border-lcars-red bg-lcars-panel p-4">
			<p class="text-lcars-red">{error}</p>
		</div>
	{/if}

	{#if !token}
		<div class="lcars-card border-lcars-blue bg-lcars-panel">
			<form class="grid gap-3 sm:grid-cols-2" onsubmit={login}>
				<input class="lcars-input" placeholder="Username" bind:value={username} required />
				<input
					class="lcars-input"
					type="password"
					placeholder="Password"
					bind:value={password}
					required
				/>
				<div class="sm:col-span-2">
					<button class="lcars-btn bg-lcars-blue text-white">Log In</button>
				</div>
			</form>
			<p class="mt-4 text-sm text-gray-500">
				Demo admin credentials are configured on the backend via the
				<code class="text-lcars-yellow">ADMIN_USER</code> / <code class="text-lcars-yellow">ADMIN_PASSWORD</code>
				environment variables.
			</p>
		</div>
	{:else}
		<div class="lcars-card mb-8 border-lcars-teal bg-lcars-panel">
			<form class="grid gap-3 sm:grid-cols-3" onsubmit={submit}>
				<input
					class="lcars-input"
					placeholder="Checklist item"
					bind:value={checklist_item}
					required
				/>
				<select class="lcars-select" bind:value={criticality}>
					<option value={null}>Criticality (any)</option>
					{#each CRITICALITIES as c}
						<option value={c.value}>{c.value} - {c.label}</option>
					{/each}
				</select>
				<input
					class="lcars-input sm:col-span-2"
					placeholder="Description"
					bind:value={description}
				/>
				<input
					class="lcars-input"
					type="number"
					placeholder="Mission ID"
					bind:value={mission_id}
				/>
				<input class="lcars-input" placeholder="Notes" bind:value={notes} />
				<label class="flex items-center gap-2 text-sm text-lcars-cream">
					<input type="checkbox" bind:checked={executed} /> Executed
				</label>
				<div class="flex gap-3 sm:col-span-3">
					<button class="lcars-btn bg-lcars-blue text-white">
						{editingId === null ? 'Add Item' : 'Save Changes'}
					</button>
					{#if editingId !== null}
						<button class="lcars-btn bg-lcars-purple text-white" onclick={cancelEdit}>
							Cancel
						</button>
					{/if}
				</div>
			</form>
		</div>

		{#if loading}
			<p class="text-lcars-teal">Loading…</p>
		{:else}
			<div class="lcars-curve-left overflow-hidden border-l-8 border-lcars-blue bg-lcars-panel">
				{#each checklistItems as item (item.id)}
					<div class="flex items-center justify-between border-b border-gray-800 px-6 py-4">
						<div class="flex items-center gap-4">
							<div class="lcars-pill bg-lcars-orange px-3 py-1 text-xs font-bold text-black">
								#{item.id}
							</div>
							<span class={item.executed ? 'text-gray-500 line-through' : 'font-medium text-lcars-cream'}>
								{item.checklist_item}
							</span>
							<span class="text-gray-500">
								— {criticalityLabel(item.criticality)} · M{item.mission_id ?? '—'}
							</span>
							{#if item.notes}
								<span class="text-gray-500"> ({item.notes})</span>
							{/if}
							{#if item.seeded}
								<span class="lcars-pill bg-lcars-yellow px-2 py-0.5 text-xs text-black"
									>ORIGINAL</span
								>
							{/if}
						</div>
						<div class="flex gap-3 text-sm">
							<button class="text-lcars-teal hover:underline" onclick={() => startEdit(item)}>
								Edit
							</button>
							<button class="text-lcars-red hover:underline" onclick={() => remove(item.id)}>
								Delete
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</section>
