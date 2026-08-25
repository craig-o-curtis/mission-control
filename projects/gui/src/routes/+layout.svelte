<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="min-h-screen bg-black">
	<header class="flex items-center gap-3 border-b-4 border-lcars-orange bg-lcars-bg px-6 py-4">
		<div class="lcars-curve-left bg-lcars-orange px-8 py-3">
			<span class="text-xl font-bold tracking-widest text-black">MISSION CONTROL</span>
		</div>
		<div class="lcars-curve-right bg-lcars-blue px-6 py-2">
			<span class="text-sm tracking-wider text-white">STARSHIP CONSOLE</span>
		</div>
		<div class="ml-auto flex gap-2">
			<div class="h-4 w-16 rounded-full bg-lcars-purple"></div>
			<div class="h-4 w-10 rounded-full bg-lcars-yellow"></div>
			<div class="h-4 w-12 rounded-full bg-lcars-teal"></div>
		</div>
	</header>
	<main class="p-6">
		{@render children()}
	</main>
</div>
