<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let projects = [];
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			projects = await api.listProjects({ published_only: true, active_only: true });
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Crowdfunding - Projetos</title>
</svelte:head>

<div class="container">
	<h1>Projetos de Financiamento Coletivo</h1>

	{#if loading}
		<p>Carregando projetos...</p>
	{:else if error}
		<p class="error">Erro: {error}</p>
	{:else if projects.length === 0}
		<p>Nenhum projeto encontrado.</p>
	{:else}
		<div class="projects-grid">
			{#each projects as project}
				<a href="/project/{project.slug}" class="project-card">
					{#if project.main_image}
						<img src={project.main_image} alt={project.title} />
					{/if}
					<div class="project-info">
						<h2>{project.title}</h2>
						<p class="short-description">{project.short_description || ''}</p>
						<div class="progress">
							<div class="progress-bar">
								<div
									class="progress-fill"
									style="width: {Math.min((project.current_amount / project.goal_amount) * 100, 100)}%"
								></div>
							</div>
							<div class="progress-text">
								R$ {project.current_amount.toFixed(2)} de R$ {project.goal_amount.toFixed(2)}
							</div>
						</div>
						<div class="stats">
							<span>{project.backers_count} apoiadores</span>
						</div>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	h1 {
		margin-bottom: 2rem;
	}

	.projects-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 2rem;
	}

	.project-card {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		overflow: hidden;
		text-decoration: none;
		color: inherit;
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.project-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.project-card img {
		width: 100%;
		height: 200px;
		object-fit: cover;
	}

	.project-info {
		padding: 1.5rem;
	}

	.project-info h2 {
		margin: 0 0 0.5rem 0;
		font-size: 1.25rem;
	}

	.short-description {
		color: #666;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.progress {
		margin: 1rem 0;
	}

	.progress-bar {
		height: 8px;
		background: #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.progress-fill {
		height: 100%;
		background: #00c853;
		transition: width 0.3s;
	}

	.progress-text {
		font-size: 0.9rem;
		color: #666;
	}

	.stats {
		margin-top: 1rem;
		font-size: 0.9rem;
		color: #666;
	}

	.error {
		color: #d32f2f;
	}
</style>
