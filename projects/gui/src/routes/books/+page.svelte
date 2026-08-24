<script lang="ts">
	import { onMount } from 'svelte';
	import { booksApi, type Book, type BookInput } from '$lib/api';

	let books = $state<Book[]>([]);
	let error = $state<string | null>(null);
	let loading = $state(true);

	let editingId = $state<number | null>(null);
	let mission_name = $state('');
	let commander = $state('');
	let mission_type = $state('');
	let description = $state('');
	let phase = $state<string | null>(null);
	let priority = $state<number | null>(null);
	let launch_date = $state('');

	const PHASES = ['planning', 'launch', 'active', 'complete', 'archived'];

	function phaseClass(p: string | null): string {
		switch (p) {
			case 'planning':
				return 'bg-gray-600 text-white';
			case 'launch':
				return 'bg-yellow-500 text-black';
			case 'active':
				return 'bg-cyan-500 text-black';
			case 'complete':
				return 'bg-green-500 text-black';
			case 'archived':
				return 'bg-gray-400 text-gray-800';
			default:
				return 'bg-gray-700 text-gray-200';
		}
	}

	async function load() {
		loading = true;
		error = null;
		try {
			books = await booksApi.list();
		} catch (e) {
			error = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	function startEdit(book: Book) {
		editingId = book.id;
		mission_name = book.mission_name;
		commander = book.commander;
		mission_type = book.mission_type;
		description = book.description ?? '';
		phase = book.phase;
		priority = book.priority;
		launch_date = book.launch_date ?? '';
	}

	function cancelEdit() {
		editingId = null;
		mission_name = '';
		commander = '';
		mission_type = '';
		description = '';
		phase = null;
		priority = null;
		launch_date = '';
	}

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		const input: BookInput = {
			mission_name,
			commander,
			mission_type,
			description: description || null,
			phase,
			priority,
			launch_date: launch_date || null
		};
		try {
			if (editingId === null) {
				await booksApi.create(input);
			} else {
				await booksApi.update(editingId, input);
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
			await booksApi.remove(id);
			books = books.filter((b) => b.id !== id);
		} catch (e) {
			error = (e as Error).message;
		}
	}

	async function reset() {
		error = null;
		try {
			await booksApi.reset();
			await load();
		} catch (e) {
			error = (e as Error).message;
		}
	}

	onMount(load);
</script>

<section class="mx-auto max-w-3xl p-8">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">Mission Control</h1>
		<button
			class="rounded bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-700"
			onclick={reset}
		>
			Reset demo data
		</button>
	</div>

	{#if error}
		<p class="mt-4 rounded bg-red-100 p-3 text-red-700">{error}</p>
	{/if}

	<form class="mt-6 grid gap-3 rounded border p-4 sm:grid-cols-2" onsubmit={submit}>
		<input class="border p-2" placeholder="Mission name" bind:value={mission_name} required />
		<input class="border p-2" placeholder="Commander" bind:value={commander} required />
		<input class="border p-2" placeholder="Mission type" bind:value={mission_type} required />
		<select class="border p-2" bind:value={phase}>
			<option value={null}>Phase (any)</option>
			{#each PHASES as p}
				<option value={p}>{p}</option>
			{/each}
		</select>
		<input
			class="border p-2"
			type="number"
			min="1"
			max="4"
			placeholder="Priority (1-4)"
			bind:value={priority}
		/>
		<input class="border p-2" placeholder="Launch date" bind:value={launch_date} />
		<input
			class="border p-2 sm:col-span-2"
			placeholder="Description"
			bind:value={description}
		/>
		<div class="sm:col-span-2">
			<button class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500">
				{editingId === null ? 'Add mission' : 'Save changes'}
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
			{#each books as book (book.id)}
				<li class="flex items-center justify-between py-3">
					<div>
						<span class="font-medium">{book.mission_name}</span>
						<span class="text-gray-500">
							— {book.commander} ({book.mission_type}) · P{book.priority ?? '—'}
						</span>
						<span class="ml-1 rounded px-1.5 py-0.5 text-xs {phaseClass(book.phase)}">
							{book.phase ?? '—'}
						</span>
						{#if book.seeded}
							<span class="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700"
								>ORIGINAL</span
							>
						{/if}
					</div>
					<div class="flex gap-3 text-sm">
						<button class="text-blue-600 hover:underline" onclick={() => startEdit(book)}>
							Edit
						</button>
						<button class="text-red-600 hover:underline" onclick={() => remove(book.id)}>
							Delete
						</button>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</section>
