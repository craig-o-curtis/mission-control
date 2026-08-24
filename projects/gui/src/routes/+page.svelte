<script lang="ts">
	const cards = [
		{
			href: '/books',
			title: 'Mission Control',
			desc: 'Browse, add, edit and reset the seeded mission collection (in-memory).'
		},
		{
			href: '/tasks',
			title: 'Checklist Ops',
			desc: 'Log in (JWT) and manage mission checklists, backed by Postgres on Render.'
		}
	];
</script>

<section class="mx-auto max-w-3xl p-8">
	<h1 class="text-3xl font-bold">Mission Control</h1>
	<p class="mt-2 text-gray-600">A demo GUI for two FastAPI backends.</p>

	<div class="mt-8 grid gap-6 sm:grid-cols-2">
		{#each cards as card}
			<a
				href={card.href}
				class="block rounded-xl border p-6 shadow-sm transition hover:shadow-md"
			>
				<h2 class="text-xl font-semibold">{card.title}</h2>
				<p class="mt-2 text-gray-600">{card.desc}</p>
			</a>
		{/each}
	</div>
</section>
