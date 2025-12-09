<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';

	let leaderboard = [];
	let project = null;
	let loading = true;
	let error = null;

	$: projectId = parseInt($page.params.projectId);

	onMount(async () => {
		try {
			project = await api.getProject(projectId);
			leaderboard = await api.getLeaderboard(projectId);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Leaderboard - {project?.title || 'Projeto'}</title>
</svelte:head>

<div class="container">
	<h1>Leaderboard - {project?.title || 'Projeto'}</h1>

	{#if loading}
		<p>Carregando leaderboard...</p>
	{:else if error}
		<p class="error">Erro: {error}</p>
	{:else if leaderboard.length === 0}
		<p>Nenhum contribuidor ainda.</p>
	{:else}
		<div class="leaderboard">
			<div class="leaderboard-header">
				<div class="rank">Rank</div>
				<div class="user">Usuário</div>
				<div class="amount">Total Contribuído</div>
				<div class="contributions">Contribuições</div>
			</div>
			{#each leaderboard as entry, index}
				<div class="leaderboard-row" class:top-three={index < 3}>
					<div class="rank">
						{#if index === 0}
							🥇
						{:else if index === 1}
							🥈
						{:else if index === 2}
							🥉
						{:else}
							#{index + 1}
						{/if}
					</div>
					<div class="user">{entry.user_name}</div>
					<div class="amount">R$ {entry.total_contributed.toFixed(2)}</div>
					<div class="contributions">{entry.contributions_count}</div>
				</div>
			{/each}
		</div>
	{/if}

	<a href="/project/{project?.slug}" class="back-link">← Voltar ao projeto</a>
</div>

<style>
	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
	}

	h1 {
		margin-bottom: 2rem;
	}

	.leaderboard {
		background: white;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.leaderboard-header {
		display: grid;
		grid-template-columns: 80px 1fr 200px 150px;
		background: #f5f5f5;
		padding: 1rem;
		font-weight: bold;
		border-bottom: 2px solid #e0e0e0;
	}

	.leaderboard-row {
		display: grid;
		grid-template-columns: 80px 1fr 200px 150px;
		padding: 1rem;
		border-bottom: 1px solid #e0e0e0;
		transition: background 0.2s;
	}

	.leaderboard-row:hover {
		background: #f9f9f9;
	}

	.leaderboard-row.top-three {
		background: #fff9e6;
	}

	.rank {
		font-weight: bold;
		font-size: 1.2rem;
	}

	.amount {
		font-weight: bold;
		color: #00c853;
	}

	.back-link {
		display: inline-block;
		margin-top: 2rem;
		color: #00c853;
		text-decoration: none;
	}

	.back-link:hover {
		text-decoration: underline;
	}

	.error {
		color: #d32f2f;
	}
</style>
